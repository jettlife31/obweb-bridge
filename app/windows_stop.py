"""Ephemeral, per-session Windows Stop event; never terminates the worker."""
import ctypes
import re


class StopSignal:
    def __init__(self, token, *, create):
        from ctypes import wintypes as w
        if not re.fullmatch(r'[0-9a-f]{64}', token):
            raise ValueError('Invalid local Stop token')
        self.handle = None
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateEventW.argtypes = [ctypes.c_void_p, w.BOOL, w.BOOL, w.LPCWSTR]
        self.kernel.CreateEventW.restype = w.HANDLE
        self.kernel.OpenEventW.argtypes = [w.DWORD, w.BOOL, w.LPCWSTR]
        self.kernel.OpenEventW.restype = w.HANDLE
        self.kernel.SetEvent.argtypes = [w.HANDLE]
        self.kernel.SetEvent.restype = w.BOOL
        self.kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        self.kernel.WaitForSingleObject.restype = w.DWORD
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.CloseHandle.restype = w.BOOL
        name = 'Local\\OBWEB-Stop-' + token
        if create:
            # Default event DACL belongs to the regular GUI user. The elevated
            # helper for that same user only requests SYNCHRONIZE access.
            self.handle = self.kernel.CreateEventW(None, True, False, name)
        else:
            self.handle = self.kernel.OpenEventW(0x00100000, False, name)
        if not self.handle:
            error = ctypes.get_last_error()
            raise OSError(error, 'Windows local Stop event could not be opened')

    def signal(self):
        if not self.kernel.SetEvent(self.handle):
            raise OSError(ctypes.get_last_error(), 'Windows local Stop event could not be signalled')

    def is_set(self):
        result = self.kernel.WaitForSingleObject(self.handle, 0)
        if result == 0:
            return True
        if result == 258:
            return False
        raise OSError(ctypes.get_last_error(), 'Windows local Stop event could not be checked')

    def close(self):
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
