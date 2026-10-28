#!/usr/bin/env python3
"""Outbreak Web gateway prototype, clients on the selected LAN. Default action is a read-only plan."""
import argparse
import asyncio
import ipaddress
import json
import os
import re
import secrets
import signal
import socket
import sys
from urllib.parse import urlsplit

from dns_proxy import DNSDatagrams, Resolver
from network import Network, cleanup_saved, inventory, host_rules, namespace_rules, namespace_socket
from wire import acquire_lease, inbound

WSS_URL = "wss://outbreakweb.com/eth"
WSS_ORIGIN = "https://outbreakweb.com"

def connection(url, origin=None):
    try:
        from websockets.asyncio.client import connect
    except ImportError:
        raise RuntimeError('Install requirements.txt in the virtual environment described in the README') from None
    return connect(url, origin=origin, compression=None, proxy=None,
                   open_timeout=15, close_timeout=3, max_size=65535, max_queue=32,
                   ping_interval=20, ping_timeout=20)


async def probe(url, origin):
    mac = b'\x02' + secrets.token_bytes(5)
    async with connection(url, origin) as ws:
        print('WebSocket connected; requesting a new DHCP lease.')
        lease = await acquire_lease(ws, mac)
        print(f'DHCP confirmed: IPv4={lease.address}/{lease.prefix}, gateway={lease.gateway}, DNS={lease.dns}; duration={lease.seconds}s.')
        print('This only verifies WebSocket/DHCP, not login or multiplayer.')


