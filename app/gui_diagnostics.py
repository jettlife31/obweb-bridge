"""Local worker progress. No packet contents, account data or frame locals."""
import asyncio
import hashlib
import os
from pathlib import Path
import sys
import threading
import time

from paths import APP_DIR

PHASES = {
    'starting': 'Starting the network worker',
    'opening_adapter': 'Opening the Ethernet adapter',
    'starting_network': 'Starting the network session',
    'running': 'Network session running',
    'stop_received': 'Stop received; cancelling network tasks',
    'cancelling_io': 'Cancelling Ethernet driver I/O',
    'closing_session': 'Closing the network session',
    'releasing_adapter': 'Releasing the Ethernet adapter',
    'driver_ack': 'Waiting for the TAP driver to acknowledge cancellation',
    'removing_adapter': 'Removing the temporary TAP adapter',
    'complete': 'Network cleanup complete',
}


def code_id():
    digest = hashlib.sha256()
    for name in ('gui.py', 'gui_backend.py', 'gui_worker.py', 'gui_transport.py',
                 'gui_diagnostics.py', 'ethernet.py', 'ethernet_adapter.py'):
        try:
            digest.update(name.encode('ascii'))
            digest.update((APP_DIR / name).read_bytes())
        except OSError:
            return 'unavailable'
    return digest.hexdigest()[:12]


def thread_locations():
    """Only application basenames/function names/line numbers, never locals."""
    frames = sys._current_frames()
    result = []
    for index, thread in enumerate(threading.enumerate()[:12], 1):
        frame = frames.get(thread.ident)
        locations = []
        while frame is not None:
            filename = frame.f_code.co_filename
            if filename.startswith(str(APP_DIR) + os.sep):
                locations.append(f'{Path(filename).name}:{frame.f_lineno}:{frame.f_code.co_name}')
            frame = frame.f_back
        if locations:
            result.append(f'thread {index}: ' + ' <- '.join(locations[:5]))
    return result


class WorkerProgress:
    def __init__(self, channel, stopped):
        self.channel, self.stopped = channel, stopped
        self.done = threading.Event()
        self.lock = threading.Lock()
        self.phase = 'starting'
        self.tick = None
        self.tasks = []
        self.stop_callback = None
        self.stop_at = None
        self.code = code_id()
        self.thread = None

    def set_phase(self, phase):
        if phase not in PHASES:
            return
        with self.lock:
            self.phase = phase

    def observe_line(self, line):
        pairs = (('READY:', 'running'),
                 ('Cancelling local Ethernet I/O', 'cancelling_io'),
                 ('Ethernet network threads stopped', 'releasing_adapter'),
                 ('Waiting for the Windows TAP driver', 'driver_ack'),
                 ('Removing the temporary Windows TAP', 'removing_adapter'),
                 ('Ethernet adapter cleanup complete', 'complete'))
        for marker, phase in pairs:
            if marker in line:
                if phase == 'running' and self.stopped.is_set():
                    return
                self.set_phase(phase)
                break

    def register_stop(self, callback):
        with self.lock:
            self.stop_callback = callback
        if self.stopped.is_set():
            callback()

    def request_stop(self, reason):
        self.stopped.set()
        with self.lock:
            first = self.stop_at is None
            if first:
                self.stop_at = time.monotonic()
                self.phase = 'stop_received'
            callback = self.stop_callback
        if first:
            try:
                self.channel.send({'type': 'stop_ack', 'reason': reason})
            except OSError:
                pass
        if callback is not None:
            self.set_phase('cancelling_io')
            callback()

    def pulse(self):
        locations = []
        for index, task in enumerate(list(asyncio.all_tasks())[:20], 1):
            for frame in task.get_stack(limit=1):
                filename = frame.f_code.co_filename
                if filename.startswith(str(APP_DIR) + os.sep):
                    locations.append(f'task {index}: {Path(filename).name}:{frame.f_lineno}:{frame.f_code.co_name}')
        with self.lock:
            self.tick = time.monotonic()
            self.tasks = locations

    def snapshot(self):
        now = time.monotonic()
        with self.lock:
            message = {'type': 'progress', 'phase': self.phase,
                       'loop_age': None if self.tick is None else round(now - self.tick, 1),
                       'pid': os.getpid(), 'code': self.code}
            stopped_long = self.stop_at is not None and now - self.stop_at >= 5
            tasks = list(self.tasks)
        if stopped_long:
            message['threads'] = [*thread_locations(), *tasks][:24]
        return message

    def start(self):
        def monitor():
            while not self.done.wait(1):
                try:
                    self.channel.send(self.snapshot())
                    # Cover an I/O issuance racing the first cancellation. This
                    # runs independently of the network event loop, only on Stop.
                    with self.lock:
                        callback = self.stop_callback if self.stopped.is_set() else None
                    if callback:
                        callback()
                except (OSError, ValueError):
                    return
        self.thread = threading.Thread(target=monitor, name='worker-progress', daemon=True)
        self.thread.start()

    def close(self):
        self.done.set()
        if self.thread:
            self.thread.join(timeout=2)
