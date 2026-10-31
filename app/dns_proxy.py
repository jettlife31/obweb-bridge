"""Generic DNS relay using sockets created in the WSS-side network namespace."""
import asyncio
import ipaddress
import socket
import struct


class Resolver:
    def __init__(self, allowed, socket_factory):
        if allowed is None:
            self.allowed = ()
        elif isinstance(allowed, (str, ipaddress.IPv4Network, ipaddress.IPv6Network)):
            self.allowed = (ipaddress.ip_network(allowed, strict=False),)
        else:
            self.allowed = tuple(ipaddress.ip_network(network, strict=False) for network in allowed)
        self.socket_factory = socket_factory
        self.servers = ()  # Supplied only by remote DHCP, never a public fallback.
        self.counts = {'queries': 0, 'answers': 0, 'errors': 0}

    def accepts(self, address):
        ip = ipaddress.ip_address(address)
        return any(ip in network for network in self.allowed)

    async def resolve(self, data, tcp=False):
        if len(data) < 12 or data[2] & 128:
            raise ValueError('Not a DNS query')
        self.counts['queries'] += 1
        loop = asyncio.get_running_loop()
        for server in self.servers:
            sock = self.socket_factory(socket.SOCK_STREAM if tcp else socket.SOCK_DGRAM)
            try:
                await asyncio.wait_for(loop.sock_connect(sock, (server, 53)), 3)
                if tcp:
                    await asyncio.wait_for(loop.sock_sendall(sock, struct.pack('!H', len(data)) + data), 3)
                    async def exact(n):
                        result = bytearray()
                        while len(result) < n:
                            part = await loop.sock_recv(sock, n - len(result))
                            if not part: raise OSError('DNS TCP closed')
                            result.extend(part)
                        return bytes(result)
                    size = int.from_bytes(await asyncio.wait_for(exact(2), 3), 'big')
                    response = await asyncio.wait_for(exact(size), 3)
                else:
                    await loop.sock_sendall(sock, data)
                    response = await asyncio.wait_for(loop.sock_recv(sock, 65535), 3)
                if len(response) < 12 or response[:2] != data[:2] or not response[2] & 128:
                    raise ValueError('Invalid upstream response')
                self.counts['answers'] += 1
                return response  # No domain parsing, answer rewriting or local records.
            except (ValueError, OSError, asyncio.TimeoutError):
                continue
            finally:
                sock.close()
        self.counts['errors'] += 1
        # A failed transport never tries the host resolver or invents a DNS record.
        raise OSError('No remote DHCP DNS responded through WSS')

    async def tcp(self, reader, writer):
        try:
            if not self.accepts(writer.get_extra_info('peername')[0]): return
            while True:
                size = int.from_bytes(await asyncio.wait_for(reader.readexactly(2), 5), 'big')
                if size < 12: return
                data = await asyncio.wait_for(reader.readexactly(size), 5)
                response = await self.resolve(data, tcp=True)
                writer.write(struct.pack('!H', len(response)) + response)
                await writer.drain()
        except (ValueError, OSError, asyncio.TimeoutError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()


class DNSDatagrams(asyncio.DatagramProtocol):
    def __init__(self, resolver):
        self.resolver, self.pending = resolver, set()

    def connection_made(self, transport): self.transport = transport

    def datagram_received(self, data, addr):
        if not self.resolver.accepts(addr[0]) or len(data) < 12 or len(self.pending) >= 32: return
        task = asyncio.create_task(self.answer(data, addr))
        self.pending.add(task); task.add_done_callback(self.pending.discard)

    async def answer(self, data, addr):
        try: self.transport.sendto(await self.resolver.resolve(data), addr)
        except (ValueError, OSError, asyncio.TimeoutError): pass

    def connection_lost(self, exc):
        for task in list(self.pending): task.cancel()