async def relay(ws, fd, mac, lease, stop, dns_resolver=None):
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue(maxsize=256)
    errors = loop.create_future()
    counts = {'sent': 0, 'received': 0, 'rejected': 0}

    def read_tap():
        try:
            packet = os.read(fd, 65536)
            if not 14 <= len(packet) <= 65535:
                raise RuntimeError('Invalid TAP frame')
            queue.put_nowait(packet)
        except BlockingIOError:
            pass
        except Exception as exc:
            if not errors.done():
                errors.set_exception(exc)
            loop.remove_reader(fd)

    async def transmit():
        while True:
            await ws.send(await queue.get())
            counts['sent'] += 1

    async def receive():
        async for packet in ws:
            packet = inbound(packet, mac, lease)
            if packet is None:
                counts['rejected'] += 1
                continue
            # Fail closed on TAP backpressure rather than allocate an unbounded queue.
            written = os.write(fd, packet)
            if written != len(packet):
                raise RuntimeError('Incomplete TAP write')
            counts['received'] += 1
        raise RuntimeError('WebSocket closed by the server')

    async def status():
        while True:
            await asyncio.sleep(30)
            print(f"Frames: sent={counts['sent']} received={counts['received']} dropped={counts['rejected']}" + (f" | DNS-WSS: {dns_resolver.counts}" if dns_resolver else ''), flush=True)

    async def expiry():
        # Renewal changes routing and needs more live evidence; never keep using an expired lease.
        await asyncio.sleep(lease.seconds * 0.9)
        raise RuntimeError('Lease is about to expire; restart the gateway and game session')

    loop.add_reader(fd, read_tap)
    tasks = [asyncio.create_task(f()) for f in [transmit, receive, status, expiry, stop.wait]]
    try:
        done, _ = await asyncio.wait([*tasks, errors], return_when=asyncio.FIRST_COMPLETED)
        for item in done:
            item.result()
    finally:
        loop.remove_reader(fd)
        for task in tasks:
            task.cancel()
        errors.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def run(c, url, origin):
    # No system proxy, credentials, captured cookies or raw session replay.
    mac = b'\x02' + secrets.token_bytes(5)
    network = Network(c)
    dns_udp, dns_tcp = None, None
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(signum, stop.set)
    try:
        resolver = Resolver(c['client_network'], namespace_socket)
        dns_udp, _ = await loop.create_datagram_endpoint(lambda: DNSDatagrams(resolver),
                                                        local_addr=(c['linux_ip'], 53))
        dns_tcp = await asyncio.start_server(resolver.tcp, c['linux_ip'], 53, limit=8192)
        network.setup(mac)
        # Ctrl+C must also cancel connection/DHCP establishment, before the relay starts.
        async def session():
            async with connection(url, origin) as ws:
                lease = await acquire_lease(ws, mac)
                network.activate(lease)
                resolver.servers = lease.dns
                print(f'Remote DHCP: IPv4={lease.address}/{lease.prefix}, gateway={lease.gateway}, DNS={lease.dns}', flush=True)
                print(f"READY: Client gateway/DNS = {c['linux_ip']}; client network = {c['client_network']}", flush=True)
                print(f'Virtual lease: {lease.seconds}s; preventive shutdown in {int(lease.seconds * .9)}s.', flush=True)
                await relay(ws, network.fd, mac, lease, stop, resolver)
        main = asyncio.create_task(session())
        stopping = asyncio.create_task(stop.wait())
        try:
            done, _ = await asyncio.wait([main, stopping], return_when=asyncio.FIRST_COMPLETED)
            if main in done:
                main.result()
        finally:
            main.cancel(); stopping.cancel()
            await asyncio.gather(main, stopping, return_exceptions=True)
    finally:
        if dns_udp:
            dns_udp.close()
        if dns_tcp:
            dns_tcp.close()
            await dns_tcp.wait_closed()
        network.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--run', action='store_true', help='Enable temporary networking; requires root')
    actions.add_argument('--probe', action='store_true', help='Test remote WSS/DHCP only, without root or network changes')
    actions.add_argument('--cleanup', action='store_true', help='Remove resources recorded from an interrupted run')
    parser.add_argument('--lan-interface', default=os.environ.get('OBWEB_LAN_INTERFACE'), help='Linux interface connected to the client network')
    parser.add_argument('--lan-ip', default=os.environ.get('OBWEB_LAN_IP'), help='Local IPv4 on that interface used as client gateway/DNS')
    parser.add_argument('--client-ip', default=os.environ.get('OBWEB_CLIENT_IP'), help='Optional: restrict to one client IPv4')
    parser.add_argument('--url', default=os.environ.get('OBWEB_WSS_URL', WSS_URL), help='WSS URL for Ethernet transport')
    parser.add_argument('--origin', default=os.environ.get('OBWEB_WSS_ORIGIN', WSS_ORIGIN), help='Origin required by the service')
    parser.add_argument('--show-rules', action='store_true', help='Include proposed rules in the plan; does not apply them')
    args = parser.parse_args()
    try:
        if args.cleanup:
            cleanup_saved()
            return 0
        if not args.url or urlsplit(args.url).scheme != 'wss' or not urlsplit(args.url).hostname:
            parser.error('invalid built-in WSS endpoint')
        if urlsplit(args.url).username or urlsplit(args.url).password:
            parser.error('do not put credentials in the URL')
        if args.probe:
            asyncio.run(probe(args.url, args.origin))
            return 0
        if not args.lan_interface:
            parser.error('provide --lan-interface; without --run, only show the plan')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,15}', args.lan_interface):
            parser.error('unsupported interface name; use a simple physical interface')
        client_ip = str(ipaddress.IPv4Address(args.client_ip)) if args.client_ip else None
        lan_ip = str(ipaddress.IPv4Address(args.lan_ip)) if args.lan_ip else None
        c = inventory(args.lan_interface, client_ip, lan_ip)
        if not args.run:
            print('PLAN — no configuration changed')
            print(json.dumps(c, ensure_ascii=False, indent=2))
            print('All IPv4 traffic routed from LAN clients goes through WSS, with no destination/protocol/port selection.')
            print('Remote DHCP provides IP/gateway/DNS; transit network is allocated automatically.')
            print('Set the client gateway and DNS to linux_ip.')
            print('Forwarding must be allowed by the existing firewall; its policies are not replaced.')
            if args.show_rules:
                print(host_rules(c)); print(namespace_rules(c))
            return 0
        asyncio.run(run(c, args.url, args.origin))
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        # External exception text can contain response bodies/headers. Never print those.
        if isinstance(exc, RuntimeError):
            print('Error:', str(exc), file=sys.stderr)
        else:
            print(f'Error ({type(exc).__name__}); no payload or remote headers were logged.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
