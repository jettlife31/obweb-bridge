"""Generate account cards for Outbreak and File #2 as part of login setup."""
import contextlib
import io
import os
from pathlib import Path
import re
import struct
import tempfile

from paths import ROOT
from third_party.mymc import ps2mc

ACCOUNT_DIRECTORY = b'/BASLUS-20765NET'
ACCOUNT_FILE = ACCOUNT_DIRECTORY + b'/BASLUS-20765NET'
ACCOUNT_OFFSET = 0xAF0
ACCOUNT_SIZE = 16
ASSETS = ROOT / 'assets' / 'outbreak-file1'
CARD_BYTES = 8650752  # 8 MiB data, 512-byte pages plus 16-byte ECC spare.


def account_data(name):
    if not re.fullmatch(r'[A-Za-z0-9]{1,15}', name):
        raise ValueError('Invalid memory-card account name')
    # Reconstruct the known initial network-save state; no user's save or
    # credential is included. The web runtime sets the same account field.
    data = bytearray(7548)
    data[ACCOUNT_OFFSET:ACCOUNT_OFFSET + ACCOUNT_SIZE] = name.encode('ascii').ljust(ACCOUNT_SIZE, b'\0')
    for offset, value in ((0xE0C, 0x10000), (0xE20, 1), (0xE24, 0x100)):
        struct.pack_into('<I', data, offset, value)
    data[0x1640:0x1644] = b'SCE\0'
    driver = b'Ethernet (Network Adaptor)\0'
    data[0x1740:0x1740 + len(driver)] = driver
    return bytes(data)


def card_bytes(name):
    files = {b'BASLUS-20765NET': account_data(name)}
    for filename in ('icon.sys', 'icon_20.ico', 'icon_21.ico', 'icon_22.ico'):
        files[filename.encode('ascii')] = (ASSETS / filename).read_bytes()
    buffer = io.BytesIO()
    card = ps2mc(buffer, False, (True, 512, 16, 16384))
    try:
        card.mkdir(ACCOUNT_DIRECTORY)
        for filename, data in files.items():
            path = ACCOUNT_DIRECTORY + b'/' + filename
            f = card.open(path, 'wb')
            try:
                f.write(data)
            finally:
                f.close()
            entry = card.get_dirent(path)
            entry[0] = 0x8497
            card.set_dirent(path, entry)
    finally:
        card.close()
    raw = buffer.getvalue()
    if len(raw) != CARD_BYTES:
        raise ValueError('Unexpected generated memory-card size')
    # Verify the generated file system and account before publishing the file.
    reader = ps2mc(io.BytesIO(raw))
    try:
        f = reader.open(ACCOUNT_FILE, 'rb')
        try:
            if f.read() != files[b'BASLUS-20765NET']:
                raise ValueError('Generated memory-card account verification failed')
        finally:
            f.close()
        with contextlib.redirect_stdout(io.StringIO()):
            valid = reader.check()
        if not valid:
            raise ValueError('Generated memory-card filesystem verification failed')
    finally:
        reader.close()
    return raw


def _existing_card(path):
    if path.is_symlink():
        raise ValueError('The generated memory-card path must not be a symbolic link')
    if not path.exists():
        return None, None
    if not path.is_file() or path.stat().st_size != CARD_BYTES:
        raise ValueError('An invalid memory-card file already exists; it was preserved. Move it before retrying.')
    raw = path.read_bytes()
    try:
        reader = ps2mc(io.BytesIO(raw))
    except Exception:
        raise ValueError('Could not read the existing memory card; it was preserved.') from None
    try:
        f = reader.open(ACCOUNT_FILE, 'rb')
        try:
            f.seek(ACCOUNT_OFFSET)
            account = f.read(ACCOUNT_SIZE).split(b'\0', 1)[0].decode('ascii')
        finally:
            f.close()
    except Exception:
        raise ValueError('Could not identify the existing card account; the card was preserved.') from None
    finally:
        reader.close()
    return raw, account


def ensure_account_card(name, directory, file_number=1):
    """Use fixed filenames, retain progress, and back up cards on account changes."""
    account_data(name)
    if file_number not in (1, 2):
        raise ValueError('Invalid Outbreak file number')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / f'outbreak-file{file_number}.ps2'
    previous, previous_account = _existing_card(target)
    if previous_account == name:
        return target.resolve(), False
    # Preserve the already-generated File #1 card when migrating the filename.
    legacy = directory / f'outbreak-file1-{name}.ps2'
    if file_number == 1 and legacy.exists():
        raw, legacy_account = _existing_card(legacy)
        if legacy_account != name:
            raise ValueError('The previous memory card belongs to another account; it was preserved.')
    else:
        raw = card_bytes(name)
    fd, temporary = tempfile.mkstemp(prefix='.account-card-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        if previous is None:
            # Exclusive publication prevents replacement by concurrent creators.
            os.link(temporary, target)
        else:
            backups = directory / 'backups'
            backups.mkdir(exist_ok=True, mode=0o700)
            backup_fd, backup_name = tempfile.mkstemp(prefix=target.stem + '-', suffix='.ps2', dir=backups)
            with os.fdopen(backup_fd, 'wb') as backup:
                backup.write(previous)
                backup.flush()
                os.fsync(backup.fileno())
            if target.is_symlink() or target.read_bytes() != previous:
                raise ValueError('The memory card changed during setup; stop the game before changing accounts. The previous snapshot was backed up.')
            os.replace(temporary, target)
        return target.resolve(), True
    finally:
        Path(temporary).unlink(missing_ok=True)


def ensure_account_cards(name, directory):
    # Both titles use the shared BASLUS-20765NET account directory.
    account_data(name)
    for number in (1, 2):
        _existing_card(Path(directory) / f'outbreak-file{number}.ps2')
    paths, created = [], False
    for number in (1, 2):
        path, new = ensure_account_card(name, directory, number)
        paths.append(path)
        created = created or new
    return paths, created


def existing_account_cards(name, directory):
    """List matching existing exports without creating or replacing anything."""
    account_data(name)
    paths = []
    for number in (1, 2):
        target = Path(directory) / f'outbreak-file{number}.ps2'
        try:
            _, account = _existing_card(target)
        except (OSError, ValueError):
            continue
        if account == name:
            paths.append(target.resolve())
    return paths
