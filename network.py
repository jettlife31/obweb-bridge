"""Ephemeral Linux routing in a dedicated namespace, with recorded undo actions."""
import ctypes
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


def command(args, text=None, check=True):
    return subprocess.run(args, input=text, text=True, capture_output=True, check=check, env={**os.environ, 'LC_ALL': 'C'})


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


def inventory(lan, client_ip=None, lan_ip=None):
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
    return f'''table inet {TABLE} {{
 chain forward {{ type filter hook forward priority filter; policy drop;
  iifname "{PEER}" oifname "{TAP}" ip saddr {c['client_network']} counter accept
  iifname "{TAP}" oifname "{PEER}" ip daddr {c['client_network']} ct state established,related counter accept
 }}
 chain nat {{ type nat hook postrouting priority srcnat; policy accept;
  oifname "{TAP}" ip saddr {c['client_network']} masquerade
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
        already_removed = args[:3] == ['ip', 'route', 'delete'] and result.returncode == 2 and result.stderr.strip() == 'RTNETLINK answers: No such process'
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
        STATE.mkdir(mode=0o700)  # Exclusive claim; never overwrite another process's state.
        self.owned = True
        owner = {'pid': os.getpid(), 'start': Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19]}
        (STATE / 'owner.json').write_text(json.dumps(owner))
        (STATE / 'owner.json').chmod(0o600)
        (STATE / 'undo.json').write_text('[]')
        (STATE / 'undo.json').chmod(0o600)
        self.run(['ip', 'netns', 'add', NS], ['ip', 'netns', 'delete', NS])
        self.run(['ip', 'link', 'add', VETH, 'type', 'veth', 'peer', 'name', PEER],
                 ['ip', 'link', 'delete', VETH])
        self.run(['ip', 'link', 'set', PEER, 'netns', NS])
        self.run(['ip', 'address', 'add', self.c['host_link'] + '/30', 'dev', VETH])
        self.run(['ip', 'link', 'set', VETH, 'up'])
        nscommand(['ip', 'link', 'set', 'lo', 'up'])
        nscommand(['ip', 'address', 'add', self.c['ns_link'] + '/30', 'dev', PEER])
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

    def activate(self, lease):
        remote = ipaddress.ip_network(f'{lease.address}/{lease.prefix}', strict=False)
        if remote.overlaps(ipaddress.ip_network(self.c['transit'])) or remote.overlaps(ipaddress.ip_network(self.c['client_network'])):
            raise RuntimeError('Remote DHCP overlaps the transit or client network; host routes were not changed')
        if any(ipaddress.ip_address(d) in ipaddress.ip_network(self.c['transit']) or ipaddress.ip_address(d) in ipaddress.ip_network(self.c['client_network']) for d in lease.dns):
            raise RuntimeError('Remote DNS conflicts with the client return network')
        nscommand(['ip', 'address', 'add', f'{lease.address}/{lease.prefix}', 'dev', TAP])
        nscommand(['ip', 'route', 'add', 'default', 'via', lease.gateway, 'dev', TAP])
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
