"""Read Linux-side WSL readiness; prepare only the project's Python venv on request."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def inspect(prepare=False):
    if sys.version_info < (3, 10):
        raise RuntimeError('Install Python 3.10+ inside the WSL distribution.')
    info = shutil.which('wslinfo')
    if not info and Path('/usr/lib/wsl/lib/wslinfo').is_file():
        info = '/usr/lib/wsl/lib/wslinfo'
    if not info:
        raise RuntimeError('Cannot verify WSL networking. Update WSL and use WSL 2 mirrored networking. See the LAN guide.')
    mode = subprocess.run([info, '--networking-mode'], capture_output=True, text=True, timeout=10)
    if mode.returncode or mode.stdout.strip().lower() != 'mirrored':
        raise RuntimeError('LAN gateway via WSL requires active mirrored networking (Windows 11 22H2+). NAT is not supported. See the LAN guide.')
    missing = [name for name in ('ip', 'nft', 'sysctl') if not shutil.which(name)]
    if missing or not Path('/dev/net/tun').exists():
        raise RuntimeError('Missing WSL network dependencies: ' + ', '.join(missing + ([] if Path('/dev/net/tun').exists() else ['/dev/net/tun'])) + '. On Ubuntu install iproute2 nftables procps; enable TUN/TAP if missing.')
    python = ROOT / '.venv-wsl/bin/python'
    if prepare:
        # The GUI runs this as the distribution's regular user. No sudo/apt or
        # host routing/firewall changes are performed by preparation.
        for args in ([sys.executable, '-m', 'venv', str(ROOT / '.venv-wsl')],
                     [str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')]):
            result = subprocess.run(args, capture_output=True, timeout=240)
            if result.returncode:
                raise RuntimeError('WSL Python setup failed. Install python3-venv and python3-pip in the distribution, check Internet access, then retry Prepare WSL.')
    if not python.exists():
        raise RuntimeError('WSL Python environment is missing. Click Prepare WSL to create .venv-wsl and install the Python libraries.')
    check = subprocess.run([str(python), '-c', 'import websockets; assert websockets.__version__ == "15.0.1"'], capture_output=True, timeout=10)
    if check.returncode:
        raise RuntimeError('WSL Python libraries need setup. Click Prepare WSL.')
    from container_interfaces import interfaces
    choices = [[f'{name} — {ip}/{prefix}', name, ip] for name, addresses in interfaces() for ip, prefix in addresses]
    if not choices:
        raise RuntimeError('No usable IPv4 LAN interface found inside WSL.')
    return {'ready': True, 'folder': str(ROOT), 'choices': choices, 'network_mode': 'mirrored'}


if __name__ == '__main__':
    try:
        report = inspect(prepare='--prepare' in sys.argv[1:])
    except RuntimeError as error:
        report = {'ready': False, 'message': str(error)}
    except Exception as error:
        report = {'ready': False, 'message': f'WSL readiness check failed ({type(error).__name__}). Check the distribution setup.'}
    print(json.dumps(report, ensure_ascii=True))
