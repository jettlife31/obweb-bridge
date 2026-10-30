#!/usr/bin/env python3
"""Read-only Npcap LAN counters: no packet files, DNS names or application data."""
import argparse
import collections
import ctypes as c
import ipaddress
import json
import os
from pathlib import Path
import struct
import sys
import time


def ipv4_header(frame):
    if len(frame) < 20 or frame[0] >> 4 != 4:
        return None
    length = (frame[0] & 15) * 4
    if length < 20 or len(frame) < length:
        return None
    return length, frame[9], str(ipaddress.IPv4Address(frame[12:16])), str(ipaddress.IPv4Address(frame[16:20]))


def metadata(frame, client, bridge):
    if len(frame) < 14 or frame[12:14] != b'\x08\x00':
        return None
    packet = frame[14:]
    header = ipv4_header(packet)
    if header is None:
        return None
    length, protocol, src, dst = header
    if client not in (src, dst):
        return None
    outgoing = src == client
    result = {'direction': 'from-client' if outgoing else 'to-client',
              'peer_is_bridge': (dst if outgoing else src) == bridge,
              'ip_protocol': protocol}
    if int.from_bytes(packet[6:8], 'big') & 0x1fff:
        result['fragment'] = True
        return result
    data = packet[length:]
    if protocol in (6, 17) and len(data) >= 4:
        source, destination = struct.unpack_from('!HH', data)
        result['service_port'] = destination if outgoing else source
        if protocol == 6 and len(data) >= 14:
            result['tcp_flags'] = data[13]
        if protocol == 17 and 53 in (source, destination) and len(data) >= 12:
            result['dns_response'] = bool(data[10] & 128)
            if result['dns_response']:
                result['dns_rcode'] = data[11] & 15
    elif protocol == 1 and len(data) >= 2:
        result.update(icmp_type=data[0], icmp_code=data[1])
        if data[0] == 3 and len(data) >= 28:
            rejected = data[8:]
            inner = ipv4_header(rejected)
            if inner:
                size, proto, _, target = inner
                result.update(rejected_protocol=proto, rejected_destination_is_bridge=target == bridge)
                if proto in (6, 17) and len(rejected) >= size + 4:
                    result['rejected_destination_port'] = struct.unpack_from('!H', rejected, size + 2)[0]
    return result


class Address(c.Structure):
    pass
Address._fields_ = [('next', c.POINTER(Address)), ('addr', c.c_void_p),
                    ('netmask', c.c_void_p), ('broadaddr', c.c_void_p), ('dstaddr', c.c_void_p)]


class Device(c.Structure):
    pass
Device._fields_ = [('next', c.POINTER(Device)), ('name', c.c_char_p),
                   ('description', c.c_char_p), ('addresses', c.POINTER(Address)), ('flags', c.c_uint32)]


class Header(c.Structure):
    _fields_ = [('seconds', c.c_int32), ('microseconds', c.c_int32), ('caplen', c.c_uint32), ('length', c.c_uint32)]


class Program(c.Structure):
    _fields_ = [('length', c.c_uint), ('instructions', c.c_void_p)]


