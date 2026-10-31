#!/usr/bin/env python3
"""Outbreak Web gateway prototype, clients on the selected LAN. Default action is a read-only plan."""
import argparse
import asyncio
from datetime import datetime
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
from network import (Network, cleanup_saved, inventory, host_rules, namespace_rules,
                     namespace_socket)
from wire import acquire_lease, dhcp_reply, inbound
from service import Reconnect, serve

WSS_URL = "wss://outbreakweb.com/eth"
WSS_ORIGIN = "https://outbreakweb.com"

def log(message, *, file=sys.stdout, flush=True):
    timestamp = datetime.now().astimezone().isoformat(timespec='seconds')
    print(f'[{timestamp}] {message}', file=file, flush=flush)


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
        log('WebSocket connected; requesting a new DHCP lease.')
        lease = await acquire_lease(ws, mac)
        log(f'DHCP confirmed: IPv4={lease.address}/{lease.prefix}, gateway={lease.gateway}, DNS={lease.dns}; duration={lease.seconds}s.')
        log('This only verifies WebSocket/DHCP, not login or multiplayer.')


class DHCPRenewal:
    """Demultiplex only our pending DHCP transaction from the shared WSS receiver."""
    def __init__(self, ws, mac):
        self.ws, self.mac = ws, mac
        self.xid = None
        self.responses = asyncio.Queue(maxsize=8)

    async def send(self, packet):
        self.xid = int.from_bytes(packet[46:50], 'big')
        await self.ws.send(packet)

    async def recv(self):
        return await self.responses.get()

    def accept(self, packet):
        if self.xid is None or not isinstance(packet, bytes):
            return False
        if dhcp_reply(packet, self.mac, self.xid) is None:
            return False
        try:
            self.responses.put_nowait(packet)
        except asyncio.QueueFull:
            pass
        return True

    async def maintain(self, lease, resolver=None):
        loop = asyncio.get_running_loop()
        deadline = loop.time() + lease.seconds
        while True:
            await asyncio.sleep(lease.seconds * .5)
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise Reconnect('Remote DHCP lease expired')
                try:
                    renewed = await asyncio.wait_for(
                        acquire_lease(self, self.mac, timeout=min(8, remaining / 4), attempts=1), remaining)
                except (OSError, asyncio.TimeoutError, RuntimeError) as exc:
                    if isinstance(exc, RuntimeError) and str(exc) == 'DHCP rejected by the tunnel':
                        raise Reconnect('Remote DHCP rejected renewal') from None
                    remaining = deadline - loop.time()
                    if remaining > 0:
                        log('Remote DHCP renewal did not respond; retrying within the current lease.')
                        await asyncio.sleep(min(30, remaining / 2))
                    continue
                finally:
                    self.xid = None
                    while not self.responses.empty():
                        self.responses.get_nowait()
                if (renewed.address, renewed.prefix, renewed.gateway) != (lease.address, lease.prefix, lease.gateway):
                    raise Reconnect('Remote DHCP changed the tunnel network')
                lease = renewed
                if resolver is not None:
                    resolver.servers = lease.dns
                deadline = loop.time() + lease.seconds
                log(f'Remote DHCP lease renewed for {lease.seconds}s; session continues.')
                break


