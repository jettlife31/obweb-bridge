"""Ephemeral Linux routing in a dedicated namespace, with recorded undo actions."""
import ctypes
import errno
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import secrets
from contextlib import contextmanager
import struct
import subprocess

NS = 'obw-gateway'
VETH = 'obw-host'
PEER = 'obw-peer'
TAP = 'obw-tap'
TABLE = 'obw_gateway'
STATE = Path(os.environ.get('OBWEB_RUNTIME_DIR', '/run/outbreak-gateway'))
TRANSIT_POOLS = tuple(map(ipaddress.ip_network, (
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '100.64.0.0/10'
)))


class LocalNetworkError(RuntimeError):
    """Safe local diagnostics, without raw command arguments or stderr."""


def command_label(args):
    if args[:3] == ['ip', 'netns', 'exec']:
        return 'namespace ' + command_label(args[4:])
    words = [word for word in args[1:] if word in
             {'netns', 'link', 'route', 'address', 'rule', 'add', 'delete', 'show', 'list', 'tables', 'table', 'set', 'replace', 'flush'}]
    tool = args[0] if args[0] in ('ip', 'nft', 'sysctl') else 'local command'
    return ' '.join([tool, *words[:3]])


def command(args, text=None, check=True):
    try:
        return subprocess.run(args, input=text, text=True, capture_output=True, check=check, env={**os.environ, 'LC_ALL': 'C'})
    except subprocess.CalledProcessError as error:
        # stderr may echo an entire nft input script. Report only known error
        # categories; never echo arguments, stdout, input text or raw stderr.
        stderr = error.stderr or ''
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', errors='replace')
        reason = next((value for value in ('operation not permitted', 'permission denied',
                      'read-only file system', 'file exists', 'no such file or directory',
                      'device or resource busy', 'invalid argument', 'operation not supported')
                      if value in stderr.lower()), 'unspecified local failure')
        detail = f'Local network command failed: {command_label(args)} (exit {error.returncode}; {reason}).'
        if reason in ('operation not permitted', 'permission denied'):
            detail += (' Host networking requires administrative access to its network namespace.'
                       ' For containers, use sudo podman or a rootful Docker daemon; rootless --cap-add is insufficient.')
        elif reason == 'read-only file system':
            detail += ' The container must allow the required network sysctl writes; see the container guide.'
        raise LocalNetworkError(detail) from None


def require_network_admin():
    # Read-only probes: no rules or sysctl values are changed.
    command(['nft', '-j', 'list', 'tables'])
    try:
        fd = os.open('/proc/sys/net/ipv4/ip_forward', os.O_WRONLY)
    except OSError as error:
        if error.errno == errno.EROFS:
            raise LocalNetworkError('Container network sysctls are read-only. Add '
                                    '--mount type=bind,src=/proc/sys/net,dst=/proc/sys/net '
                                    'to the rootful container run command.') from None
        raise LocalNetworkError(f'Cannot access the required network sysctl (OS error {error.errno}).') from None
    else:
        os.close(fd)



def list_namespaces():
    # iproute2 may emit no bytes at all (rather than []) when no namespaces exist.
    output = command(['ip', '-j', 'netns', 'list']).stdout
    if not output.strip():
        return []
    try:
        namespaces = json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError('Invalid local response from ip -j netns list; no changes were made') from None
    if not isinstance(namespaces, list) or any(
        not isinstance(entry, dict) or not isinstance(entry.get('name'), str)
        for entry in namespaces
    ):
        raise RuntimeError('Unexpected format in the local namespace list')
    return namespaces


def nscommand(args, **kwargs):
    return command(['ip', 'netns', 'exec', NS, *args], **kwargs)


