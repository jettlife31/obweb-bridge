"""Native Windows LAN capture/injection. Never changes host routes/DNS/forwarding."""
import ctypes as c
import ipaddress
import json
import os
from pathlib import Path
import re
import struct
import sys
import threading

from paths import ROOT


def interfaces():
    from ethernet_adapter import WindowsTap
    script = ('@(Get-NetAdapter | Where-Object Status -eq Up | ForEach-Object { '
              '$a=$_; Get-NetIPAddress -InterfaceIndex $a.InterfaceIndex -AddressFamily IPv4 '
              '-ErrorAction SilentlyContinue | Where-Object AddressState -eq Preferred | '
              'ForEach-Object { [pscustomobject]@{name=$a.Name; guid=$a.InterfaceGuid; '
              'index=$a.InterfaceIndex; mac=$a.MacAddress; ip=$_.IPAddress; prefix=$_.PrefixLength} } '
              '}) | ConvertTo-Json -Compress')
    raw = json.loads(WindowsTap.powershell(script) or '[]')
    rows = [raw] if isinstance(raw, dict) else raw
    result = []
    for row in rows:
        address = ipaddress.IPv4Address(row['ip'])
        if address.is_loopback or address.is_link_local or address.is_unspecified:
            continue
        result.append(row)
    return result


def inventory(name, lan_ip):
    from ethernet_adapter import WindowsTap
    rows = interfaces()
    matches = [r for r in rows if r['name'] == name and r['ip'] == lan_ip]
    if len(matches) != 1:
        raise RuntimeError('Select an active Windows LAN interface and IPv4 address.')
    row = matches[0]
    index = int(row['index'])
    forwarding = WindowsTap.powershell(f'(Get-NetIPInterface -InterfaceIndex {index} -AddressFamily IPv4).Forwarding.ToString()')
    if forwarding != 'Disabled':
        raise RuntimeError('Windows IP forwarding is already enabled on this interface. Disable routing/Internet Connection Sharing before using the native LAN endpoint.')
    mac = bytes.fromhex(row['mac'].replace('-', '').replace(':', ''))
    if len(mac) != 6 or mac[0] & 1 or mac == bytes(6):
        raise RuntimeError('The selected interface does not provide a usable Ethernet MAC.')
    guid = row['guid'].strip('{}')
    if not re.fullmatch(r'[0-9a-fA-F-]{36}', guid):
        raise RuntimeError('Invalid Windows LAN adapter identifier.')
    network = ipaddress.ip_network(f'{row["ip"]}/{int(row["prefix"])}', strict=False)
    if network.prefixlen < 16 or network.prefixlen > 30:
        raise RuntimeError('Select a client LAN with an IPv4 prefix between /16 and /30.')
    return dict(interface=name, index=index, lan_ip=row['ip'], client_network=str(network),
                mac=mac, device='\\Device\\NPF_{' + guid + '}',
                local_ips=tuple(sorted({r['ip'] for r in rows})))


class PacketHeader(c.Structure):
    # Windows timeval uses two 32-bit LONGs, including on x64.
    _fields_ = [('seconds', c.c_int32), ('micros', c.c_int32),
                ('caplen', c.c_uint32), ('length', c.c_uint32)]


class BPF(c.Structure):
    _fields_ = [('length', c.c_uint), ('instructions', c.c_void_p)]