async def relay(ws, fd, mac, lease, stop, dns_resolver=None):
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue(maxsize=256)
    errors = loop.create_future()
    counts = {'sent': 0, 'received': 0, 'rejected': 0}
    renewal = DHCPRenewal(ws, mac)

    def read_tap():
        try:
            packet = os.read(fd, 65536)
            if not 14 <= len(packet) <= 65535:
                raise RuntimeError('Invalid TAP frame')
            queue.put_nowait(packet)
        except BlockingIOError:
            pass
        except OSError:
            if not errors.done():
                errors.set_exception(RuntimeError('Local TAP read failed.'))
            loop.remove_reader(fd)
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
            if renewal.accept(packet):
                continue
            packet = inbound(packet, mac, lease)
            if packet is None:
                counts['rejected'] += 1
                continue
            # Fail closed on TAP backpressure rather than allocate an unbounded queue.
            try:
                written = os.write(fd, packet)
            except OSError:
                raise RuntimeError('Local TAP write failed.') from None
            if written != len(packet):
                raise RuntimeError('Incomplete TAP write')
            counts['received'] += 1
        raise Reconnect('WebSocket closed by the server')

    async def status():
        while True:
            await asyncio.sleep(30)
            log(f"Frames: sent={counts['sent']} received={counts['received']} dropped={counts['rejected']}" + (f" | DNS-WSS: {dns_resolver.counts}" if dns_resolver else ''))

    loop.add_reader(fd, read_tap)
    tasks = [asyncio.create_task(f()) for f in [transmit, receive, status, stop.wait]]
    tasks.append(asyncio.create_task(renewal.maintain(lease, dns_resolver)))
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
        try:
            network.setup(mac)
        except OSError as exc:
            raise RuntimeError(f'Local network setup failed (OS error {exc.errno}: {exc.strerror})') from None

        resolver = Resolver(c['client_network'], namespace_socket)
        try:
            dns_udp, _ = await loop.create_datagram_endpoint(lambda: DNSDatagrams(resolver),
                                                            local_addr=(c['linux_ip'], 53))
        except OSError as exc:
            raise RuntimeError(f'Could not bind the UDP DNS listener on the selected LAN address (OS error {exc.errno}: {exc.strerror})') from None
        try:
            dns_tcp = await asyncio.start_server(resolver.tcp, c['linux_ip'], 53, limit=8192)
        except OSError as exc:
            raise RuntimeError(f'Could not bind the TCP DNS listener on the selected LAN address (OS error {exc.errno}: {exc.strerror})') from None
        # Ctrl+C must also cancel connection/DHCP establishment, before the relay starts.
        from websockets.exceptions import WebSocketException
        activated = False

        async def session():
            nonlocal activated
            try:
                async with connection(url, origin) as ws:
                    try:
                        lease = await acquire_lease(ws, mac)
                    except (OSError, RuntimeError) as exc:
                        raise Reconnect('Remote DHCP unavailable') from exc
                    try:
                        network.validate_lease(lease)
                    except RuntimeError as exc:
                        raise Reconnect('Remote DHCP network conflicts with local routing') from exc
                    # Drop old queued frames: transport reconnection must not
                    # replay packets from a disconnected game session.
                    while True:
                        try:
                            os.read(network.fd, 65536)
                        except BlockingIOError:
                            break
                    if activated:
                        network.configure_tunnel(lease)
                    else:
                        network.activate(lease)
                        activated = True
                    resolver.servers = lease.dns
                    log(f'Remote DHCP: IPv4={lease.address}/{lease.prefix}, gateway={lease.gateway}, DNS={lease.dns}')
                    log(f"READY: Client gateway/DNS = {c['linux_ip']}; client network = {c['client_network']}")
                    log(f'Virtual lease: {lease.seconds}s; automatic DHCP renewal enabled.')
                    await relay(ws, network.fd, mac, lease, stop, resolver)
            except (WebSocketException, OSError) as exc:
                raise Reconnect('WSS transport interrupted') from exc
            finally:
                resolver.servers = ()
                network.suspend()

        main = asyncio.create_task(serve(session, log))
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
    parser.add_argument('--lan-interface', help='Linux interface connected to the client network')
    parser.add_argument('--lan-ip', help='Local IPv4 on that interface used as client gateway/DNS')
    parser.add_argument('--client-ip', help='Optional: restrict to one client IPv4')
    parser.add_argument('--transit-network', help=argparse.SUPPRESS)
    parser.add_argument('--route-table', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--url', default=WSS_URL, help='WSS URL for Ethernet transport')
    parser.add_argument('--origin', default=WSS_ORIGIN, help='Origin required by the service')
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
        c = inventory(args.lan_interface, client_ip, lan_ip, args.transit_network, args.route_table)
        if not args.run:
            print('PLAN — no configuration changed')
            print(json.dumps(c, ensure_ascii=False, indent=2))
            print('All IPv4 traffic routed from LAN clients goes through WSS, with no destination/protocol/port selection.')
            print('Remote DHCP provides IP/gateway/DNS; transit network is allocated automatically.')
            print('Set the client gateway and DNS to linux_ip.')
            print('For PCSX2 on this computer, use start-ethernet.sh instead of this LAN gateway.')
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
            log('Error: ' + str(exc), file=sys.stderr)
        else:
            log(f'Error ({type(exc).__name__}); no payload or remote headers were logged.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
