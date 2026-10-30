"""Local Ethernet adapters. No host default routes, DNS or forwarding changes."""
import ctypes
import json
import os
from pathlib import Path
import select
import secrets
import re
import shutil
import subprocess
import sys


def openvpn_install_directories():
    """Read OpenVPN's installation location, including custom drives."""
    try:
        import winreg
    except ImportError:
        return []
    directories = []
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, r'SOFTWARE\OpenVPN', 0, winreg.KEY_READ | view) as key:
                    for value in ('', 'InstallDir'):
                        try:
                            directory, _ = winreg.QueryValueEx(key, value)
                            if isinstance(directory, str) and directory:
                                directories.append(directory)
                        except OSError:
                            pass
            except OSError:
                pass
    return directories


def find_tapctl():
    executable = shutil.which('tapctl.exe')
    if executable:
        return executable
    roots = openvpn_install_directories()
    roots.extend(str(Path(os.environ.get(variable, default)) / 'OpenVPN')
                 for variable, default in (('ProgramFiles', r'C:\Program Files'),
                                           ('ProgramFiles(x86)', r'C:\Program Files (x86)'),
                                           ('ProgramW6432', r'C:\Program Files')))
    for root in dict.fromkeys(roots):
        candidate = Path(os.path.expandvars(root)) / 'bin' / 'tapctl.exe'
        if candidate.is_file():
            return str(candidate)
    print('tapctl.exe was not found automatically. It is included with OpenVPN / TAP-Windows6.')
    while True:
        try:
            location = input('Enter the path to tapctl.exe or its folder (blank to cancel): ').strip()
        except (EOFError, OSError):
            raise RuntimeError('Could not read the tapctl.exe location. Run the launcher in an interactive terminal.') from None
        if not location:
            raise RuntimeError('TAP setup cancelled; install TAP-Windows6 and locate tapctl.exe before retrying.')
        candidate = Path(os.path.expandvars(location.strip('\"').strip("'"))).expanduser()
        if candidate.is_dir():
            candidate = candidate / 'tapctl.exe'
        if candidate.name.lower() == 'tapctl.exe' and candidate.is_file():
            return str(candidate.resolve())
        print('tapctl.exe was not found at that location. Enter its full path or the folder containing it.')


def marker(occupied):
    # Adapter discovery address only; never used by the PS2 or WSS transport.
    while True:
        address = f'169.254.{secrets.randbelow(254) + 1}.{secrets.randbelow(254) + 1}'
        if address not in occupied:
            return address


class LinuxTap:
    name = 'obw-pcsx2'

    def __init__(self):
        self.fd = None

    def __enter__(self):
        import fcntl
        import struct
        if os.geteuid():
            raise RuntimeError('Local Ethernet setup requires sudo; use start-ethernet.sh.')
        if Path('/sys/class/net', self.name).exists():
            raise RuntimeError('obw-pcsx2 already exists; stop its owner before starting another session.')
        occupied = subprocess.run(['ip', '-j', '-4', 'address', 'show'], check=True, capture_output=True, text=True).stdout
        address = marker(occupied)
        self.fd = os.open('/dev/net/tun', os.O_RDWR | os.O_NONBLOCK)
        try:
            fcntl.ioctl(self.fd, 0x400454ca, struct.pack('16sH', self.name.encode(), 0x0002 | 0x1000 | 0x8000))
            # PCSX2 requires a host IPv4 on the capture adapter. This /32 creates
            # no subnet/default route; the guest obtains its own lease remotely.
            subprocess.run(['ip', 'address', 'add', address + '/32', 'dev', self.name], check=True, capture_output=True)
            Path(f'/proc/sys/net/ipv6/conf/{self.name}/disable_ipv6').write_text('1')
            subprocess.run(['ip', 'link', 'set', self.name, 'up'], check=True, capture_output=True)
            self.mac = bytes.fromhex(Path('/sys/class/net', self.name, 'address').read_text().strip().replace(':', ''))
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def read(self):
        if not select.select([self.fd], [], [], .25)[0]:
            return None
        try:
            return os.read(self.fd, 65536)
        except BlockingIOError:
            return None

    def write(self, frame):
        if os.write(self.fd, frame) != len(frame):
            raise RuntimeError('Incomplete local Ethernet write')

    def __exit__(self, *args):
        if self.fd is not None:
            os.close(self.fd)  # Nonpersistent TAP is removed with its final descriptor.
            self.fd = None


