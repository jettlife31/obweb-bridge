"""Desktop controller: elevate only the network worker, never the account UI."""
import ctypes
import hmac
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

ROOT = Path(__file__).resolve().parent


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
    command = [sys.executable, '-u', str(ROOT / 'gui_worker.py'), '--port', str(port), '--token', token]
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

    @property
    def active(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, config):
        if self.active:
            raise RuntimeError('Stop the current bridge before starting another one.')
        self.cancelled.clear()
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
            wsl_distro = config.pop('wsl_distro', None)
            self.emit({'type': 'status', 'message': 'Starting WSL gateway…' if wsl_distro else 'Waiting for administrator approval…'})
            if self.cancelled.is_set():
                return
            if wsl_distro:
                from wsl_support import worker_command
                if sys.platform != 'win32' or config.get('mode') != 'gateway':
                    raise RuntimeError('WSL is available only for the Windows LAN gateway.')
                command = worker_command(wsl_distro, listener.getsockname()[1], token)
                if self.cancelled.is_set():
                    return
                self.process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            else:
                self._launch(listener.getsockname()[1], token)
            deadline = time.monotonic() + 120  # Startup authorization only, never a session limit.
            while not self.cancelled.is_set():
                if self.process and self.process.poll() is not None:
                    raise RuntimeError('WSL worker exited before startup. Check the WSL distribution, mirrored networking and Linux dependencies.' if wsl_distro else 'Network worker exited before startup. Check the administrator authorization and Python dependencies.')
                if time.monotonic() >= deadline:
                    raise RuntimeError('WSL worker could not connect to the GUI over localhost. Check mirrored networking and the Hyper-V firewall.' if wsl_distro else 'Administrator approval timed out. Start again when ready.')
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
                connection.settimeout(None)
                channel = candidate
                with self.lock:
                    self.channel = channel
                channel.send({'type': 'start', **config})
                if self.cancelled.is_set():
                    channel.send({'type': 'stop'})
                break
            if channel is not None:
                while True:
                    message = channel.receive()
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
            self.emit({'type': 'finished'})

    def stop(self):
        self.cancelled.set()
        self.send({'type': 'stop'})

    def send(self, message):
        with self.lock:
            if self.channel:
                try:
                    self.channel.send(message)
                except OSError:
                    pass
