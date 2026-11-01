"""Local worker progress. No packet contents, account data or frame locals."""
import asyncio
import hashlib
import os
from pathlib import Path
import sys
import threading
import time

from paths import APP_DIR

PHASES = {
    'starting': 'Starting the network worker',
    'opening_adapter': 'Opening the Ethernet adapter',
    'starting_network': 'Starting the network session',
    'running': 'Network session running',
    'stop_received': 'Stop received; cancelling network tasks',
    'cancelling_io': 'Cancelling Ethernet driver I/O',
    'closing_session': 'Closing the network session',
    'releasing_adapter': 'Releasing the Ethernet adapter',
    'driver_ack': 'Waiting for the TAP driver to acknowledge cancellation',
    'removing_adapter': 'Removing the temporary TAP adapter',
    'complete': 'Network cleanup complete',
}


def code_id():
    digest = hashlib.sha256()
    for name in ('gui.py', 'gui_backend.py', 'gui_worker.py', 'gui_transport.py',
                 'gui_diagnostics.py', 'ethernet.py', 'ethernet_adapter.py', 'windows_stop.py'):
        try:
            digest.update(name.encode('ascii'))
            digest.update((APP_DIR / name).read_bytes())
        except OSError:
            return 'unavailable'
    return digest.hexdigest()[:12]


def thread_locations():
    """Only application basenames/function names/line numbers, never locals."""
    frames = sys._current_frames()
    result = []
    for index, thread in enumerate(threading.enumerate()[:12], 1):
        frame = frames.get(thread.ident)
        locations = []
        while frame is not None:
            filename = frame.f_code.co_filename
            if filename.startswith(str(APP_DIR) + os.sep):
                locations.append(f'{Path(filename).name}:{frame.f_lineno}:{frame.f_code.co_name}')
            frame = frame.f_back
        if locations:
            result.append(f'thread {index}: ' + ' <- '.join(locations[:5]))
    return result


class WorkerProgress:
    def __init__(self, channel, stopped):
        self.channel, self.stopped = channel, stopped
        self.done = threading.Event()
        self.lock = threading.Lock()
        self.phase = 'starting'
        self.tick = None
        self.tasks = []
        self.stop_callback = None
        self.stop_at = None
        self.code = code_id()
        self.thread = None
        self.control_handler = None
        self.control_state = 'not_bound'
        self.control_last = 'none'
        self.control_count = 0
        self.stop_signal = None
        self.stop_signal_state = 'not_used'
        self.stop_reason = 'none'

    def attach_stop_signal(self, signal):
        self.stop_signal = signal
        self.stop_signal_state = 'available'

    def bind_control(self, handler):
        with self.lock:
            self.control_handler = handler
            self.control_state = 'polling'

    def _poll_control(self):
        with self.lock:
            handler = self.control_handler
            active = self.control_state == 'polling'
        if handler is None or not active:
            return
        try:
            # Bound work per tick so command bursts cannot starve heartbeats.
            for _ in range(16):
                message = self.channel.poll_message()
                if message is None:
                    return
                kind = message.get('type')
                with self.lock:
                    self.control_last = kind if kind in ('stop', 'input') else 'unknown'
                    self.control_count += 1
                handler(message)
                if kind == 'stop':
                    with self.lock:
                        self.control_state = 'stop_received'
                    return
        except EOFError:
            with self.lock:
                self.control_state = 'eof'
            self.request_stop('control_channel_closed')
        except (OSError, ValueError, RecursionError):
            with self.lock:
                self.control_state = 'read_failed'
            self.request_stop('control_read_failed')

    def set_phase(self, phase):
        if phase not in PHASES:
            return
        with self.lock:
            self.phase = phase

    def observe_line(self, line):
        pairs = (('READY:', 'running'),
                 ('Cancelling local Ethernet I/O', 'cancelling_io'),
                 ('Ethernet network threads stopped', 'releasing_adapter'),
                 ('Waiting for the Windows TAP driver', 'driver_ack'),
                 ('Removing the temporary Windows TAP', 'removing_adapter'),
                 ('Ethernet adapter cleanup complete', 'complete'))
        for marker, phase in pairs:
            if marker in line:
                if phase == 'running' and self.stopped.is_set():
                    return
                self.set_phase(phase)
                break

    def register_stop(self, callback):
        with self.lock:
            self.stop_callback = callback
        if self.stopped.is_set():
            callback()

    def request_stop(self, reason):
        self.stopped.set()
        with self.lock:
            first = self.stop_at is None
            if first:
                self.stop_at = time.monotonic()
                self.phase = 'stop_received'
                self.stop_reason = reason
            callback = self.stop_callback
        if first:
            try:
                self.channel.send({'type': 'stop_ack', 'reason': reason})
                self.channel.send(self.snapshot())
            except OSError:
                pass
        if callback is not None and first:
            self.set_phase('cancelling_io')
            callback()

    def pulse(self):
        locations = []
        for index, task in enumerate(list(asyncio.all_tasks())[:20], 1):
            for frame in task.get_stack(limit=1):
                filename = frame.f_code.co_filename
                if filename.startswith(str(APP_DIR) + os.sep):
                    locations.append(f'task {index}: {Path(filename).name}:{frame.f_lineno}:{frame.f_code.co_name}')
        with self.lock:
            self.tick = time.monotonic()
            self.tasks = locations

    def snapshot(self):
        now = time.monotonic()
        with self.lock:
            message = {'type': 'progress', 'phase': self.phase,
                       'loop_age': None if self.tick is None else round(now - self.tick, 1),
                       'pid': os.getpid(), 'code': self.code,
                       'control_state': self.control_state, 'control_last': self.control_last,
                       'control_count': self.control_count,
                       'control_buffer_bytes': len(getattr(self.channel, 'buffer', ())),
                       'windows_stop_signal': self.stop_signal_state, 'stop_reason': self.stop_reason}
            tasks = list(self.tasks)
        # Include safe locations even before Stop is recognized. Otherwise a
        # stuck command receiver (the reported failure) has no stack evidence.
        message['threads'] = [*thread_locations(), *tasks][:24]
        return message

    def start(self):
        def monitor():
            next_report = 0
            while not self.done.wait(.1):
                try:
                    if self.stop_signal is not None and not self.stopped.is_set():
                        try:
                            if self.stop_signal.is_set():
                                self.stop_signal_state = 'received'
                                self.request_stop('windows_event')
                        except OSError:
                            self.stop_signal_state = 'check_failed'
                            self.stop_signal.close()
                            self.stop_signal = None
                    self._poll_control()
                    if time.monotonic() < next_report:
                        continue
                    self.channel.send(self.snapshot())
                    next_report = time.monotonic() + 1
                    # Cover an I/O issuance racing the first cancellation. This
                    # runs independently of the network event loop, only on Stop.
                    with self.lock:
                        callback = self.stop_callback if self.stopped.is_set() else None
                    if callback:
                        callback()
                except (OSError, ValueError):
                    return
        self.thread = threading.Thread(target=monitor, name='worker-progress', daemon=True)
        self.thread.start()

    def close(self):
        self.done.set()
        if self.thread:
            self.thread.join(timeout=2)
        if self.stop_signal is not None and (self.thread is None or not self.thread.is_alive()):
            self.stop_signal.close()
            self.stop_signal = None
