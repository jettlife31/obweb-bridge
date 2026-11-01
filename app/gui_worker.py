"""Elevated network-only worker for the shared desktop UI."""
import argparse
import asyncio
import builtins
import contextlib
import os
import queue
import re
import socket
import sys
import threading

from gui_transport import Channel
from gui_diagnostics import WorkerProgress


class Output:
    def __init__(self, channel, progress=None):
        self.channel = channel
        self.progress = progress
        self.buffer = ''
        self.lock = threading.Lock()

    def write(self, text):
        with self.lock:
            self.buffer += text
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                if line:
                    if self.progress:
                        self.progress.observe_line(line)
                    self.channel.send({'type': 'log', 'line': line[:8000]})
        return len(text)

    def flush(self):
        pass


async def until_stopped(coroutine, stopped, progress=None):
    if stopped.is_set():
        coroutine.close()
        return
    task = asyncio.create_task(coroutine)
    if progress:
        loop = asyncio.get_running_loop()
        def pulse():
            if not progress.done.is_set():
                progress.pulse()
                loop.call_later(.5, pulse)
        pulse()  # Stays alive during coroutine cancellation/executor shutdown.
    async def wait():
        while not stopped.is_set():
            await asyncio.sleep(.2)
    waiter = asyncio.create_task(wait())
    try:
        done, _ = await asyncio.wait([task, waiter], return_when=asyncio.FIRST_COMPLETED)
        if task in done:
            task.result()
    finally:
        task.cancel()
        waiter.cancel()
        await asyncio.gather(task, waiter, return_exceptions=True)


def run_worker(channel, config, progress=None):
    mode = config.get('mode')
    if mode not in ('ethernet', 'gateway'):
        raise ValueError('Invalid bridge mode')
    if set(config) - {'type', 'mode', 'adapter', 'interface', 'lan_ip'}:
        raise ValueError('Unsupported network setting')
    stopped = progress.stopped if progress else threading.Event()
    responses = queue.Queue(maxsize=1)
    def on_message(message):
        if message['type'] == 'stop':
            if progress:
                progress.request_stop('command')
            else:
                stopped.set()
                channel.send({'type': 'stop_ack', 'reason': 'command'})
        elif message['type'] == 'input' and isinstance(message.get('value'), str):
            try:
                responses.put_nowait(message['value'][:4096])
            except queue.Full:
                pass
    if progress:
        # One monitor owns both command reception and health reports. A healthy
        # heartbeat now means the command receiver itself is also being polled.
        progress.bind_control(on_message)
    else:
        def monitor():
            try:
                while not stopped.is_set():
                    on_message(channel.receive())
            except (EOFError, OSError, ValueError, RecursionError):
                stopped.set()
        threading.Thread(target=monitor, name='worker-control', daemon=True).start()
    def prompt(text):
        channel.send({'type': 'prompt', 'text': text})
        while not stopped.is_set():
            try:
                return responses.get(timeout=.2)
            except queue.Empty:
                pass
        raise KeyboardInterrupt()
    previous_input = builtins.input
    builtins.input = prompt
    try:
        if stopped.is_set():
            return
        if mode == 'ethernet':
            import ethernet
            from ethernet_adapter import LinuxTap, WindowsTap
            name = config.get('adapter') or None
            if name is not None and (not isinstance(name, str) or len(name) > 256):
                raise ValueError('Invalid adapter name')
            adapter = WindowsTap(name) if sys.platform == 'win32' else LinuxTap()
            if progress:
                progress.set_phase('opening_adapter')
                callback = getattr(adapter, 'stop_io', None)
                if callback:
                    progress.register_stop(callback)
            with adapter:
                if progress:
                    progress.set_phase('starting_network')
                asyncio.run(until_stopped(ethernet.run(adapter), stopped, progress))
                ethernet.log('Ethernet network threads stopped; cleaning up the adapter.')
            ethernet.log('Ethernet adapter cleanup complete.')
        else:
            if sys.platform == 'win32':
                from windows_lan import inventory
                import windows_gateway
                interface = config.get('interface')
                if not isinstance(interface, str) or not 1 <= len(interface) <= 256:
                    raise ValueError('Select a Windows LAN interface')
                plan = inventory(interface, config.get('lan_ip'))
                channel.send({'type': 'plan', 'plan': {k: plan[k] for k in ('lan_ip', 'client_network')}})
                asyncio.run(until_stopped(windows_gateway.run(plan), stopped, progress))
                return
            if sys.platform != 'linux':
                raise ValueError('LAN gateway mode requires Windows or Linux')
            interface = config.get('interface', '')
            if not isinstance(interface, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,15}', interface):
                raise ValueError('Select a supported LAN interface')
            from network import inventory
            import gateway
            plan = inventory(interface, lan_ip=config.get('lan_ip') or None)
            channel.send({'type': 'plan', 'plan': plan})
            asyncio.run(until_stopped(gateway.run(plan, gateway.WSS_URL, gateway.WSS_ORIGIN), stopped, progress))
    finally:
        builtins.input = previous_input


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--token', required=True)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535 or not re.fullmatch(r'[0-9a-f]{64}', args.token):
        return 2
    # The GUI owns credentials. Never inherit container configuration here.
    for name in list(os.environ):
        if name.startswith('OBWEB_'):
            os.environ.pop(name)
    try:
        connection = socket.create_connection(('127.0.0.1', args.port), timeout=10)
    except OSError:
        return 1  # GUI closed during elevation; no network setup was attempted.
    channel = Channel(connection)
    progress = WorkerProgress(channel, threading.Event())
    try:
        channel.send({'type': 'hello', 'token': args.token, 'pid': os.getpid(), 'code': progress.code})
        config = channel.receive()
        connection.settimeout(None)
        if config['type'] != 'start':
            return 1
        if sys.platform == 'win32':
            try:
                from windows_stop import StopSignal
                progress.attach_stop_signal(StopSignal(args.token, create=False))
            except OSError:
                progress.stop_signal_state = 'unavailable'
                channel.send({'type': 'log', 'line': 'Native Windows Stop event unavailable; using local control commands.'})
        progress.start()
        with contextlib.redirect_stdout(Output(channel, progress)), contextlib.redirect_stderr(Output(channel, progress)):
            run_worker(channel, config, progress)
        channel.send({'type': 'stopped'})
    except KeyboardInterrupt:
        with contextlib.suppress(OSError):
            channel.send({'type': 'stopped'})
    except (EOFError, OSError):
        pass  # Control loss triggers the monitor and existing resource cleanup.
    except Exception as error:
        message = str(error) if isinstance(error, (RuntimeError, ValueError)) else f'Network setup failed ({type(error).__name__}).'
        with contextlib.suppress(OSError):
            channel.send({'type': 'error', 'message': message})
    finally:
        progress.close()
        channel.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
