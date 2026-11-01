"""Small length-delimited JSON channel for a local, elevated network worker.

No pickle, shell commands, account credentials or remote packet data are sent.
"""
import json
import struct
import select
import threading

LIMIT = 65536


class Channel:
    def __init__(self, sock):
        self.sock = sock
        self.lock = threading.Lock()
        self.buffer = bytearray()

    def send(self, message):
        data = json.dumps(message, ensure_ascii=True).encode('ascii')
        if len(data) > LIMIT:
            raise ValueError('Local control message too large')
        with self.lock:
            self.sock.sendall(struct.pack('!I', len(data)) + data)

    def _message(self):
        if len(self.buffer) < 4:
            return None
        count = struct.unpack('!I', self.buffer[:4])[0]
        if not 0 < count <= LIMIT:
            raise ValueError('Invalid local control message length')
        if len(self.buffer) < count + 4:
            return None
        data = bytes(self.buffer[4:count + 4])
        del self.buffer[:count + 4]
        value = json.loads(data)
        if not isinstance(value, dict) or not isinstance(value.get('type'), str):
            raise ValueError('Invalid local control message')
        return value

    def _receive_chunk(self):
        chunk = self.sock.recv(LIMIT + 4)
        if not chunk:
            raise EOFError('Local control connection closed')
        self.buffer.extend(chunk)

    def receive(self):
        while True:
            message = self._message()
            if message is not None:
                return message
            self._receive_chunk()

    def poll_message(self, timeout=0):
        """A single reader can poll without losing a partial length/body.

        Used by the worker progress monitor, so it can keep reporting health
        even when a command arrives split across TCP receives.
        """
        message = self._message()
        if message is not None:
            return message
        if not select.select([self.sock], [], [], timeout)[0]:
            return None
        self._receive_chunk()
        return self._message()

    def finish_sending(self):
        """Keep receiving cleanup reports, but guarantee EOF at the peer."""
        import socket
        with self.lock:
            self.sock.shutdown(socket.SHUT_WR)

    def close(self):
        import socket
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()