class WindowsTap:
    """Use a TAP-Windows6 adapter via its driver API; Npcap is used by PCSX2."""
    def __init__(self, name=None):
        self.name = name or 'obw-pcsx2'
        self.created = False
        self.address_added = False
        self.handle = None
        self.tapctl = None
        self.restore_dhcp = False

    @staticmethod
    def powershell(script):
        # Windows PowerShell otherwise uses the active console code page, which
        # may differ from Python's UTF-8 default. Keep both pipes as bytes so an
        # undecodable diagnostic cannot crash subprocess's reader thread.
        prelude = ('$ErrorActionPreference="Stop"; '
                   '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); '
                   '$OutputEncoding = [Console]::OutputEncoding; ')
        # Emit structured local error metadata, never the full command, error
        # body or an unrelated diagnostic stream.
        guarded = ('try { ' + script + ' } catch { '
                   '$details = @{ error_id = $_.FullyQualifiedErrorId; '
                   'category = $_.CategoryInfo.Category.ToString(); '
                   'exception = $_.Exception.GetType().FullName; '
                   'hresult = $_.Exception.HResult; '
                   'native_code = $_.Exception.NativeErrorCode }; '
                   '[Console]::Error.WriteLine("OBWEB_PS_ERROR:" + '
                   '($details | ConvertTo-Json -Compress)); exit 1 }')
        command = re.search(r'\b(?:Get|Set|New|Remove)-[A-Za-z]+', script)
        operation = command[0] if command else 'PowerShell'
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                                 prelude + guarded], capture_output=True)
        if result.returncode:
            details = []
            for line in result.stderr.splitlines():
                if not line.startswith(b'OBWEB_PS_ERROR:'):
                    continue
                try:
                    record = json.loads(line[len(b'OBWEB_PS_ERROR:'):].decode('utf-8-sig'))
                    for key in ('error_id', 'category', 'exception', 'hresult', 'native_code'):
                        value = record.get(key)
                        if isinstance(value, (str, int)) and str(value):
                            clean = re.sub(r'[^A-Za-z0-9_., :+()\\/-]', '?', str(value))[:200]
                            details.append(f'{key}={clean}')
                except (UnicodeError, ValueError, AttributeError):
                    pass
                break
            detail = '; '.join(details) or 'no structured Windows error was returned'
            raise RuntimeError(f'Windows adapter operation failed at {operation} '
                               f'(exit {result.returncode}): {detail}')
        try:
            return result.stdout.decode('utf-8-sig').strip()
        except UnicodeDecodeError:
            raise RuntimeError('Windows adapter output was not valid UTF-8; verify the PowerShell installation and retry.') from None

    def adapters(self):
        raw = self.powershell('Get-NetAdapter -IncludeHidden | Select-Object Name,InterfaceDescription,InterfaceGuid,InterfaceIndex,MacAddress | ConvertTo-Json -Compress')
        data = json.loads(raw or '[]')
        return [data] if isinstance(data, dict) else data

    def __enter__(self):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            raise RuntimeError('Run start-ethernet.ps1 as Administrator.')
        try:
            adapters = self.adapters()
            matching = [a for a in adapters if a['Name'] == self.name]
            if not matching:
                self.tapctl = find_tapctl()
                result = subprocess.run([self.tapctl, 'create', '--hwid', 'tap0901', '--name', self.name], capture_output=True)
                if result.returncode:
                    raise RuntimeError('Could not create the dedicated TAP-Windows6 adapter.')
                self.created = True
                guid = re.search(rb'\{[0-9a-fA-F-]{36}\}', result.stdout)
                if guid:
                    self.guid = guid[0].decode('ascii')
                matching = [a for a in self.adapters() if a['Name'] == self.name]
            if len(matching) != 1 or 'TAP-Windows' not in matching[0]['InterfaceDescription']:
                raise RuntimeError('Select a dedicated TAP-Windows6 adapter; physical adapters are not supported in local Ethernet mode.')
            adapter = matching[0]
            self.guid = '{' + adapter['InterfaceGuid'].strip('{}') + '}'
            self.index = int(adapter['InterfaceIndex'])
            self.mac = bytes.fromhex(adapter['MacAddress'].replace('-', ''))
            routes = self.powershell(f'@(Get-NetRoute -InterfaceIndex {self.index} -DestinationPrefix 0.0.0.0/0 -ErrorAction SilentlyContinue).Count')
            if routes != '0':
                raise RuntimeError('The selected TAP adapter has a default route; use a dedicated adapter.')
            addresses = self.powershell(f'@(Get-NetIPAddress -InterfaceIndex {self.index} -AddressFamily IPv4 -ErrorAction SilentlyContinue).Count')
            if addresses == '0':
                self.restore_dhcp = self.powershell(f'(Get-NetIPInterface -InterfaceIndex {self.index} -AddressFamily IPv4).Dhcp.ToString()') == 'Enabled'
                self.address = marker(self.powershell('Get-NetIPAddress -AddressFamily IPv4 | Select-Object -ExpandProperty IPAddress'))
                self.powershell(f'New-NetIPAddress -InterfaceIndex {self.index} -IPAddress {self.address} -PrefixLength 32 -SkipAsSource $true | Out-Null')
                self.address_added = True
            self._open()
            return self
        except BaseException:
            try:
                self.__exit__(None, None, None)
            except Exception as cleanup_error:
                # Keep the setup error visible even when partial cleanup fails.
                print(str(cleanup_error) if isinstance(cleanup_error, RuntimeError)
                      else 'Windows TAP cleanup failed; check the dedicated adapter before retrying.',
                      file=sys.stderr)
            raise

    def _open(self):
        from ctypes import wintypes as w
        class Overlapped(ctypes.Structure):
            _fields_ = [('Internal', ctypes.c_size_t), ('InternalHigh', ctypes.c_size_t),
                        ('Offset', w.DWORD), ('OffsetHigh', w.DWORD), ('hEvent', w.HANDLE)]
        self.Overlapped = Overlapped
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateFileW.argtypes = [w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
        self.kernel.CreateFileW.restype = w.HANDLE
        self.kernel.CreateEventW.argtypes = [ctypes.c_void_p,w.BOOL,w.BOOL,w.LPCWSTR]
        self.kernel.CreateEventW.restype = w.HANDLE
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.CancelIoEx.argtypes = [w.HANDLE,ctypes.POINTER(Overlapped)]
        self.kernel.WaitForSingleObject.argtypes = [w.HANDLE,w.DWORD]
        self.kernel.GetOverlappedResult.argtypes = [w.HANDLE,ctypes.POINTER(Overlapped),ctypes.POINTER(w.DWORD),w.BOOL]
        self.kernel.ReadFile.argtypes = [w.HANDLE,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD),ctypes.POINTER(Overlapped)]
        self.kernel.WriteFile.argtypes = self.kernel.ReadFile.argtypes
        self.kernel.DeviceIoControl.argtypes = [w.HANDLE,w.DWORD,ctypes.c_void_p,w.DWORD,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD),ctypes.POINTER(Overlapped)]
        handle = self.kernel.CreateFileW('\\\\.\\Global\\' + self.guid + '.tap', 0xc0000000, 3, None, 3, 0x40000000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise RuntimeError('Could not open the TAP-Windows6 driver. Stop other software using this adapter.')
        self.handle = handle
        status = w.ULONG(1)
        self._operation('control', status, ctypes.sizeof(status), 3000)

    def _operation(self, operation, buffer, size, timeout):
        from ctypes import wintypes as w
        event = self.kernel.CreateEventW(None, True, False, None)
        if not event:
            raise ctypes.WinError(ctypes.get_last_error())
        ov = self.Overlapped(hEvent=event)
        count = w.DWORD()
        try:
            if operation == 'control':
                # TAP_WIN_IOCTL_SET_MEDIA_STATUS, function 6, METHOD_BUFFERED.
                ok = self.kernel.DeviceIoControl(self.handle, (0x22 << 16) | (6 << 2), ctypes.byref(buffer), size, ctypes.byref(buffer), size, ctypes.byref(count), ctypes.byref(ov))
            else:
                function = self.kernel.ReadFile if operation == 'read' else self.kernel.WriteFile
                ok = function(self.handle, buffer, size, ctypes.byref(count), ctypes.byref(ov))
            if ok:
                return count.value
            if ctypes.get_last_error() != 997:
                raise ctypes.WinError(ctypes.get_last_error())
            if self.kernel.WaitForSingleObject(event, timeout) != 0:
                self.kernel.CancelIoEx(self.handle, ctypes.byref(ov))
                self.kernel.GetOverlappedResult(self.handle, ctypes.byref(ov), ctypes.byref(count), True)
                raise TimeoutError('TAP operation timed out')
            if not self.kernel.GetOverlappedResult(self.handle, ctypes.byref(ov), ctypes.byref(count), True):
                raise ctypes.WinError(ctypes.get_last_error())
            return count.value
        finally:
            self.kernel.CloseHandle(event)

    def read(self):
        buffer = ctypes.create_string_buffer(65536)
        try:
            size = self._operation('read', buffer, len(buffer), 250)
            return buffer.raw[:size]
        except TimeoutError:
            return None

    def write(self, frame):
        buffer = ctypes.create_string_buffer(frame)
        if self._operation('write', buffer, len(frame), 3000) != len(frame):
            raise RuntimeError('Incomplete TAP-Windows write')

    def __exit__(self, *args):
        if self.handle is not None:
            self.kernel.CancelIoEx(self.handle, None)
            self.kernel.CloseHandle(self.handle)
            self.handle = None
        if self.created:
            # tapctl accepts the interface GUID, not an interpolated shell command.
            if hasattr(self, 'guid'):
                result = subprocess.run([self.tapctl, 'delete', self.guid], capture_output=True)
                if result.returncode:
                    print('Could not remove the temporary TAP adapter; remove obw-pcsx2 using tapctl.', file=sys.stderr)
        elif self.address_added:
            self.powershell(f'Remove-NetIPAddress -InterfaceIndex {self.index} -IPAddress {self.address} -Confirm:$false')
            if self.restore_dhcp:
                self.powershell(f'Set-NetIPInterface -InterfaceIndex {self.index} -AddressFamily IPv4 -Dhcp Enabled')
