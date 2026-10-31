"""Experimental native Windows LAN endpoint: Npcap + WinDivert + Ethernet WSS."""
import asyncio
from datetime import datetime
import ipaddress
import secrets
import socket
import struct
import threading

from service import Reconnect, serve
from wire import acquire_lease, dhcp_reply, ipv4
from windows_packets import classify, translate

URL = 'wss://outbreakweb.com/eth'
ORIGIN = 'https://outbreakweb.com'


def log(message):
    print(f'[{datetime.now().astimezone().isoformat(timespec="seconds")}] {message}', flush=True)


def connection():
    from websockets.asyncio.client import connect
    return connect(URL, origin=ORIGIN, compression=None, proxy=None,
                   open_timeout=15, close_timeout=3, max_size=65535, max_queue=32,
                   ping_interval=20, ping_timeout=20)


def arp(mac, lease, target_mac=bytes(6), *, reply=False):
    destination = target_mac if reply else b'\xff' * 6
    return (destination + mac + b'\x08\x06' + struct.pack('!HHBBH', 1, 0x800, 6, 4, 2 if reply else 1)
            + mac + socket.inet_aton(lease.address) + target_mac + socket.inet_aton(lease.gateway))


def arp_fields(frame):
    if len(frame) < 42 or frame[12:14] != b'\x08\x06' or frame[14:20] != b'\x00\x01\x08\x00\x06\x04':
        return None
    if frame[22:28] != frame[6:12] or frame[6] & 1 or frame[6:12] == bytes(6):
        return None
    return int.from_bytes(frame[20:22], 'big'), frame[22:28], socket.inet_ntoa(frame[28:32]), socket.inet_ntoa(frame[38:42])


async def resolve_gateway(ws, mac, lease):
    loop = asyncio.get_running_loop()
    for _ in range(3):
        await ws.send(arp(mac, lease))
        deadline = loop.time() + 2
        while deadline > loop.time():
            try:
                frame = await asyncio.wait_for(ws.recv(), deadline - loop.time())
            except asyncio.TimeoutError:
                break
            if not isinstance(frame, bytes):
                continue
            fields = arp_fields(frame)
            if fields and fields[0] == 2 and fields[2:] == (lease.gateway, lease.address) and frame[:6] == mac:
                return fields[1]
    raise Reconnect('Remote gateway ARP did not respond')


class Renewal:
    def __init__(self, ws, mac):
        self.ws, self.mac = ws, mac
        self.xid = None
        self.queue = asyncio.Queue(maxsize=8)

    async def send(self, frame):
        self.xid = int.from_bytes(frame[46:50], 'big')
        await self.ws.send(frame)

    async def recv(self):
        return await self.queue.get()

    def accept(self, frame):
        if self.xid is None or not isinstance(frame, bytes) or dhcp_reply(frame, self.mac, self.xid) is None:
            return False
        try:
            self.queue.put_nowait(frame)
        except asyncio.QueueFull:
            pass
        return True

    async def maintain(self, lease):
        loop = asyncio.get_running_loop()
        deadline = loop.time() + lease.seconds
        while True:
            await asyncio.sleep(lease.seconds * .5)
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise Reconnect('Remote DHCP lease expired')
                try:
                    renewed = await asyncio.wait_for(acquire_lease(self, self.mac, timeout=min(8, remaining / 4), attempts=1), remaining)
                except (OSError, asyncio.TimeoutError, RuntimeError) as error:
                    if isinstance(error, RuntimeError) and str(error) == 'DHCP rejected by the tunnel':
                        raise Reconnect('Remote DHCP rejected renewal') from None
                    remaining = deadline - loop.time()
                    if remaining > 0:
                        await asyncio.sleep(min(30, remaining / 2))
                    continue
                finally:
                    self.xid = None
                    while not self.queue.empty():
                        self.queue.get_nowait()
                # DNS/address changes require a fresh translation session.
                if (renewed.address, renewed.gateway, renewed.prefix, renewed.dns) != (lease.address, lease.gateway, lease.prefix, lease.dns):
                    raise Reconnect('Remote DHCP configuration changed')
                lease = renewed
                deadline = loop.time() + lease.seconds
                log('Remote DHCP lease renewed; native LAN session continues.')
                break


