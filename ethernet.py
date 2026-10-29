#!/usr/bin/env python3
"""Dedicated local Ethernet endpoint to WSS; gateway.py remains the LAN gateway."""
import argparse
import asyncio
from datetime import datetime
import struct
import sys

from wire import ipv4, inbound, acquire_lease
from service import Reconnect, serve

URL = 'wss://outbreakweb.com/eth'
ORIGIN = 'https://outbreakweb.com'


def log(message):
    print(f'[{datetime.now().astimezone().isoformat(timespec="seconds")}] {message}', flush=True)


def dhcp_source(frame):
    """Learn the guest from its DHCP request, never from host background traffic."""
    parsed = ipv4(frame)
    if parsed is None:
        return None
    packet, header = parsed
    if packet[9] != 17 or int.from_bytes(packet[6:8], 'big') & 0x3fff:
        return None
    udp = packet[header:]
    if len(udp) < 248 or struct.unpack_from('!HH', udp) != (68, 67):
        return None
    body = udp[8:]
    if body[:3] != b'\x01\x01\x06' or body[236:240] != b'\x63\x82\x53\x63':
        return None
    return frame[6:12] if body[28:34] == frame[6:12] else None


async def relay(ws, adapter, state=None):
    state = state if state is not None else {}
    guest = state.get('mac')
    counts = dict(sent=0, received=0, ignored=0)

    async def transmit():
        nonlocal guest
        while True:
            try:
                frame = await asyncio.to_thread(adapter.read)
            except OSError:
                raise RuntimeError('Local Ethernet adapter read failed.') from None
            if frame is None:
                continue
            if not isinstance(frame, bytes) or not 14 <= len(frame) <= 65535:
                raise RuntimeError('Invalid local Ethernet frame')
            source = frame[6:12]
            if source == adapter.mac:
                counts['ignored'] += 1
                continue
            if guest is None or (source != guest and dhcp_source(frame) == source):
                guest = dhcp_source(frame)
                if guest is None:
                    counts['ignored'] += 1
                    continue
                state['mac'] = guest
                log('Guest DHCP detected; forwarding Ethernet frames directly to WSS.')
            if source != guest:
                counts['ignored'] += 1
                continue
            await ws.send(frame)
            counts['sent'] += 1

    async def receive():
        async for frame in ws:
            if not isinstance(frame, bytes) or not 14 <= len(frame) <= 65535:
                raise Reconnect('Invalid Ethernet frame from WSS')
            if guest is not None:
                frame = inbound(frame, guest)
            if guest is None or (frame[:6] != guest and not frame[0] & 1):
                counts['ignored'] += 1
                continue
            try:
                await asyncio.to_thread(adapter.write, frame)
            except OSError:
                raise RuntimeError('Local Ethernet adapter write failed.') from None
            counts['received'] += 1
        raise Reconnect('WebSocket closed by the server')

    async def status():
        while True:
            await asyncio.sleep(30)
            log(f'Ethernet: sent={counts["sent"]} received={counts["received"]} ignored={counts["ignored"]}')

    tasks = [asyncio.create_task(f()) for f in (transmit, receive, status)]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def run(adapter):
    from websockets.asyncio.client import connect
    from websockets.exceptions import WebSocketException
    state = {}
    connected_before = False

    async def session():
        nonlocal connected_before
        try:
            async with connect(URL, origin=ORIGIN, compression=None, proxy=None,
                               open_timeout=15, close_timeout=3, max_size=65535,
                               max_queue=32, ping_interval=20, ping_timeout=20) as ws:
                if connected_before:
                    # Never replay buffered game traffic after a transport loss.
                    try:
                        while await asyncio.to_thread(adapter.read) is not None:
                            pass
                    except OSError:
                        raise RuntimeError('Local Ethernet adapter read failed.') from None
                connected_before = True
                if state.get('mac'):
                    try:
                        await acquire_lease(ws, state['mac'])
                    except (RuntimeError, OSError) as exc:
                        raise Reconnect('Remote DHCP unavailable') from exc
                log(f'READY: PCSX2 Ethernet device = {adapter.name}; mode = PCAP Switched.')
                log('Disable DHCP interception. Use automatic DNS and an automatic in-game network profile.')
                log('The remote DHCP server assigns the guest IP, gateway and DNS. No manual PS2 IP is needed.')
                await relay(ws, adapter, state)
        except (WebSocketException, OSError) as exc:
            raise Reconnect('WSS transport interrupted') from exc

    await serve(session, log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adapter', help='Dedicated TAP-Windows adapter name (Windows only)')
    args = parser.parse_args()
    if sys.platform == 'linux':
        from ethernet_adapter import LinuxTap
        adapter = LinuxTap()
    elif sys.platform == 'win32':
        from ethernet_adapter import WindowsTap
        adapter = WindowsTap(args.adapter)
    else:
        parser.error('Local Ethernet mode supports Linux and Windows')
    try:
        with adapter:
            asyncio.run(run(adapter))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        # Only locally constructed errors are printed; remote text may contain secrets.
        log(str(exc) if isinstance(exc, RuntimeError) else f'Local Ethernet mode failed ({type(exc).__name__}).')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