class Npcap:
    def __init__(self, plan):
        self.plan, self.handle, self.directory = plan, None, None

    def __enter__(self):
        folder = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/Npcap'
        if not (folder / 'wpcap.dll').is_file():
            raise RuntimeError('Install Npcap from https://npcap.com/#download before starting the Windows LAN gateway.')
        self.directory = os.add_dll_directory(str(folder))
        try:
            self.dll = c.CDLL(str(folder / 'wpcap.dll'))
            d = self.dll
            d.pcap_open_live.argtypes = [c.c_char_p, c.c_int, c.c_int, c.c_int, c.c_char_p]
            d.pcap_open_live.restype = c.c_void_p
            d.pcap_close.argtypes = [c.c_void_p]
            d.pcap_datalink.argtypes = [c.c_void_p]
            d.pcap_compile.argtypes = [c.c_void_p, c.POINTER(BPF), c.c_char_p, c.c_int, c.c_uint32]
            d.pcap_setfilter.argtypes = [c.c_void_p, c.POINTER(BPF)]
            d.pcap_freecode.argtypes = [c.POINTER(BPF)]
            d.pcap_next_ex.argtypes = [c.c_void_p, c.POINTER(c.POINTER(PacketHeader)), c.POINTER(c.POINTER(c.c_ubyte))]
            d.pcap_sendpacket.argtypes = [c.c_void_p, c.c_void_p, c.c_int]
            d.pcap_setnonblock.argtypes = [c.c_void_p, c.c_int, c.c_char_p]
            self.handle = d.pcap_open_live(self.plan['device'].encode('ascii'), 65535, 0, 100, c.create_string_buffer(256))
            if not self.handle:
                raise RuntimeError('Npcap could not open the selected LAN interface. Check its driver binding and administrator access.')
            if d.pcap_datalink(self.handle) != 1:
                raise RuntimeError('The selected Npcap interface does not expose Ethernet frames.')
            mac = ':'.join(f'{b:02x}' for b in self.plan['mac'])
            local_sources = ' or '.join(f'src host {ip}' for ip in self.plan['local_ips'])
            local_destinations = ' or '.join(f'dst host {ip}' for ip in self.plan['local_ips'])
            expression = (f'ether dst {mac} and ip and src net {self.plan["client_network"]} '
                          f'and not ({local_sources}) and (not ({local_destinations}) or '
                          f'(dst host {self.plan["lan_ip"]} and (udp dst port 53 or tcp dst port 53)))')
            program = BPF()
            if d.pcap_compile(self.handle, c.byref(program), expression.encode('ascii'), 1, 0xffffffff):
                raise RuntimeError('Npcap could not compile the client LAN filter.')
            try:
                if d.pcap_setfilter(self.handle, c.byref(program)):
                    raise RuntimeError('Npcap could not apply the client LAN filter.')
            finally:
                d.pcap_freecode(c.byref(program))
            # Explicit nonblocking reads guarantee Stop can join the reader even
            # on an otherwise silent interface. No pcap handle closes mid-read.
            if d.pcap_setnonblock(self.handle, 1, c.create_string_buffer(256)):
                raise RuntimeError('Npcap could not enable nonblocking reads.')
            return self
        except BaseException:
            self.__exit__()
            raise

    def read(self):
        header, data = c.POINTER(PacketHeader)(), c.POINTER(c.c_ubyte)()
        status = self.dll.pcap_next_ex(self.handle, c.byref(header), c.byref(data))
        if status == 0:
            return None
        if status != 1:
            raise RuntimeError('Npcap LAN read failed.')
        size = header.contents.caplen
        if not 14 <= size <= 65535 or size != header.contents.length:
            return None
        return c.string_at(data, size)

    def write(self, frame):
        if self.dll.pcap_sendpacket(self.handle, frame, len(frame)):
            raise RuntimeError('Npcap LAN write failed.')

    def __exit__(self, *args):
        if self.handle:
            self.dll.pcap_close(self.handle)
            self.handle = None
        if self.directory:
            self.directory.close()
            self.directory = None


class DivertAddress(c.Structure):
    _fields_ = [('timestamp', c.c_int64), ('flags', c.c_uint32),
                ('reserved', c.c_uint32), ('data', c.c_ubyte * 64)]


def locate_windivert():
    if c.sizeof(c.c_void_p) != 8:
        raise RuntimeError('The native Windows LAN gateway requires 64-bit Python and WinDivert x64.')
    for folder in (ROOT / 'third_party/WinDivert/x64', ROOT / 'WinDivert/x64'):
        if (folder / 'WinDivert.dll').is_file() and (folder / 'WinDivert64.sys').is_file():
            return folder / 'WinDivert.dll'
    text = input('Locate WinDivert.dll (x64, beside the signed WinDivert64.sys driver): ').strip().strip('"')
    path = Path(text).expanduser()
    if path.is_dir():
        path = path / 'WinDivert.dll'
    if not text or path.name.lower() != 'windivert.dll' or not path.is_file() or not (path.parent / 'WinDivert64.sys').is_file():
        raise RuntimeError('Download the official WinDivert 2.2 x64 package and keep its DLL and signed driver together.')
    return path.resolve()


