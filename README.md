# Generic WSS gateway for Android / ARMSX2

This project connects ARMSX2 on Android, using Online / Sockets, to the Outbreak Web Ethernet-over-WebSocket transport through a Linux computer. The emulator is not modified.

The gateway routes client IPv4 traffic through an isolated Linux network namespace, generic NAT, a TAP device, and the binary WSS connection. Remote DHCP provides the tunnel address, subnet, gateway, DNS and lease. DNS requests are forwarded unchanged to the DNS server supplied by remote DHCP. The gateway has no game destination, application port, or domain routing rules.

This is an IPv4 gateway with NAT, not a layer-2 bridge from the emulated PS2 adapter. In Sockets mode, ARMSX2 terminates the emulated network inside Android. The Linux computer does not receive the PS2's original Ethernet frames. The TAP/WSS path carries frames without selecting game IPs, application protocols or ports; the kernel handles routing and NAT.

The only Ethernet normalization replaces an all-zero destination MAC received from the server with the TAP interface MAC. That observed frame format would otherwise not be delivered normally to the kernel. No remote destination filters are used.

## Requirements

Linux, Python 3.10+, `iproute2`, `nftables`, TUN/TAP and network namespaces. On Debian or Ubuntu, install system packages if needed:

```sh
sudo apt install python3-venv iproute2 nftables
```

Copy `config.example.json` to `config.local.json`, then set `lan_interface` to the Linux interface connected to the client network. The client subnet is detected automatically. The optional `android_ip` setting can restrict access to one IPv4 address. Keep `config.local.json` local; it is ignored by Git.

## Run

Run the launcher as a regular user:

```sh
./start-local.sh
```

It creates `.venv`, installs the pinned Python dependency, displays a read-only network plan, prepares the Outbreak Web login, then requests `sudo` to configure temporary networking. Wait for **READY**. It does not change the Linux computer's default gateway or install a persistent service. Press Ctrl+C to clean up.

Optional direct commands:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python gateway.py --config config.local.json
.venv/bin/python gateway.py --config config.local.json --probe
sudo .venv/bin/python gateway.py --config config.local.json --run
```

`--probe` checks WSS and remote DHCP only. It does not authenticate to the game.

## Client and ARMSX2 setup

The client and Linux computer must be on the same LAN subnet, with Wi-Fi client isolation disabled. Set the client's Wi-Fi gateway and DNS to the Linux LAN IP printed by the program. Keep a valid client address and subnet mask. Do not configure a public secondary DNS.

In ARMSX2, enable Ethernet and select **Online / Sockets**. Keep the PS2 IP, gateway and subnet automatic, and set primary/secondary DNS manually to the Linux LAN IP. Fully restart the game after changing network settings; do not resume a save state.

The remote IP, gateway and DNS belong to the WSS tunnel and must not be entered as the client's Wi-Fi settings. All IPv4 traffic routed through Linux from the detected LAN subnet uses WSS. Clients that continue to use the home router are not redirected. IPv6, VPN, mobile data and same-subnet direct connections are outside this IPv4 gateway. Ordinary Internet access depends on what the remote WSS network provides.

## Account setup

`login_web.py` is separate from packet forwarding. It registers or checks the username and credential over HTTPS. It can create a new identity or import an account using the site's transfer code. The identity is stored in a private local state directory and the derived game password is shown only in the local terminal. Enter it manually in the game. No account credentials are included in this project.

The original Outbreak USA v2.00 and File #2 USA images were preserved; prepared copies use the DNAS bypass. The bypass was verified in code. On 2026-10-24, the user reported that both games connected and started matches in ARMSX2.

## Network behavior and limits

- All IPv4 unicast destinations routed through this gateway use the same WSS path. TCP, UDP and ICMP were exercised in an isolated Linux integration test. There is no application-protocol allowlist.
- Traffic addressed to Linux itself is local. DNS received by the relay is forwarded through the remote namespace. Local Ethernet discovery such as ARP remains on the LAN.
- DHCPv4 supplies the remote address, subnet, gateway, DNS and lease. Overlapping networks that make return routing ambiguous are rejected. Classless DHCP routes (options 121/249) and lease renewal are not supported.
- The gateway shuts down before 90% of the lease expires, or when WSS disconnects. It does not reconnect transparently.
- NAT changes IP/transport headers and does not rewrite addresses embedded in application payloads.
- The bridge does not implement DNAS, game login or game services. The DNAS bypass is in the prepared game image.
- The current client scope is the detected LAN subnet. `--android-ip` can narrow it to one client.

## Diagnostics and privacy

The program does not log packet payloads, arbitrary DNS names, credentials or raw packets. Routine output shows frame counts and DNS query/answer/error counts.

With the gateway running, diagnostics can be started in another terminal:

```sh
sudo .venv/bin/python diagnose.py --config config.local.json --seconds 45
```

Try connecting while the diagnostic runs. It reports counts by interface, direction, protocol/port and DNS response code without showing DNS names or remote addresses. An optional `--test-dns ADDRESS` checks a DNS server supplied by remote DHCP through the tunnel. `--dns-name NAME` can compare captured questions with one name; other names remain hidden. The diagnostic does not restart the gateway or change network settings.

## Cleanup and validation

Press Ctrl+C to remove the temporary namespace, interfaces, routes, firewall table and modified sysctls. Restore the client's original Wi-Fi settings afterward. If the process was killed without cleanup, inspect the recorded state and run:

```sh
sudo .venv/bin/python gateway.py --config config.local.json --cleanup
```

The cleanup refuses to interfere with a live instance and never flushes the system firewall ruleset.

Automated tests can be run with:

```sh
.venv/bin/python -m unittest discover -s tests -v
sh tests/linux_integration.sh
```

The isolated Linux test covers arbitrary TCP/UDP/ICMP and DNS UDP/TCP through a simulated remote endpoint, client IP changes without restarting, no home-router fallback on link failure, preservation of host routing, and cleanup. It is not a physical Android or console test. The user has confirmed successful matches on ARMSX2 for both prepared games; physical PS2 console operation has not been verified.
