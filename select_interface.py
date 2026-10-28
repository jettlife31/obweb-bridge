#!/usr/bin/env python3
"""Interactively select the Linux LAN interface connected to the client network."""
import json
import subprocess

result = subprocess.run(
    ['ip', '-j', '-4', 'address', 'show'],
    capture_output=True, text=True, check=True
)
interfaces = []
for item in json.loads(result.stdout):
    addresses = [a for a in item.get('addr_info', []) if a.get('scope') == 'global']
    if addresses:
        interfaces.append((item['ifname'], ', '.join(a['local'] for a in addresses)))
if not interfaces:
    raise SystemExit('No active LAN interfaces with global IPv4 addresses were found.')
with open('/dev/tty', 'w') as tty_out, open('/dev/tty', 'r') as tty_in:
    tty_out.write('Select the Linux interface connected to the client LAN:\n')
    for i, (name, addresses) in enumerate(interfaces, 1):
        tty_out.write(f'  {i}) {name} ({addresses})\n')
    tty_out.flush()
    while True:
        tty_out.write('Interface number (or q to quit): ')
        tty_out.flush()
        value = tty_in.readline().strip()
        if value.lower() == 'q':
            raise SystemExit(1)
        if value.isdigit() and 1 <= int(value) <= len(interfaces):
            print(interfaces[int(value) - 1][0])
            break
        tty_out.write('Choose a number from the list.\n')