class Capture:
    def __init__(self, client, bridge):
        self.client, self.bridge = client, bridge
        self.handle = None
        self.directory = None

    def __enter__(self):
        directory = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'Npcap'
        try:
            self.directory = os.add_dll_directory(str(directory))
            self.lib = c.CDLL(str(directory / 'wpcap.dll'))
        except (OSError, AttributeError):
            self.close()
            raise RuntimeError('Npcap could not be loaded. Install Npcap from https://npcap.com/#download.') from None
        lib = self.lib
        lib.pcap_findalldevs.argtypes = [c.POINTER(c.POINTER(Device)), c.c_char_p]
        lib.pcap_findalldevs.restype = c.c_int
        lib.pcap_freealldevs.argtypes = [c.POINTER(Device)]
        lib.pcap_freealldevs.restype = None
        lib.pcap_open_live.argtypes = [c.c_char_p, c.c_int, c.c_int, c.c_int, c.c_char_p]
        lib.pcap_open_live.restype = c.c_void_p
        lib.pcap_datalink.argtypes = [c.c_void_p]
        lib.pcap_datalink.restype = c.c_int
        lib.pcap_compile.argtypes = [c.c_void_p, c.POINTER(Program), c.c_char_p, c.c_int, c.c_uint32]
        lib.pcap_compile.restype = c.c_int
        lib.pcap_setfilter.argtypes = [c.c_void_p, c.POINTER(Program)]
        lib.pcap_setfilter.restype = c.c_int
        lib.pcap_freecode.argtypes = [c.POINTER(Program)]
        lib.pcap_freecode.restype = None
        lib.pcap_next_ex.argtypes = [c.c_void_p, c.POINTER(c.POINTER(Header)), c.POINTER(c.POINTER(c.c_ubyte))]
        lib.pcap_next_ex.restype = c.c_int
        lib.pcap_close.argtypes = [c.c_void_p]
        lib.pcap_close.restype = None
        # A nonblocking read bounds observation even when no packets arrive.
        lib.pcap_setnonblock.argtypes = [c.c_void_p, c.c_int, c.c_char_p]
        lib.pcap_setnonblock.restype = c.c_int
        devices = c.POINTER(Device)()
        error = c.create_string_buffer(256)
        try:
            if lib.pcap_findalldevs(c.byref(devices), error):
                raise RuntimeError('Could not enumerate Npcap adapters. Check its driver and permissions.')
            names = []
            current = devices
            while current:
                address = current.contents.addresses
                while address:
                    pointer = address.contents.addr
                    if pointer:
                        raw = c.string_at(pointer, 8)
                        if int.from_bytes(raw[:2], sys.byteorder) == 2 and str(ipaddress.IPv4Address(raw[4:8])) == self.bridge:
                            names.append(bytes(current.contents.name))
                            break
                    address = address.contents.next
                current = current.contents.next
            if len(names) != 1:
                raise RuntimeError('Select a bridge LAN IPv4 assigned to exactly one Npcap adapter.')
            self.handle = lib.pcap_open_live(names[0], 128, 0, 100, error)
            if not self.handle:
                raise RuntimeError('Could not open the LAN adapter. Run this diagnostic as Administrator and check Npcap.')
            if lib.pcap_datalink(self.handle) != 1:
                raise RuntimeError('The selected capture adapter does not provide Ethernet frames.')
            program = Program()
            if lib.pcap_compile(self.handle, c.byref(program), f'ip and host {self.client}'.encode('ascii'), 1, 0xffffffff):
                raise RuntimeError('Could not prepare the client-only capture filter.')
            try:
                if lib.pcap_setfilter(self.handle, c.byref(program)):
                    raise RuntimeError('Could not apply the client-only capture filter.')
            finally:
                lib.pcap_freecode(c.byref(program))
            if lib.pcap_setnonblock(self.handle, 1, error):
                raise RuntimeError('Could not enable bounded Npcap reads.')
            return self
        except BaseException:
            self.close()
            raise
        finally:
            if devices:
                lib.pcap_freealldevs(devices)

    def read(self):
        header, packet = c.POINTER(Header)(), c.POINTER(c.c_ubyte)()
        code = self.lib.pcap_next_ex(self.handle, c.byref(header), c.byref(packet))
        if code == 0:
            time.sleep(.02)
            return None
        if code != 1:
            raise RuntimeError('Npcap stopped reading the LAN adapter.')
        if not 0 <= header.contents.caplen <= 128:
            raise RuntimeError('Npcap returned an invalid captured length.')
        return c.string_at(packet, header.contents.caplen)

    def close(self):
        if self.handle:
            self.lib.pcap_close(self.handle)
            self.handle = None
        if self.directory:
            self.directory.close()
            self.directory = None

    def __exit__(self, *args):
        self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-ip', required=True, type=ipaddress.IPv4Address)
    parser.add_argument('--lan-ip', required=True, type=ipaddress.IPv4Address)
    parser.add_argument('--seconds', type=int, default=45)
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Run this diagnostic with Windows Python, not inside WSL.')
    if not 5 <= args.seconds <= 120 or args.client_ip == args.lan_ip:
        parser.error('Use distinct client/bridge IPs and 5 to 120 seconds.')
    client, bridge = str(args.client_ip), str(args.lan_ip)
    counts = collections.Counter()
    try:
        with Capture(client, bridge) as capture:
            print(f'Counting only the selected LAN client for {args.seconds}s. Try connecting NOW. No packet files or DNS names are saved.', flush=True)
            end = time.monotonic() + args.seconds
            while time.monotonic() < end:
                frame = capture.read()
                if frame is not None:
                    item = metadata(frame, client, bridge)
                    if item:
                        counts[json.dumps(item, sort_keys=True)] += 1
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2
    except OSError:
        print('Windows capture failed; no raw packet or driver error text was logged.', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        pass
    print(json.dumps({'duration_seconds': args.seconds, 'traffic': [dict(json.loads(item), count=count) for item, count in counts.items()],
                      'privacy': 'No packet files, application payloads, DNS names, MACs or unrelated IP addresses logged.'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
