"""IPv4 address translation for the native LAN endpoint; no payload inspection/logging."""
import ipaddress
import struct
from wire import checksum


def packet_header(packet):
    if len(packet) < 20 or packet[0] >> 4 != 4:
        return None
    h = (packet[0] & 15) * 4
    total = int.from_bytes(packet[2:4], 'big')
    return (h, total) if 20 <= h <= total <= len(packet) else None


def adjust_checksum(value, old, new):
    """RFC 1624 one's-complement update, including first fragments."""
    result = (~value) & 0xffff
    for before, after in zip(struct.unpack('!' + 'H' * (len(old) // 2), old),
                             struct.unpack('!' + 'H' * (len(new) // 2), new)):
        result += ((~before) & 0xffff) + after
    while result >> 16:
        result = (result & 0xffff) + (result >> 16)
    return (~result) & 0xffff


def translate(packet, *, source=None, destination=None, quoted=None):
    """Change IP addresses, preserving ports and all protocol/application bytes.

    Every fragment gets its IP header updated. The initial TCP/UDP fragment
    receives an incremental pseudo-header update; complete packets are computed
    from scratch to accommodate NIC checksum offload. ICMP error quotations are
    translated back as well, including truncated UDP headers.
    """
    parsed = packet_header(packet)
    if parsed is None:
        raise ValueError('Invalid IPv4 packet')
    h, total = parsed
    p = bytearray(packet[:total])
    before = bytes(p[12:20])
    if source is not None:
        p[12:16] = ipaddress.IPv4Address(source).packed
    if destination is not None:
        p[16:20] = ipaddress.IPv4Address(destination).packed
    after = bytes(p[12:20])
    fragment = int.from_bytes(p[6:8], 'big')
    if not fragment & 0x1fff:
        protocol = p[9]
        offset = {6: 16, 17: 6}.get(protocol)
        if offset is not None:
            if len(p) < h + offset + 2:
                raise ValueError('Truncated transport checksum')
            location = h + offset
            value = int.from_bytes(p[location:location + 2], 'big')
            # IPv4 UDP zero explicitly means no checksum.
            if protocol != 17 or value:
                if fragment & 0x2000:
                    value = adjust_checksum(value, before, after)
                else:
                    p[location:location + 2] = bytes(2)
                    pseudo = after + bytes([0, protocol]) + (len(p) - h).to_bytes(2, 'big')
                    value = checksum(pseudo + bytes(p[h:]))
                if protocol == 17 and not value:
                    value = 0xffff
                p[location:location + 2] = value.to_bytes(2, 'big')
        if protocol == 1 and len(p) >= h + 8 and p[h] in (3, 4, 5, 11, 12) and quoted:
            q = h + 8
            if len(p) >= q + 20 and p[q] >> 4 == 4:
                old_body = bytes(p[h:])
                qh = (p[q] & 15) * 4
                if qh >= 20 and len(p) >= q + qh:
                    old_ips = bytes(p[q + 12:q + 20])
                    for position in (q + 12, q + 16):
                        address = str(ipaddress.IPv4Address(bytes(p[position:position + 4])))
                        if address in quoted:
                            p[position:position + 4] = ipaddress.IPv4Address(quoted[address]).packed
                    new_ips = bytes(p[q + 12:q + 20])
                    off = {6: 16, 17: 6}.get(p[q + 9])
                    if off is not None and not int.from_bytes(p[q + 6:q + 8], 'big') & 0x1fff and len(p) >= q + qh + off + 2:
                        location = q + qh + off
                        value = int.from_bytes(p[location:location + 2], 'big')
                        if p[q + 9] != 17 or value:
                            value = adjust_checksum(value, old_ips, new_ips)
                            if p[q + 9] == 17 and not value:
                                value = 0xffff
                            p[location:location + 2] = value.to_bytes(2, 'big')
                    p[q + 10:q + 12] = bytes(2)
                    p[q + 10:q + 12] = checksum(bytes(p[q:q + qh])).to_bytes(2, 'big')
                    value = adjust_checksum(int.from_bytes(p[h + 2:h + 4], 'big'), old_body + bytes(len(old_body) % 2), bytes(p[h:]) + bytes(len(old_body) % 2))
                    p[h + 2:h + 4] = value.to_bytes(2, 'big')
    p[10:12] = bytes(2)
    p[10:12] = checksum(bytes(p[:h])).to_bytes(2, 'big')
    return bytes(p)


def classify(frame, plan):
    """Accept only client-to-gateway Ethernet, excluding this host's traffic."""
    if len(frame) < 34 or frame[12:14] != b'\x08\x00' or frame[:6] != plan['mac'] or frame[6] & 1 or frame[6:12] == plan['mac']:
        return None
    parsed = packet_header(frame[14:])
    if parsed is None:
        return None
    h, total = parsed
    packet = frame[14:14 + total]
    source = ipaddress.IPv4Address(bytes(packet[12:16]))
    destination = ipaddress.IPv4Address(bytes(packet[16:20]))
    network = ipaddress.IPv4Network(plan['client_network'])
    if source not in network or str(source) in plan['local_ips'] or source in (network.network_address, network.broadcast_address):
        return None
    if source.is_loopback or source.is_multicast or source.is_unspecified:
        return None
    if destination.is_multicast or destination.is_unspecified or destination.is_loopback or destination in (network.broadcast_address, ipaddress.IPv4Address('255.255.255.255')):
        return None
    dns = str(destination) == plan['lan_ip']
    if str(destination) in plan['local_ips']:
        if not dns or packet[9] not in (6, 17) or int.from_bytes(packet[6:8], 'big') & 0x3fff or len(packet) < h + 4 or int.from_bytes(packet[h + 2:h + 4], 'big') != 53:
            return None
    return str(source), frame[6:12], dns, packet


def routing_error(packet, plan):
    """Suppress only Windows ICMP errors quoting traffic for our LAN relay."""
    parsed = packet_header(packet)
    if parsed is None:
        return False
    h, total = parsed
    if packet[9] != 1 or total < h + 28 or packet[h] not in (3, 5, 11, 12):
        return False
    if str(ipaddress.IPv4Address(bytes(packet[12:16]))) not in plan['local_ips']:
        return False
    client = str(ipaddress.IPv4Address(bytes(packet[16:20])))
    q = h + 8
    if packet[q] >> 4 != 4 or packet[q + 12:q + 16] != packet[16:20]:
        return False
    destination = str(ipaddress.IPv4Address(bytes(packet[q + 16:q + 20])))
    if ipaddress.IPv4Address(client) not in ipaddress.IPv4Network(plan['client_network']) or client in plan['local_ips']:
        return False
    if destination not in plan['local_ips']:
        return True
    # An inbound firewall rejection may precede the NETWORK-layer DNS guard.
    # Suppress that OS error too; the DNS request itself travels over Npcap.
    qh = (packet[q] & 15) * 4
    return (destination == plan['lan_ip'] and qh >= 20 and total >= q + qh + 4
            and packet[q + 9] in (6, 17) and int.from_bytes(packet[q + qh + 2:q + qh + 4], 'big') == 53)
