"""Revision-locked Outbreak DNAS patches; no external executable required."""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path


@dataclass(frozen=True)
class Game:
    title: str
    size: int
    original: str
    patched: str
    offsets: tuple


GAMES = (
    Game('Outbreak (USA v2.00)', 4698767360,
         '69ae2c48e6f01e2605659feabb54eb9b82c63a809bdc8a78ad2d160b3c59a4a1',
         '0a6b912d873cb262e991f359125e37dde4848864d905c888f822ed98cf9bc0c1',
         (0x4CFFC0, 0x4CFFD0)),
    Game('Outbreak File #2 (USA)', 4677795840,
         'bf33c7bcd727868abe6866d747a930c3c54bb7395ab8ebdfce1f7137641f6759',
         '6363263595ea0a4d12308b3c05e2a9c53cc92e96469c0509ee7952b97c09c970',
         (0x727890, 0x7278A0)),
)
REPLACEMENT = bytes.fromhex('000080a0010002240800e00300000000')
CHUNK = 8 * 1024 * 1024


class PatchError(Exception):
    pass


class Cancelled(PatchError):
    pass


def _check(cancel):
    if cancel is not None and cancel.is_set():
        raise Cancelled('Cancelled. The original ISO was preserved.')


def _digest(stream, size, progress, cancel, stage):
    stream.seek(0)
    digest = hashlib.sha256()
    done = 0
    while True:
        _check(cancel)
        block = stream.read(CHUNK)
        if not block:
            break
        digest.update(block)
        done += len(block)
        progress(stage, min(done / max(size, 1), 1))
    return digest.hexdigest()


def inspect_iso(path, progress=lambda stage, fraction: None, cancel=None):
    """Identify a supported original by its complete SHA-256, never its name."""
    with Path(path).open('rb') as stream:
        size = os.fstat(stream.fileno()).st_size
        if size not in {g.size for g in GAMES}:
            raise PatchError('Unsupported ISO size. Select an unmodified USA Outbreak v2.00 or File #2 ISO.')
        digest = _digest(stream, size, progress, cancel, 'Checking original ISO')
    for game in GAMES:
        if digest == game.patched:
            raise PatchError('This ISO already has the Outbreak Web patch. No changes are needed.')
        if size == game.size and digest == game.original:
            return game
    raise PatchError('SHA-256 does not match a supported original ISO. No patch was applied.')


def apply_patch(source, destination, game, progress=lambda stage, fraction: None, cancel=None):
    """Revalidate input, copy with two replacements, and verify the saved result."""
    if game not in GAMES:
        raise PatchError('Unsupported game revision.')
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise PatchError('Choose a different output file. The original ISO must be preserved.')
    created = False
    owned = None
    try:
        with source.open('rb') as original:
            size = os.fstat(original.fileno()).st_size
            if size != game.size or _digest(original, size, progress, cancel, 'Rechecking original ISO') != game.original:
                raise PatchError('The original ISO changed or its SHA-256 does not match. No patch was applied.')
            _check(cancel)
            # Exclusive creation also protects an existing output or symlink.
            with destination.open('x+b') as output:
                created = True
                owned = os.fstat(output.fileno())
                original.seek(0)
                original_hash = hashlib.sha256()
                position = 0
                while True:
                    _check(cancel)
                    block = original.read(CHUNK)
                    if not block:
                        break
                    original_hash.update(block)
                    modified = bytearray(block)
                    for offset in game.offsets:
                        lo = max(offset, position)
                        hi = min(offset + len(REPLACEMENT), position + len(block))
                        if lo < hi:
                            modified[lo-position:hi-position] = REPLACEMENT[lo-offset:hi-offset]
                    output.write(modified)
                    position += len(block)
                    progress('Writing patched copy', min(position / size, 1))
                if position != size or original_hash.hexdigest() != game.original:
                    raise PatchError('The source changed while copying. The incomplete output was removed.')
                output.flush()
                os.fsync(output.fileno())
                if _digest(output, size, progress, cancel, 'Verifying patched ISO') != game.patched:
                    raise PatchError('The patched ISO failed SHA-256 verification. The output was removed.')
                _check(cancel)
    except BaseException:
        if created:
            try:
                if os.path.samestat(destination.stat(), owned):
                    destination.unlink()
            except FileNotFoundError:
                pass
        raise
    return destination
