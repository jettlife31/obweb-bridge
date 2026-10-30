"""WSL discovery and argument-only launch commands for the Windows desktop UI."""
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def decode(data):
    if isinstance(data, str):
        return data
    # wsl.exe inventory is commonly UTF-16LE; Linux command output is UTF-8.
    encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else ('utf-16-le' if b'\0' in data else 'utf-8-sig')
    return data.decode(encoding, errors='replace').strip()


def executable():
    path = shutil.which('wsl.exe')
    if not path:
        raise RuntimeError('WSL was not found. Install WSL 2 and a Linux distribution, then refresh. See the LAN guide.')
    return path


def distro_name(name):
    if not isinstance(name, str) or not name.strip() or len(name) > 128 or name.startswith('-') or any(ord(c) < 32 for c in name):
        raise RuntimeError('Select a valid WSL distribution.')
    return name


def run(arguments, timeout=30):
    try:
        result = subprocess.run([executable(), *arguments], capture_output=True, timeout=timeout,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        raise RuntimeError('WSL did not respond in time. Open the distribution once to finish its setup, then refresh.') from None
    if result.returncode:
        # Do not expose arbitrary command output, which could include user data.
        raise RuntimeError(f'WSL command failed (exit {result.returncode}). Open the distribution and check its installation.')
    return decode(result.stdout)


def distributions():
    names = run(['--list', '--quiet'])
    available = [n.strip() for n in names.splitlines() if n.strip() and not n.strip().lower().startswith('docker-desktop')]
    if not available:
        raise RuntimeError('No usable WSL distribution found. Install and initialize a distribution such as Ubuntu, then refresh.')
    return [distro_name(n) for n in available]


def command(name, *arguments, root=False):
    return [executable(), '--distribution', distro_name(name), *(['--user', 'root'] if root else []), '--exec', *arguments]


def linux_root(name):
    value = run(command(name, 'wslpath', '-a', '-u', str(ROOT))[1:])
    if not value.startswith('/') or '\n' in value or '\0' in value:
        raise RuntimeError('The application folder is not accessible from this WSL distribution.')
    return value.rstrip('/')


def probe(name, *, prepare=False):
    folder = linux_root(name)
    raw = run(command(name, 'python3', folder + '/wsl_probe.py', *(['--prepare'] if prepare else []))[1:], timeout=300 if prepare else 45)
    try:
        result = json.loads(raw)
        if not isinstance(result, dict) or not isinstance(result.get('ready'), bool):
            raise ValueError()
    except (ValueError, TypeError):
        raise RuntimeError('Could not read the WSL setup report. Check Python 3.10+ in the distribution.') from None
    if not result['ready']:
        raise RuntimeError(result.get('message', 'WSL setup is incomplete.'))
    return result


def worker_command(name, port, token):
    # Recheck the active network mode/dependencies immediately before launching.
    result = probe(name)
    folder = result['folder']
    return command(name, folder + '/.venv-wsl/bin/python', '-u', folder + '/gui_worker.py',
                   '--port', str(port), '--token', token, root=True)
