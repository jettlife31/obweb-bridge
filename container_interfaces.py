#!/usr/bin/env python3
"""Read-only interface discovery and validation before container setup."""
import argparse
from datetime import datetime
import ipaddress
import json
import os
import re
import subprocess
import sys

RESERVED = {'lo', 'obw-host', 'obw-peer', 'obw-tap', 'obw-pcsx2'}


def log(message):
    timestamp = datetime.now().astimezone().isoformat(timespec='seconds')
    print(f'[{timestamp}] {message}', file=sys.stderr, flush=True)


def interfaces():
    result = subprocess.run(['ip', '-j', '-4', 'address', 'show'],
                            capture_output=True, text=True, check=True)
    available = []
    for link in json.loads(result.stdout):
        name = link.get('ifname', '')
        if name in RESERVED or 'UP' not in link.get('flags', []):
            continue
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,15}', name):
            continue
        addresses = []
        for address in link.get('addr_info', []):
            if address.get('scope') != 'global':
                continue
            ip = ipaddress.IPv4Address(address['local'])
            if ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_multicast:
                continue
            addresses.append((str(ip), address['prefixlen']))
        if addresses:
            available.append((name, addresses))
    return available


def show(available):
    log('Available interfaces in the container network namespace:')
    for name, addresses in available:
        log(f'  {name}: ' + ', '.join(f'{ip}/{prefix}' for ip, prefix in addresses))
    if not available:
        log('  No usable active IPv4 interface found.')
    log('Choose the interface on the client LAN. Use Docker Engine on Linux with --network host.')
    log('Docker Desktop may show only VM interfaces; these do not expose the physical LAN to this gateway.')
    if available:
        example = available[0][0]
        log(f'Example: -e OBWEB_LAN_INTERFACE={example} (replace with the client LAN interface).')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list-interfaces', action='store_true')
    parser.add_argument('--check-network-admin', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        available = interfaces()
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        log('Could not read the local interface inventory; no network configuration was changed.')
        return 2
    if args.list_interfaces:
        show(available)
        return 0
    selected = os.environ.get('OBWEB_LAN_INTERFACE', '')
    address = os.environ.get('OBWEB_LAN_IP', '')
    client = os.environ.get('OBWEB_CLIENT_IP', '')
    choices = dict(available)
    error = None
    if not selected:
        error = 'OBWEB_LAN_INTERFACE is required.'
    elif selected not in choices:
        error = 'OBWEB_LAN_INTERFACE does not select a usable active IPv4 interface.'
    elif address and address not in [ip for ip, _ in choices[selected]]:
        error = 'OBWEB_LAN_IP is not assigned to the selected interface.'
    else:
        candidates = [(ip, prefix) for ip, prefix in choices[selected] if not address or ip == address]
        if client:
            try:
                client_ip = ipaddress.IPv4Address(client)
                candidates = [(ip, prefix) for ip, prefix in candidates if client_ip in ipaddress.ip_network(f'{ip}/{prefix}', strict=False)]
            except ValueError:
                error = 'OBWEB_CLIENT_IP must be a valid IPv4 address.'
        if not error and len(candidates) != 1:
            error = 'Select one matching interface IPv4 address with OBWEB_LAN_IP and check OBWEB_CLIENT_IP if set.'
    if error:
        log(error)
        show(available)
        log('Startup blocked before login or networking. Set the variables and recreate the container.')
        return 2
    if args.check_network_admin:
        from network import require_network_admin, LocalNetworkError
        try:
            require_network_admin()
        except LocalNetworkError as error:
            log(str(error))
            log('Startup blocked before account setup or network changes.')
            return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
