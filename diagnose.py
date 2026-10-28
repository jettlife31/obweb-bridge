#!/usr/bin/env python3
"""Passive client counters and optional independent DNS-over-WSS test; no payload logging."""
import argparse
import asyncio
import ipaddress
import secrets
import subprocess
from urllib.parse import urlsplit
from dns_proxy import Resolver
from network import namespace_socket, NS, TAP
import collections
import json
import os
import select
import socket
import struct
import time


def dns_metadata(data, expected_name=None):
    if len(data) < 12: return {}
    fields = struct.unpack_from('!6H', data)
    result = {'dns_flags': fields[1], 'dns_questions': fields[2], 'dns_additional': fields[5], 'dns_bytes': len(data)}
    if not fields[2]: return result
    labels = []; offset = 12; end = None; seen = set()
    try:
        while True:
            if offset in seen or offset >= len(data): return result
            seen.add(offset); length = data[offset]; offset += 1
            if not length: break
            if length & 192 == 192:
                if offset >= len(data): return result
                end = end or offset + 1
                offset = ((length & 63) << 8) | data[offset]
                continue
            if length > 63 or offset + length > len(data): return result
            labels.append(data[offset:offset + length].decode('ascii')); offset += length
        end = end or offset
        if end + 4 > len(data): return result
        typ, cls = struct.unpack_from('!HH', data, end)
        result.update(dns_qtype=typ, dns_qclass=cls)
        if expected_name is not None:
            result['dns_matches_requested_name'] = '.'.join(labels).lower() == expected_name.rstrip('.').lower()
    except (UnicodeError, struct.error): pass
    return result


def inspect(frame, client_scope, expected_name=None):
    if len(frame)<34 or frame[12:14]!=b'\x08\x00':return None
    p=frame[14:];h=(p[0]&15)*4
    if p[0]>>4!=4 or h<20 or len(p)<h:return None
    src,dst=socket.inet_ntoa(p[12:16]),socket.inet_ntoa(p[16:20])
    scope=ipaddress.ip_network(client_scope,strict=False)
    outgoing=ipaddress.ip_address(src) in scope
    if not outgoing and ipaddress.ip_address(dst) not in scope:return None
    r={'direction':'from-client' if outgoing else 'to-client','ip_protocol':p[9]}
    if p[9] in (6,17) and len(p)>=h+8 and not int.from_bytes(p[6:8],'big')&0x1fff:
        sp,dp=struct.unpack_from('!HH',p,h)
        r['service_port']=dp if outgoing else sp
        if p[9]==6 and len(p)>=h+14:r['tcp_flags']=p[h+13]
        if p[9]==17 and 53 in (sp,dp) and len(p)>=h+20:
            data=p[h+8:];r['dns_response']=bool(data[2]&128)
            if data[2]&128:r['dns_rcode']=data[3]&15
            r.update(dns_metadata(data, expected_name))
    return r


async def probe_remote_dns(server, hostname):
    labels = hostname.encode('idna').split(b'.')
    if not labels or any(not label or len(label) > 63 for label in labels):
        raise ValueError('Invalid endpoint hostname')
    query = secrets.token_bytes(2) + struct.pack('!5H', 0x100, 1, 0, 0, 0)
    query += b''.join(bytes([len(label)]) + label for label in labels) + b'\0\0\1\0\1'
    resolver = Resolver('', namespace_socket)
    resolver.servers = (server,)
    try:
        response = await resolver.resolve(query)
        return {'response_received': True, 'rcode': response[3] & 15}
    except (OSError, ValueError, asyncio.TimeoutError) as exc:
        return {'response_received': False, 'error_type': type(exc).__name__}


def tap_counts():
    result = subprocess.run(['ip', 'netns', 'exec', NS, 'ip', '-j', '-s', 'link', 'show', TAP],
                            capture_output=True, text=True)
    if result.returncode: return {'available': False}
    try:
        link = json.loads(result.stdout)[0]
        stats = link.get('stats64', link.get('stats', {}))
        return {'available': True, 'rx_packets': stats['rx']['packets'], 'tx_packets': stats['tx']['packets']}
    except (ValueError, KeyError, IndexError): return {'available': False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lan-interface',default=os.environ.get('OBWEB_LAN_INTERFACE'),help='Linux LAN interface used by the bridge')
    parser.add_argument('--lan-ip',default=os.environ.get('OBWEB_LAN_IP'),help='Local IPv4 used by the bridge')
    parser.add_argument('--seconds',type=int,default=45)
    parser.add_argument('--dns-name',help='DNS test name and capture comparison; other names are not shown')
    parser.add_argument('--test-dns',type=ipaddress.IPv4Address,help='DNS supplied by DHCP, for a namespace/WSS test only')
    parser.add_argument('--url',default=os.environ.get('OBWEB_WSS_URL','wss://outbreakweb.com/eth'),help='WSS URL used to select the default DNS test name')
    args=parser.parse_args()
    if not args.lan_interface: parser.error('Set OBWEB_LAN_INTERFACE or pass --lan-interface')
    if os.geteuid():parser.error('Run with sudo; keep the gateway running in another terminal')
    if not 5<=args.seconds<=120:parser.error('Use 5 to 120 seconds')
    counts=collections.Counter()
    addresses=json.loads(subprocess.run(['ip','-j','-4','address','show','dev',args.lan_interface],capture_output=True,text=True,check=True).stdout)
    scopes=[str(ipaddress.ip_network(f"{a['local']}/{a['prefixlen']}",strict=False)) for a in addresses[0]['addr_info'] if a['scope']=='global' and (not args.lan_ip or a['local']==args.lan_ip)]
    if len(scopes)!=1:parser.error('LAN interface has an ambiguous IPv4 subnet')
    client_scope=scopes[0]
    before=tap_counts();probe=None
    if args.test_dns and not before.get('available'):
        print('Gateway/TAP not found: wait for READY in the other terminal, then run diagnostics again.',flush=True)
        return
    if args.test_dns:
        print('Testing DNS through the tunnel, independently of client traffic...',flush=True)
        probe=asyncio.run(probe_remote_dns(str(args.test_dns),args.dns_name or urlsplit(args.url).hostname))
        print('WSS DNS test:',json.dumps(probe),flush=True)
    start=time.monotonic()
    print(f'Passive counters for {args.seconds}s. Try connecting now. No packets or DNS names are saved.',flush=True)
    with socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(3)) as sock:
        while (left:=args.seconds-(time.monotonic()-start))>0:
            if not select.select([sock],[],[],min(left,1))[0]:continue
            frame,info=sock.recvfrom(65535)
            if info[0] not in (args.lan_interface,'obw-host'):continue
            result=inspect(frame,client_scope,args.dns_name)
            if result:
                result['interface']=info[0];counts[json.dumps(result,sort_keys=True)]+=1
    print(json.dumps({'dns_wss_selftest':probe,'tap_before':before,'tap_after':tap_counts(),'traffic':[dict(json.loads(k),count=v) for k,v in counts.items()]},indent=2))


if __name__=='__main__':main()
