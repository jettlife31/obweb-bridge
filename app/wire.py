"""Minimal Ethernet/DHCP codec. No game payload logging or session replay."""
import ipaddress
import secrets
import socket
import struct
from dataclasses import dataclass



def checksum(data):
    data += b'\0' * (len(data) % 2)
    value = sum(struct.unpack('!' + 'H' * (len(data) // 2), data))
    while value >> 16:
        value = (value & 65535) + (value >> 16)
    return (~value) & 65535


def ipv4(frame):
    if len(frame) < 34 or frame[12:14] != b'\x08\x00':
        return None
    packet = frame[14:]
    ihl = (packet[0] & 15) * 4
    total = int.from_bytes(packet[2:4], 'big')
    if packet[0] >> 4 != 4 or not 20 <= ihl <= total <= len(packet):
        return None
    if checksum(packet[:ihl]):
        return None
    return packet[:total], ihl


def dhcp_request(mac, xid, requested=None, server=None):
    body = bytearray(240)
    struct.pack_into('!BBBBIHH', body, 0, 1, 1, 6, 0, xid, 0, 0x8000)
    body[28:34] = mac
    body[236:240] = bytes.fromhex('63825363')
    body += bytes([53, 1, 3 if requested else 1, 61, 7, 1]) + mac
    body += bytes([55, 4, 1, 3, 6, 51])
    if requested:
        body += bytes([50, 4]) + socket.inet_aton(requested)
        body += bytes([54, 4]) + socket.inet_aton(server)
    body += b'\xff'
    body += bytes(max(0, 300 - len(body)))
    udp = struct.pack('!HHHH', 68, 67, len(body) + 8, 0) + body
    ip = bytearray(struct.pack('!BBHHHBBH4s4s', 0x45, 0, 20 + len(udp), 0, 0,
                               64, 17, 0, bytes(4), b'\xff' * 4))
    struct.pack_into('!H', ip, 10, checksum(ip))
    return b'\xff' * 6 + mac + b'\x08\x00' + ip + udp


@dataclass(frozen=True)
class Lease:
    address: str
    gateway: str
    prefix: int
    seconds: int
    dns: tuple[str, ...] = ()


def dhcp_reply(frame, mac, xid):
    parsed = ipv4(frame)
    if parsed is None:
        return None
    p, h = parsed
    if p[9] != 17 or int.from_bytes(p[6:8], 'big') & 0x3fff or len(p) < h + 248:
        return None
    sport, dport, size, _ = struct.unpack_from('!HHHH', p, h)
    if (sport, dport) != (67, 68) or size < 248 or h + size > len(p):
        return None
    b = p[h + 8:h + size]
    if b[:3] != b'\x02\x01\x06' or int.from_bytes(b[4:8], 'big') != xid or b[28:34] != mac:
        return None
    if b[236:240] != bytes.fromhex('63825363'):
        return None
    opts, offset = {}, 240
    while offset < len(b):
        code = b[offset]; offset += 1
        if code == 255:
            break
        if code == 0:
            continue
        if offset >= len(b):
            return None
        n = b[offset]; offset += 1
        if offset + n > len(b):
            return None
        opts[code] = b[offset:offset + n]; offset += n
    return socket.inet_ntoa(b[16:20]), opts


async def acquire_lease(ws, mac, timeout=8, attempts=3):
    import asyncio
    xid = secrets.randbits(32)
    async def exchange(packet, expected):
        for _ in range(attempts):
            await ws.send(packet)
            deadline = asyncio.get_running_loop().time() + timeout
            while (remaining := deadline - asyncio.get_running_loop().time()) > 0:
                try:
                    raw = await asyncio.wait_for(ws.recv(), remaining)
                except asyncio.TimeoutError:
                    break
                if not isinstance(raw, bytes):
                    continue
                reply = dhcp_reply(raw, mac, xid)
                if reply and reply[1].get(53) == b'\x06':
                    raise RuntimeError('DHCP rejected by the tunnel')
                if reply and reply[1].get(53) == bytes([expected]):
                    return reply
        raise RuntimeError('Tunnel DHCP did not respond')
    address, opts = await exchange(dhcp_request(mac, xid), 2)
    if len(opts.get(54, b'')) != 4:
        raise RuntimeError('DHCP offer is missing the server identifier')
    server = socket.inet_ntoa(opts[54])
    acknowledged, ack = await exchange(dhcp_request(mac, xid, address, server), 5)
    if acknowledged != address or ack.get(54) != opts[54]:
        raise RuntimeError('DHCP ACK does not match the offer')
    config = dict(opts); config.update(ack)
    return lease_from_options(address, config)


def lease_from_options(address, options):
    def unicast(value):
        ip = ipaddress.IPv4Address(value)
        if ip.is_multicast or ip.is_loopback or ip.is_unspecified or int(ip) == 0xffffffff:
            raise ValueError('Expected unicast address')
        return str(ip)
    try:
        address = unicast(address)
        mask = socket.inet_ntoa(options[1])
        prefix = ipaddress.IPv4Network(f'0.0.0.0/{mask}').prefixlen
        gateway = unicast(socket.inet_ntoa(options[3][:4]))
        dns_bytes = options[6]
        if not dns_bytes or len(dns_bytes) % 4: raise ValueError('Invalid DNS list')
        dns = tuple(unicast(socket.inet_ntoa(dns_bytes[i:i+4])) for i in range(0, len(dns_bytes), 4))
        duration = options[51]
        if len(duration) != 4 or int.from_bytes(duration, 'big') < 30: raise ValueError('Invalid lease time')
        if ipaddress.ip_address(gateway) not in ipaddress.ip_network(f'{address}/{prefix}', strict=False):
            raise ValueError('Off-link gateway')
        if 121 in options or 249 in options:
            raise ValueError('Classless DHCP routes require support not yet implemented')
        return Lease(address, gateway, prefix, int.from_bytes(duration, 'big'), dns)
    except (ValueError, KeyError, OSError):
        raise RuntimeError('DHCP must provide IPv4, subnet mask, local gateway, DNS, and lease time; no external fallback') from None


def inbound(frame, mac, lease=None):
    """No IP/protocol/service filtering. Normalize only an invalid all-zero Ethernet destination."""
    if not isinstance(frame, bytes) or not 14 <= len(frame) <= 65535:
        return None
    return mac + frame[6:] if frame[:6] == bytes(6) else frame
