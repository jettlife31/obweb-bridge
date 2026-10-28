# Restarting the generic gateway

Copy `config.example.json` to `config.local.json` and set the LAN interface for your system. Local settings are stored in `config.local.json`, which is excluded from Git. The packet transport does not interpret Outbreak or its services. The launcher runs the separate `login_web.py` account setup before configuring the network.

1. Stop the previous gateway with **Ctrl+C** so it can remove its temporary configuration.
2. Run `./iniciar-local.sh` as a regular user.
3. Enter your Outbreak Web username. Choose **N** for a new username, or **I** to import the transfer code from the page if the username is already yours. The code is entered invisibly. Do not use another service's password.
4. The helper registers/checks the username and credential over HTTPS, separately from WSS packet transport. It displays the username and 12-character game password in the terminal. Enter them manually in the game. Keep the screen private.
5. Press Enter and wait for **READY**. The plan should say that client IPv4 traffic uses WSS.

## Configure the client network

The client must be on the same LAN subnet as the Linux computer. The gateway detects that subnet automatically; no client IP needs to be entered in the bridge configuration.

Configure the client's Wi-Fi gateway and DNS to the Linux LAN IP printed by the program. Make sure the client has a valid address and subnet mask. Do not set a public secondary DNS.

In ARMSX2, enable Ethernet and select **Online / Sockets**. Keep the PS2 IP, gateway and subnet automatic, and set primary/secondary DNS manually to the Linux LAN IP. Fully restart the game after network changes; do not resume a save state.

The remote network settings come from WSS DHCP. DNS queries received by the gateway are forwarded to the remote DNS without domain-specific handling. Ordinary Internet access from clients routed through this gateway depends on the services exposed by WSS. IPv6, VPN and mobile data are outside this IPv4 gateway.

## Prepared game images and login

Use the patched copy of Outbreak USA v2.00 or File #2 USA. Start the game from a full boot, enter NETWORK PLAY, then manually enter the username and password shown by the helper. The DNAS bypass was verified in code. On 2026-10-24, the user reported that both games connected and started matches in ARMSX2.

The identity is stored in `$XDG_STATE_HOME/outbreak-web-login/identities.json` or `~/.local/state/outbreak-web-login/identities.json`, with private directory/file permissions. It is reused to keep the same password. Do not delete it if you want to keep the identity. Existing site accounts require their transfer code; the username alone cannot recover them. No identity data is included in the gateway files.

If registration or the website connection fails, the gateway will not start. Ctrl+C at the login prompt also cancels startup. Account setup does not change DNS, destinations, ports, or forwarded packets.

## Network scope

All IPv4 traffic routed through the Linux gateway from the LAN subnet uses WSS. Devices that keep using the home router are not redirected. DNS accepts requests from the detected local subnet only. The optional `--android-ip` setting can restrict use to one IPv4 address.