def inventory(lan, client_ip=None, lan_ip=None, transit_network=None, route_table=None):
    for executable in ['ip', 'nft', 'sysctl']:
        if not shutil.which(executable):
            raise RuntimeError(f'Missing dependency: {executable}')
    interfaces = json.loads(command(['ip', '-j', '-4', 'address', 'show', 'dev', lan]).stdout)
    addresses = interfaces[0]['addr_info']
    candidates = [a for a in addresses if a['scope'] == 'global' and
                  (lan_ip is None or a['local'] == lan_ip) and
                  (client_ip is None or ipaddress.ip_address(client_ip) in ipaddress.ip_network(f"{a['local']}/{a['prefixlen']}", strict=False))]
    if len(candidates) != 1:
        raise RuntimeError('Select a LAN interface and local IPv4 address with exactly one matching subnet')
    address = candidates[0]['local']
    subnet = ipaddress.ip_network(f"{address}/{candidates[0]['prefixlen']}", strict=False)
    if client_ip in [address, str(subnet.network_address), str(subnet.broadcast_address)]:
        raise RuntimeError('Invalid client IP or same as the Linux IP')
    if client_ip is not None and (not ipaddress.ip_address(client_ip).is_private or ipaddress.ip_address(client_ip).is_loopback):
        raise RuntimeError('Use a private client IP on the local network')
    defaults = json.loads(command(['ip', '-j', '-4', 'route', 'show', 'default']).stdout)
    if len(defaults) != 1 or 'gateway' not in defaults[0]:
        raise RuntimeError('Expected one IPv4 default route with a router; VPN or multiple routes require review')
    default = defaults[0]
    if default['gateway'] in [client_ip, address]:
        raise RuntimeError('The existing gateway cannot be the client or Linux itself')
    routes = json.loads(command(['ip', '-j', '-4', 'route', 'show', 'table', 'all']).stdout)
    networks = [ipaddress.ip_network(r['dst'], strict=False) for r in routes if r.get('dst', 'default') != 'default']
    if transit_network is not None:
        try:
            transit = ipaddress.ip_network(transit_network, strict=True)
        except ValueError:
            raise RuntimeError('Invalid selected transit network') from None
        if transit.prefixlen != 30 or not any(transit.subnet_of(pool) for pool in TRANSIT_POOLS):
            raise RuntimeError('Selected transit network must be an unused private/shared /30')
        if any(transit.overlaps(n) for n in networks):
            raise RuntimeError('Selected transit network is no longer unused')
    else:
        # Pick a free /30 from private/shared space; link-local is avoided because
        # some hosts install a covering 169.254.0.0/16 route.
        for _ in range(4096):
            pool = secrets.choice(TRANSIT_POOLS)
            offset = secrets.randbelow(pool.num_addresses // 4) * 4
            transit = ipaddress.ip_network((int(pool.network_address) + offset, 30))
            if not any(transit.overlaps(n) for n in networks): break
        else: raise RuntimeError('Could not find an unused transit network')
    rules = json.loads(command(['ip', '-j', '-4', 'rule', 'show']).stdout)
    if any(r.get('priority') == 1 for r in rules):
        raise RuntimeError('A priority-1 policy already exists; review routing before starting')
    tables = {str(r.get('table', 'main')) for r in [*routes, *rules]}
    if route_table is not None:
        if not 10000 <= route_table <= 59999 or str(route_table) in tables:
            raise RuntimeError('Selected routing table is no longer available')
        table = route_table
    else:
        table = secrets.randbelow(50000) + 10000
        while str(table) in tables: table = secrets.randbelow(50000) + 10000
    return {'lan': lan, 'linux_ip': address, 'client_ip': client_ip, 'client_network': client_ip + '/32' if client_ip else str(subnet),
            'uplink': default['dev'], 'router': default['gateway'], 'prefix': candidates[0]['prefixlen'],
            'transit': str(transit), 'host_link': str(transit[1]), 'ns_link': str(transit[2]),
            'route_table': table}


@contextmanager
def in_namespace():
    original = os.open('/proc/self/ns/net', os.O_RDONLY)
    target = os.open('/run/netns/' + NS, os.O_RDONLY)
    libc = ctypes.CDLL(None, use_errno=True)
    def switch(fd):
        if libc.setns(fd, 0) != 0: raise OSError(ctypes.get_errno(), 'setns')
    try:
        switch(target)
        yield
    finally:
        switch(original)
        os.close(original); os.close(target)


def namespace_socket(kind):
    with in_namespace():
        sock = socket.socket(socket.AF_INET, kind)
    sock.setblocking(False)
    return sock


def host_rules(c):
    return f'''table inet {TABLE} {{
 chain forward {{ type filter hook forward priority -5; policy accept;
  iifname "{c['lan']}" ip saddr {c['client_network']} oifname != "{VETH}" counter drop
  oifname "{VETH}" ip saddr != {c['client_network']} counter drop
  iifname "{VETH}" ip daddr != {c['client_network']} counter drop
 }}
}}\n'''


def namespace_rules(c):
    # No service/protocol/port selection. Conntrack NAT keeps client socket flows usable.
    allowed_sources = c['client_network']
    return f'''table inet {TABLE} {{
 chain forward {{ type filter hook forward priority filter; policy drop;
  iifname "{PEER}" oifname "{TAP}" ip saddr {allowed_sources} counter accept
  iifname "{TAP}" oifname "{PEER}" ip daddr {allowed_sources} ct state established,related counter accept
 }}
 chain nat {{ type nat hook postrouting priority srcnat; policy accept;
  oifname "{TAP}" ip saddr {allowed_sources} masquerade
 }}
}}\n'''


def cleanup_saved():
    if os.geteuid():
        raise RuntimeError('Cleanup requires sudo')
    if not STATE.exists():
        print('No cleanup state found.')
        return
    if STATE.is_symlink() or STATE.stat().st_uid != 0 or STATE.stat().st_mode & 0o077:
        raise RuntimeError('Unsafe state directory; cleanup refused')
    owner_file = STATE / 'owner.json'
    if owner_file.exists():
        if owner_file.is_symlink() or owner_file.stat().st_uid != 0:
            raise RuntimeError('Invalid owner record')
        owner = json.loads(owner_file.read_text())
        process = Path(f"/proc/{int(owner['pid'])}/stat")
        if owner['pid'] != os.getpid() and process.exists():
            if process.read_text().split(') ', 1)[1].split()[19] == owner['start']:
                raise RuntimeError('The gateway is still running; stop it with Ctrl+C before cleanup')
    path = STATE / 'undo.json'
    if path.is_symlink() or path.stat().st_uid != 0 or path.stat().st_mode & 0o077:
        raise RuntimeError('Unsafe state file; cleanup refused')
    undo = json.loads(path.read_text())
    failed = []
    for args in reversed(undo):
        result = command(args, check=False)
        already_removed = False
        if result.returncode:
            if args[:3] == ['ip', 'netns', 'delete'] and len(args) == 4:
                already_removed = all(entry['name'] != args[3] for entry in list_namespaces())
            elif args[:3] == ['ip', 'link', 'delete'] and len(args) == 4:
                link = command(['ip', '-j', 'link', 'show', 'dev', args[3]], check=False)
                already_removed = link.returncode != 0
            elif args[:3] == ['nft', 'delete', 'table'] and len(args) == 5:
                tables = command(['nft', '-j', 'list', 'tables'], check=False)
                if tables.returncode == 0:
                    try:
                        listed = json.loads(tables.stdout).get('nftables', [])
                        already_removed = not any(
                            item.get('table', {}).get('family') == args[3] and
                            item.get('table', {}).get('name') == args[4]
                            for item in listed
                        )
                    except (json.JSONDecodeError, AttributeError):
                        already_removed = False
            elif args[:3] == ['ip', 'route', 'delete']:
                route_args = args[3:]
                table = route_args[route_args.index('table') + 1] if 'table' in route_args else 'main'
                routes = command(['ip', '-j', '-4', 'route', 'show', 'table', table], check=False)
                if routes.returncode == 0:
                    try:
                        entries = json.loads(routes.stdout)
                        destination = 'default' if 'default' in route_args else route_args[0]
                        gateway = route_args[route_args.index('via') + 1] if 'via' in route_args else None
                        device = route_args[route_args.index('dev') + 1] if 'dev' in route_args else None
                        metric = route_args[route_args.index('metric') + 1] if 'metric' in route_args else None
                        unreachable = 'unreachable' in route_args
                        already_removed = not any(
                            entry.get('dst', 'default') == destination and
                            entry.get('gateway') == gateway and entry.get('dev') == device and
                            (metric is None or str(entry.get('metric', 0)) == metric) and
                            (entry.get('type') == 'unreachable') == unreachable
                            for entry in entries
                        )
                    except (json.JSONDecodeError, ValueError, IndexError):
                        already_removed = False
            elif args[:3] == ['sysctl', '-q', '-w'] and len(args) == 4:
                key = args[3].split('=', 1)[0]
                sysctl_path = Path('/proc/sys') / key.replace('.', '/')
                already_removed = not sysctl_path.exists()
        if result.returncode and not already_removed:
            failed.append(args)
            print('Could not remove a resource; see /run/outbreak-gateway/undo.json')
    if failed:
        path.write_text(json.dumps(list(reversed(failed))))
        raise RuntimeError('Cleanup incomplete; recovery record was preserved')
    path.unlink()
    if owner_file.exists(): owner_file.unlink()
    STATE.rmdir()


class Network:
    def __init__(self, config):
        self.c, self.undo, self.fd = config, [], None
        self.owned = False

    def remember(self, args):
        self.undo.append(args)
        temporary = STATE / 'undo.tmp'
        temporary.write_text(json.dumps(self.undo))
        temporary.chmod(0o600)
        temporary.replace(STATE / 'undo.json')

    def run(self, args, undo=None):
        command(args)
        if undo:
            self.remember(undo)

    def claim_state(self):
        # Images and named volumes may supply an empty directory. Claim the
        # owner file atomically so two starters cannot adopt that directory.
        if STATE.is_symlink():
            raise RuntimeError('The runtime state directory must not be a symbolic link')
        STATE.mkdir(mode=0o700, exist_ok=True)
        if any(STATE.iterdir()):
            raise RuntimeError('Runtime state already exists; use --cleanup before restarting')
        try:
            fd = os.open(STATE / 'owner.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            raise RuntimeError('Runtime state is already claimed by another startup') from None
        self.owned = True
        with os.fdopen(fd, 'w') as owner_file:
            owner = {'pid': os.getpid(), 'start': Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19]}
            json.dump(owner, owner_file)
        if os.geteuid() == 0:
            os.chown(STATE, 0, 0)
        STATE.chmod(0o700)
        fd = os.open(STATE / 'undo.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as journal:
            journal.write('[]')

    def setup(self, mac):
        if os.geteuid():
            raise RuntimeError('Running the gateway requires sudo; the plan and tests do not')
        if any(n['name'] == NS for n in list_namespaces()):
            raise RuntimeError('Namespace already exists; use --cleanup if it belongs to a previous run')
        links = json.loads(command(['ip', '-j', 'link', 'show']).stdout)
        if any(x['ifname'] in [VETH, PEER] for x in links):
            raise RuntimeError('Reserved interface already exists')
        tables = json.loads(command(['nft', '-j', 'list', 'tables']).stdout)
        if any(x.get('table', {}).get('name') == TABLE for x in tables['nftables']):
            raise RuntimeError('Reserved nftables table already exists')
        self.claim_state()
        (STATE / 'undo.json').chmod(0o600)
        self.run(['ip', 'netns', 'add', NS], ['ip', 'netns', 'delete', NS])
        self.run(['ip', 'link', 'add', VETH, 'type', 'veth', 'peer', 'name', PEER],
                 ['ip', 'link', 'delete', VETH])
        self.run(['ip', 'link', 'set', PEER, 'netns', NS])
        self.run(['ip', 'address', 'add', self.c['host_link'] + '/' + str(ipaddress.ip_network(self.c['transit']).prefixlen), 'dev', VETH])
        self.run(['ip', 'link', 'set', VETH, 'up'])
        nscommand(['ip', 'link', 'set', 'lo', 'up'])
        nscommand(['ip', 'address', 'add', self.c['ns_link'] + '/' + str(ipaddress.ip_network(self.c['transit']).prefixlen), 'dev', PEER])
        nscommand(['ip', 'link', 'set', PEER, 'up'])
        nscommand(['ip', 'route', 'add', self.c['client_network'], 'via', self.c['host_link']])
        nscommand(['sysctl', '-q', '-w', 'net.ipv4.ip_forward=1'])
        nscommand(['sysctl', '-q', '-w', 'net.ipv4.conf.all.rp_filter=0'])
        nscommand(['sysctl', '-q', '-w', 'net.ipv4.conf.default.rp_filter=0'])
        nscommand(['sysctl', '-q', '-w', 'net.ipv6.conf.all.disable_ipv6=1'])
        nscommand(['sysctl', '-q', '-w', 'net.ipv6.conf.default.disable_ipv6=1'])
        self.fd = self.open_tap()
        nscommand(['ip', 'link', 'set', TAP, 'address', ':'.join(f'{b:02x}' for b in mac), 'up'])
        nscommand(['nft', '-f', '-'], text=namespace_rules(self.c))

    def open_tap(self):
        with in_namespace():
            fd = os.open('/dev/net/tun', os.O_RDWR | os.O_NONBLOCK)
            try:
                fcntl.ioctl(fd, 0x400454ca, struct.pack('16sH', TAP.encode(), 0x0002 | 0x1000))
            except BaseException:
                os.close(fd); raise
        return fd

    def validate_lease(self, lease):
        remote = ipaddress.ip_network(f'{lease.address}/{lease.prefix}', strict=False)
        if remote.overlaps(ipaddress.ip_network(self.c['transit'])) or remote.overlaps(ipaddress.ip_network(self.c['client_network'])):
            raise RuntimeError('Remote DHCP overlaps the transit or client network; host routes were not changed')
        if any(ipaddress.ip_address(d) in ipaddress.ip_network(self.c['transit']) or ipaddress.ip_address(d) in ipaddress.ip_network(self.c['client_network']) for d in lease.dns):
            raise RuntimeError('Remote DNS conflicts with the client return network')

    def configure_tunnel(self, lease):
        self.validate_lease(lease)
        # The TAP belongs exclusively to this gateway. Retain host routing and
        # the local interfaces while replacing a disconnected remote session.
        nscommand(['ip', 'address', 'flush', 'dev', TAP, 'scope', 'global'])
        nscommand(['ip', 'address', 'add', f'{lease.address}/{lease.prefix}', 'dev', TAP])
        nscommand(['ip', 'link', 'set', TAP, 'up'])
        nscommand(['ip', 'route', 'replace', 'default', 'via', lease.gateway, 'dev', TAP])

    def suspend(self):
        # Offline client traffic cannot fall through to the host Internet route.
        nscommand(['ip', 'link', 'set', TAP, 'down'])

    def activate(self, lease):
        self.configure_tunnel(lease)
        command(['nft', '-c', '-f', '-'], text=host_rules(self.c))
        command(['nft', '-f', '-'], text=host_rules(self.c))
        self.remember(['nft', 'delete', 'table', 'inet', TABLE])
        table = str(self.c['route_table'])
        # A terminal unreachable route prevents RPDB fall-through to the home router if TAP/veth fails.
        self.run(['ip', 'route', 'add', 'unreachable', 'default', 'metric', '32767', 'table', table],
                 ['ip', 'route', 'delete', 'unreachable', 'default', 'metric', '32767', 'table', table])
        self.run(['ip', 'route', 'add', 'default', 'via', self.c['ns_link'], 'dev', VETH, 'onlink', 'table', table],
                 ['ip', 'route', 'delete', 'default', 'via', self.c['ns_link'], 'dev', VETH, 'table', table])
        rule = ['priority', '1', 'from', self.c['client_network'], 'iif', self.c['lan'], 'table', table]
        self.run(['ip', 'rule', 'add', *rule], ['ip', 'rule', 'delete', *rule])
        for key, value in [(f"net.ipv4.conf.{self.c['lan']}.forwarding", '1'),
                           (f'net.ipv4.conf.{VETH}.forwarding', '1'),
                           ('net.ipv4.conf.all.send_redirects', '0'),
                           (f"net.ipv4.conf.{self.c['lan']}.send_redirects", '0'),
                           (f'net.ipv4.conf.{VETH}.rp_filter', '0'),
                           ('net.ipv4.conf.all.rp_filter', '0')]:
            old = command(['sysctl', '-n', key]).stdout.strip()
            if old != value:
                self.run(['sysctl', '-q', '-w', f'{key}={value}'], ['sysctl', '-q', '-w', f'{key}={old}'])

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        if self.owned:
            cleanup_saved()
            self.owned = False