class WindowsGuards:
    """Drop local DNS delivery and only OS routing errors for relayed clients.

    Npcap handles actual relay traffic. Windows forwarding remains disabled,
    including if this process crashes. No firewall/route/settings are edited.
    """
    def __init__(self, plan, dll=None):
        self.plan, self.path = plan, dll
        self.handles, self.threads = [], []
        self.stopped = threading.Event()
        self.error = None

    def __enter__(self):
        from windows_packets import routing_error
        path = self.path or locate_windivert()
        try:
            self.dll = c.WinDLL(str(path), use_last_error=True)
        except OSError as error:
            raise RuntimeError(f'WinDivert DLL could not load (Windows error {error.winerror}).') from None
        d = self.dll
        d.WinDivertOpen.argtypes = [c.c_char_p, c.c_int, c.c_int16, c.c_uint64]
        d.WinDivertOpen.restype = c.c_void_p
        d.WinDivertRecv.argtypes = [c.c_void_p, c.c_void_p, c.c_uint, c.POINTER(c.c_uint), c.POINTER(DivertAddress)]
        d.WinDivertSend.argtypes = [c.c_void_p, c.c_void_p, c.c_uint, c.POINTER(c.c_uint), c.POINTER(DivertAddress)]
        d.WinDivertShutdown.argtypes = [c.c_void_p, c.c_int]
        d.WinDivertClose.argtypes = [c.c_void_p]
        network = ipaddress.IPv4Network(self.plan['client_network'])
        client = (f'ip.SrcAddr >= {network.network_address} and ip.SrcAddr <= {network.broadcast_address}'
                  + ''.join(f' and ip.SrcAddr != {ip}' for ip in self.plan['local_ips']))
        dns = (f'ip and inbound and ifIdx == {self.plan["index"]} and ({client}) and '
               f'ip.DstAddr == {self.plan["lan_ip"]} and ((udp and udp.DstPort == 53) or (tcp and tcp.DstPort == 53))')
        errors = (f'ip and outbound and ifIdx == {self.plan["index"]} and icmp and ip.DstAddr >= {network.network_address} '
                  f'and ip.DstAddr <= {network.broadcast_address} and '
                  '(icmp.Type == 3 or icmp.Type == 5 or icmp.Type == 11 or icmp.Type == 12)')
        try:
            # DROP|RECV_ONLY for DNS: no application payloads cross this handle.
            self._open(dns, flags=2 | 4)
            handle = self._open(errors)
            def guard():
                try:
                    while not self.stopped.is_set():
                        packet = c.create_string_buffer(65535)
                        size, address = c.c_uint(), DivertAddress()
                        if not d.WinDivertRecv(handle, packet, len(packet), c.byref(size), c.byref(address)):
                            if self.stopped.is_set():
                                return
                            raise RuntimeError('WinDivert routing-error guard read failed.')
                        if not routing_error(packet.raw[:size.value], self.plan):
                            if not d.WinDivertSend(handle, packet, size.value, None, c.byref(address)):
                                raise RuntimeError('WinDivert routing-error guard reinjection failed.')
                except RuntimeError as error:
                    self.error = error
            thread = threading.Thread(target=guard, daemon=True)
            thread.start()
            self.threads.append(thread)
            return self
        except BaseException:
            self.__exit__()
            raise

    def _open(self, expression, flags=0):
        handle = self.dll.WinDivertOpen(expression.encode('ascii'), 0, 100, flags)
        if handle in (None, c.c_void_p(-1).value):
            code = c.get_last_error()
            raise RuntimeError(f'WinDivert could not start (Windows error {code}). Check administrator approval and the official signed driver; see the Windows LAN guide.')
        self.handles.append(handle)
        return handle

    def __exit__(self, *args):
        self.stopped.set()
        for handle in self.handles:
            self.dll.WinDivertShutdown(handle, 0)  # Wake any blocked receive.
        for thread in self.threads:
            thread.join(timeout=5)
        alive = any(thread.is_alive() for thread in self.threads)
        for handle in self.handles:
            self.dll.WinDivertClose(handle)
        self.handles.clear()
        if alive:
            raise RuntimeError('WinDivert guard did not stop cleanly.')
