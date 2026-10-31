"""Small length-delimited JSON channel for a local, elevated network worker.

No pickle, shell commands, account credentials or remote packet data are sent.
"""
import json
import struct
import threading

LIMIT = 65536


class Channel:
    def __init__(self, sock):
        self.sock = sock
        self.lock = threading.Lock()

    def send(self, message):
        data = json.dumps(message, ensure_ascii=True).encode('ascii')
        if len(data) > LIMIT:
            raise ValueError('Local control message too large')
        with self.lock:
            self.sock.sendall(struct.pack('!I', len(data)) + data)

    def _read(self, count):
        data = bytearray()
        while len(data) < count:
            chunk = self.sock.recv(count - len(data))
            if not chunk:
                raise EOFError('Local control connection closed')
            data.extend(chunk)
        return bytes(data)

    def receive(self):
        count = struct.unpack('!I', self._read(4))[0]
        if not 0 < count <= LIMIT:
            raise ValueError('Invalid local control message length')
        value = json.loads(self._read(count))
        if not isinstance(value, dict) or not isinstance(value.get('type'), str):
            raise ValueError('Invalid local control message')
        return value

    def close(self):
        import socket
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()
