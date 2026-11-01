"""Desktop controller: elevate only the network worker, never the account UI."""
import ctypes
import hmac
import math
import re
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time

from gui_transport import Channel
from gui_diagnostics import PHASES, code_id

from paths import APP_DIR, ROOT


class WindowsProcess:
    """Retain the elevated handle so Stop waits for cleanup on Windows too."""
    def __init__(self, handle):
        from ctypes import wintypes as w
        self.handle = handle
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
        self.kernel.GetExitCodeProcess.restype = w.BOOL
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.CloseHandle.restype = w.BOOL
        self.code = None

    def poll(self):
        from ctypes import wintypes as w
        if self.code is not None:
            return self.code
        code = w.DWORD()
        if not self.kernel.GetExitCodeProcess(self.handle, ctypes.byref(code)):
            raise RuntimeError('Could not check the network worker state.')
        if code.value == 259:  # STILL_ACTIVE
            return None
        self.code = code.value
        self.kernel.CloseHandle(self.handle)
        return self.code

    def wait(self, timeout):
        deadline = time.monotonic() + timeout
        while self.poll() is None:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired('network worker', timeout)
            time.sleep(.1)
        return self.code


def elevated_command(port, token):
    command = [sys.executable, '-u', str(APP_DIR / 'gui_worker.py'), '--port', str(port), '--token', token]
    if sys.platform == 'linux' and os.geteuid() != 0:
        if not shutil.which('pkexec'):
            raise RuntimeError('Install polkit (pkexec) to authorize network setup from the desktop.')
        return ['pkexec', *command]
    return command