class ClientTunnel:
    """One isolated remote lease per client and path; no shared NAT port space."""
    def __init__(self, client, dns, plan, adapter, counts):
        self.client, self.dns, self.plan, self.adapter, self.counts = client, dns, plan, adapter, counts
        self.queue = asyncio.Queue(maxsize=128)
        self.mac = b'\x02' + secrets.token_bytes(5)
        self.client_mac = None
        self.connected_before = False

    def enqueue(self, mac, packet):
        self.client_mac = mac
        try:
            self.queue.put_nowait(packet)
        except asyncio.QueueFull:
            self.counts['dropped'] += 1

    async def session(self):
        from websockets.exceptions import WebSocketException
        try:
            async with connection() as ws:
                try:
                    lease = await acquire_lease(ws, self.mac)
                    gateway_mac = await resolve_gateway(ws, self.mac, lease)
                except (RuntimeError, OSError) as error:
                    raise Reconnect('Remote network setup unavailable') from error
                if ipaddress.IPv4Address(lease.address) in ipaddress.IPv4Network(self.plan['client_network']):
                    raise RuntimeError('Remote DHCP overlaps the selected client LAN; use a different LAN subnet.')
                # The first discovery packets are retained while DHCP starts;
                # after a disconnect, buffered game packets are never replayed.
                if self.connected_before:
                    while not self.queue.empty():
                        self.queue.get_nowait()
                self.connected_before = True
                renewal = Renewal(ws, self.mac)

                async def transmit():
                    while True:
                        packet = await self.queue.get()
                        try:
                            packet = translate(packet, source=lease.address,
                                               destination=lease.dns[0] if self.dns else None)
                        except ValueError:
                            self.counts['dropped'] += 1
                            continue
                        await ws.send(gateway_mac + self.mac + b'\x08\x00' + packet)
                        self.counts['sent'] += 1

                async def receive():
                    async for frame in ws:
                        if not isinstance(frame, bytes):
                            continue
                        if renewal.accept(frame):
                            continue
                        fields = arp_fields(frame)
                        if fields and fields[0] == 1 and fields[3] == lease.address:
                            # Answer the actual request sender, not a fixed peer.
                            response = (fields[1] + self.mac + b'\x08\x06' + struct.pack('!HHBBH', 1, 0x800, 6, 4, 2)
                                        + self.mac + socket.inet_aton(lease.address) + fields[1] + socket.inet_aton(fields[2]))
                            await ws.send(response)
                            continue
                        parsed = ipv4(frame)
                        if parsed is None or frame[:6] not in (self.mac, bytes(6)):
                            continue
                        packet, _ = parsed
                        if packet[16:20] != socket.inet_aton(lease.address) or self.client_mac is None:
                            continue
                        resolver = socket.inet_aton(lease.dns[0])
                        if self.dns and packet[12:16] != resolver:
                            continue
                        quoted = {lease.address: self.client}
                        if self.dns:
                            quoted[lease.dns[0]] = self.plan['lan_ip']
                        try:
                            packet = translate(packet, source=self.plan['lan_ip'] if self.dns else None,
                                               destination=self.client, quoted=quoted)
                        except ValueError:
                            self.counts['dropped'] += 1
                            continue
                        self.adapter.write(self.client_mac + self.plan['mac'] + b'\x08\x00' + packet)
                        self.counts['received'] += 1
                    raise Reconnect('WebSocket closed by the server')

                tasks = [asyncio.create_task(coro) for coro in (transmit(), receive(), renewal.maintain(lease))]
                try:
                    done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        task.result()
                finally:
                    for task in tasks:
                        task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
        except (WebSocketException, OSError) as error:
            raise Reconnect('WSS transport interrupted') from error

    async def run(self):
        await serve(self.session, log)


async def relay(adapter, guards, plan):
    loop = asyncio.get_running_loop()
    packets = asyncio.Queue(maxsize=512)
    stopped = threading.Event()
    failure = loop.create_future()
    pending = threading.BoundedSemaphore(512)
    counts = dict(sent=0, received=0, dropped=0)
    clients, tasks = {}, {}

    def put(frame):
        try:
            packets.put_nowait(frame)
        except asyncio.QueueFull:
            counts['dropped'] += 1
        finally:
            pending.release()

    def failed():
        if not failure.done():
            failure.set_exception(RuntimeError('Npcap LAN receive failed.'))

    def reader():
        try:
            while not stopped.is_set():
                frame = adapter.read()
                if frame is None:
                    stopped.wait(.01)
                elif pending.acquire(timeout=.05):
                    loop.call_soon_threadsafe(put, frame)
        except Exception:
            loop.call_soon_threadsafe(failed)
    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    async def dispatch():
        while True:
            frame = await packets.get()
            value = classify(frame, plan)
            if value is None:
                continue
            client, mac, dns, packet = value
            key = client, dns
            if key not in clients:
                # Resource ceiling, never a duration/idle shutdown. Multiple
                # devices stay available until the user stops the application.
                if client not in {k[0] for k in clients} and len({k[0] for k in clients}) >= 32:
                    counts['dropped'] += 1
                    continue
                log('Client DNS traffic detected; preparing its remote session.' if dns else 'Client forwarded traffic detected; preparing its remote session.')
                tunnel = clients[key] = ClientTunnel(client, dns, plan, adapter, counts)
                task = tasks[key] = asyncio.create_task(tunnel.run())
                def completed(task):
                    if not task.cancelled() and task.exception() is not None and not failure.done():
                        failure.set_exception(task.exception())
                task.add_done_callback(completed)
            clients[key].enqueue(mac, packet)

    async def status():
        while True:
            if guards.error:
                raise guards.error
            await asyncio.sleep(1)

    async def counters():
        while True:
            await asyncio.sleep(30)
            log(f'Native LAN: clients={len({k[0] for k in clients})} sent={counts["sent"]} received={counts["received"]} dropped={counts["dropped"]}')

    main = [asyncio.create_task(coro) for coro in (dispatch(), status(), counters())]
    try:
        done, _ = await asyncio.wait([*main, failure], return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    finally:
        stopped.set()
        await asyncio.to_thread(thread.join)
        for task in [*main, *tasks.values()]:
            task.cancel()
        await asyncio.gather(*main, *tasks.values(), return_exceptions=True)
        if not failure.done():
            failure.cancel()
        elif not failure.cancelled():
            failure.exception()


async def run(plan):
    from windows_lan import Npcap, WindowsGuards
    # Open and validate dependencies before advertising availability. These
    # handles add no routes, DNS settings, adapters or persistent firewall rules.
    with Npcap(plan) as adapter, WindowsGuards(plan) as guards:
        log(f'READY: Native Windows LAN endpoint; client gateway/DNS = {plan["lan_ip"]}.')
        log('Experimental: local capture is ready. Client/WSS data path is confirmed only when counters increase.')
        await relay(adapter, guards, plan)