class BridgeController:
    def __init__(self, emit):
        self.emit = emit
        self.lock = threading.Lock()
        self.channel = None
        self.cancelled = threading.Event()
        self.thread = None
        self.process = None
        self.finished = threading.Event()
        self.finished.set()
        self.diagnostic_lock = threading.Lock()
        self.diagnostics = {}
        self.gui_code = code_id()
        self.stop_watch = None
        self.stop_delivery_lock = threading.Lock()
        self.stop_delivered = False

    @property
    def active(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, config):
        if self.active:
            raise RuntimeError('Stop the current bridge before starting another one.')
        self.cancelled.clear()
        self.stop_delivered = False
        self.finished.clear()
        with self.diagnostic_lock:
            self.diagnostics = {'phase': 'starting', 'stop_delivery': 'not requested', 'stop_ack': False}
        self.thread = threading.Thread(target=self._serve, args=(dict(config),), daemon=True)
        self.thread.start()

    def _launch(self, port, token):
        command = elevated_command(port, token)
        if sys.platform == 'win32' and not ctypes.windll.shell32.IsUserAnAdmin():
            from ctypes import wintypes as w
            class ExecuteInfo(ctypes.Structure):
                _fields_ = [('cbSize', w.DWORD), ('fMask', w.ULONG), ('hwnd', w.HWND),
                            ('lpVerb', w.LPCWSTR), ('lpFile', w.LPCWSTR), ('lpParameters', w.LPCWSTR),
                            ('lpDirectory', w.LPCWSTR), ('nShow', ctypes.c_int), ('hInstApp', w.HINSTANCE),
                            ('lpIDList', ctypes.c_void_p), ('lpClass', w.LPCWSTR), ('hkeyClass', w.HANDLE),
                            ('dwHotKey', w.DWORD), ('hIcon', w.HANDLE), ('hProcess', w.HANDLE)]
            shell = ctypes.WinDLL('shell32', use_last_error=True)
            shell.ShellExecuteExW.argtypes = [ctypes.POINTER(ExecuteInfo)]
            shell.ShellExecuteExW.restype = w.BOOL
            info = ExecuteInfo(cbSize=ctypes.sizeof(ExecuteInfo), fMask=0x40, lpVerb='runas',
                               lpFile=command[0], lpParameters=subprocess.list2cmdline(command[1:]),
                               lpDirectory=str(ROOT), nShow=0)
            if not shell.ShellExecuteExW(ctypes.byref(info)) or not info.hProcess:
                raise RuntimeError('Administrator approval was cancelled or the network worker could not start.')
            self.process = WindowsProcess(info.hProcess)
        else:
            env = {k: v for k, v in os.environ.items() if not k.startswith('OBWEB_')}
            self.process = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _serve(self, config):
        listener = socket.socket()
        channel = None
        try:
            listener.bind(('127.0.0.1', 0))
            listener.listen(4)
            listener.settimeout(.3)
            token = secrets.token_hex(32)
            self.emit({'type': 'status', 'message': 'Waiting for administrator approval…'})
            if self.cancelled.is_set():
                return
            self._launch(listener.getsockname()[1], token)
            deadline = time.monotonic() + 120  # Startup authorization only, never a session limit.
            while not self.cancelled.is_set():
                if self.process and self.process.poll() is not None:
                    raise RuntimeError('Network worker exited before startup. Check the administrator authorization and Python dependencies.')
                if time.monotonic() >= deadline:
                    raise RuntimeError('Administrator approval timed out. Start again when ready.')
                try:
                    connection, _ = listener.accept()
                except socket.timeout:
                    continue
                connection.settimeout(2)
                candidate = Channel(connection)
                try:
                    hello = candidate.receive()
                    if hello.get('type') != 'hello' or not hmac.compare_digest(str(hello.get('token', '')), token):
                        candidate.close()
                        continue
                except (OSError, EOFError, ValueError):
                    candidate.close()
                    continue
                self._progress({'phase': 'starting', 'pid': hello.get('pid'), 'code': hello.get('code'), 'loop_age': None})
                connection.settimeout(None)
                channel = candidate
                channel.send({'type': 'start', **config})
                with self.lock:
                    self.channel = channel
                if self.cancelled.is_set():
                    self._deliver_stop(channel)
                break
            if channel is not None:
                while True:
                    message = channel.receive()
                    if message['type'] == 'progress':
                        self._progress(message)
                    elif message['type'] == 'stop_ack':
                        with self.diagnostic_lock:
                            self.diagnostics['stop_ack'] = True
                        self.emit({'type': 'log', 'line': 'Network worker acknowledged Stop; network cleanup is now requested.'})
                    self.emit(message)
                    if message['type'] in ('error', 'stopped'):
                        break
        except (OSError, EOFError):
            if not self.cancelled.is_set():
                self.emit({'type': 'error', 'message': 'The local network worker disconnected. Check the adapter and start again.'})
        except Exception as error:
            detail = str(error) if isinstance(error, RuntimeError) else f'Local controller failed ({type(error).__name__}).'
            self.emit({'type': 'error', 'message': detail})
        finally:
            listener.close()
            with self.lock:
                self.channel = None
            if channel:
                channel.close()
            if self.process:
                waiting = False
                while True:
                    try:
                        self.process.wait(timeout=10)
                        break
                    except subprocess.TimeoutExpired:
                        # Keep Start disabled; never claim cleanup finished or
                        # force-kill a privileged worker while it is cleaning up.
                        if not waiting:
                            self.emit({'type': 'log', 'line': 'Network cleanup is still in progress.'})
                            waiting = True
                self.process = None
            self.finished.set()
            self.emit({'type': 'finished'})

    def _progress(self, message):
        with self.diagnostic_lock:
            self.diagnostics['heartbeat'] = time.monotonic()
            phase = message.get('phase')
            if phase in PHASES:
                self.diagnostics['phase'] = phase
            pid = message.get('pid')
            if isinstance(pid, int) and 0 < pid < 2**32:
                self.diagnostics['pid'] = pid
            code = message.get('code', '')
            if isinstance(code, str) and re.fullmatch(r'[0-9a-f]{12}', code):
                self.diagnostics['worker_code'] = code
            age = message.get('loop_age')
            self.diagnostics['loop_age'] = round(age, 1) if isinstance(age, (int, float)) and math.isfinite(age) and age >= 0 else None
            # Fixed application function locations only; never allow report data
            # to become a general-purpose payload/credential transport.
            stacks = message.get('threads', [])
            if isinstance(stacks, list):
                self.diagnostics['threads'] = [value[:700] for value in stacks[:24] if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_ .:<>-]+', value)]

    def diagnostic_lines(self):
        with self.diagnostic_lock:
            state = dict(self.diagnostics)
        heartbeat = state.get('heartbeat')
        return [f'GUI code: {self.gui_code}',
                f'Network worker PID: {state.get("pid", "not reported")}',
                f'Worker code: {state.get("worker_code", "not reported")}',
                f'Stop delivery: {state.get("stop_delivery", "not requested")}',
                f'Stop acknowledged: {state.get("stop_ack", False)}',
                f'Worker phase: {PHASES.get(state.get("phase"), "not reported")}',
                'Last worker heartbeat: ' + (f'{time.monotonic() - heartbeat:.1f}s ago' if heartbeat is not None else 'not received'),
                'Network loop heartbeat: ' + (f'{state["loop_age"]}s ago' if state.get('loop_age') is not None else 'not observed'),
                *state.get('threads', [])]

    def _watch_stop(self):
        elapsed = 0
        while not self.finished.wait(5):
            elapsed += 5
            if elapsed != 5 and elapsed % 15:
                continue
            with self.diagnostic_lock:
                state = dict(self.diagnostics)
            ack = state.get('stop_ack', False)
            if not ack:
                message = f'Still waiting {elapsed}s: the network worker has NOT acknowledged Stop.'
            else:
                message = f'Still waiting {elapsed}s: {PHASES.get(state.get("phase"), "network cleanup")}.'
            heartbeat = state.get('heartbeat')
            if heartbeat is None or time.monotonic() - heartbeat > 5:
                message += ' The worker progress monitor is not responding.'
            elif state.get('phase') in ('starting_network', 'running', 'stop_received', 'cancelling_io', 'closing_session') and state.get('loop_age') is not None and state['loop_age'] > 5:
                message += ' The worker monitor responds, but the network event loop is not advancing.'
            self.emit({'type': 'log', 'line': message})
            for location in state.get('threads', []):
                self.emit({'type': 'log', 'line': 'Worker location: ' + location})

    def _deliver_stop(self, channel):
        # Serialize the GUI's Stop against a Stop queued during authorization.
        # A complete start configuration always precedes Stop on the wire.
        with self.stop_delivery_lock:
            if self.stop_delivered:
                return True
            sent = False
            if channel is not None:
                try:
                    channel.send({'type': 'stop'})
                    self.stop_delivered = sent = True
                    # EOF is a second signal; preserve incoming cleanup reports.
                    channel.finish_sending()
                except OSError:
                    pass
            with self.diagnostic_lock:
                self.diagnostics['stop_delivery'] = 'sent' if sent else 'not sent; channel unavailable'
        self.emit({'type': 'log', 'line': 'Stop command sent to the network worker.' if sent else 'Stop is pending: control channel unavailable; waiting for worker exit or connection.'})
        return sent

    def stop(self):
        if self.cancelled.is_set():
            return
        self.cancelled.set()
        with self.lock:
            channel = self.channel
        self._deliver_stop(channel)
        if not self.finished.is_set():
            self.stop_watch = threading.Thread(target=self._watch_stop, name='stop-diagnostics', daemon=True)
            self.stop_watch.start()

    def send(self, message):
        with self.lock:
            channel = self.channel
        if channel:
            try:
                channel.send(message)
                return True
            except OSError:
                pass
        return False
