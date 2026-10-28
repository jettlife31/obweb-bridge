# obweb-bridge

A Linux IPv4 gateway that carries client traffic to Outbreak Web over its Ethernet WebSocket transport. Clients can be ARMSX2 on Android, a physical PS2, or another computer on the same LAN. The emulator does not need to be modified. Windows and WSL2 host backends are not implemented yet.

## Setup

### 0. Prerequisites

#### Patch your game image

Use the matching xdelta patch for your own USA game image:

- Outbreak USA v2.00: `xdelta/Resident Evil - Outbreak (USA) (v2.00).xdelta`
  - Original ISO SHA-256: `69ae2c48e6f01e2605659feabb54eb9b82c63a809bdc8a78ad2d160b3c59a4a1`
  - Patched ISO SHA-256: `0a6b912d873cb262e991f359125e37dde4848864d905c888f822ed98cf9bc0c1`
- Outbreak File #2 USA: `xdelta/Resident Evil - Outbreak - File 2 (USA).xdelta`
  - Original ISO SHA-256: `bf33c7bcd727868abe6866d747a930c3c54bb7395ab8ebdfce1f7137641f6759`
  - Patched ISO SHA-256: `6363263595ea0a4d12308b3c05e2a9c53cc92e96469c0509ee7952b97c09c970`

Apply the patch to a copy of the matching original image and keep the original unchanged. The SHA-256 values above were verified against the source and patched ISO files. For example, with `xdelta3`:

```sh
xdelta3 -d -s "original.iso" "patch.xdelta" "outbreak-web.iso"
```

#### Prepare your Outbreak Web account

Before starting the bridge, sign in to Outbreak Web and:

1. Open **Settings > Online > Show my code** and copy your REO transfer code. The bridge login will ask you to paste this code when you choose **Import**.
2. Open **Saves > Export save (.ps2)** and save the exported file somewhere safe for your emulator or console setup.

Keep the REO code and exported save private. Do not include them in screenshots or share them with the bridge project.

### 1. Prepare the Linux bridge and route the client through it

The bridge runs on a Linux computer. Install Python 3.10+, `iproute2`, `nftables`, and TUN/TAP support. On Debian or Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
```

The native launcher asks which Linux interface connects to the client LAN. Common names are `enp3s0` or `eno1` for Ethernet and `wlp2s0` or `wlan0` for Wi-Fi. It displays each interface's IPv4 address so you can choose the right one.

```sh
./start-local.sh
```

The native launcher starts as a regular user and requests `sudo` only for temporary network setup. The bridge host requires Linux; a Windows PC can be a client by using the Linux bridge's LAN IP as its gateway and DNS.

#### Run the published container image

Use Linux Docker Engine. Host networking routes client traffic only; Windows can be a client but cannot host this backend.

The container requires `OBWEB_LAN_INTERFACE` (the Linux interface connected to the client LAN) and `OBWEB_USERNAME`. `OBWEB_RUN_MODE` is internal and set automatically. Compose users can pass the same variables under `environment:`.

Docker creates the named volume on first use and keeps it between runs. The network namespace directory is created inside the container.

```bash
docker run --rm --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --device /dev/net/tun:/dev/net/tun \
  --security-opt seccomp=unconfined \
  --mount type=volume,src=obweb-bridge-data,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=wlp2s0 \
  -e OBWEB_USERNAME=your_username \
  ghcr.io/zenaror/obweb-bridge:latest
```

Replace `wlp2s0` with your Linux interface name. Omit the REO code to create a new account; the code's username must match `OBWEB_USERNAME`. The container prints the game credentials. An existing username without a matching code produces an error. The `obweb-bridge-data` Docker volume keeps account and cleanup state between runs; add `--cleanup` after the image name to recover from a forced stop. Pull requests build the image; pushes to `main` and version tags publish it.

Add these `-e` flags before the image name only when needed:

- **OPTIONAL** — `-e OBWEB_LAN_IP=192.168.1.10` when the selected interface has multiple local IPv4 addresses.
- **OPTIONAL** — `-e OBWEB_CLIENT_IP=192.168.1.114` to restrict forwarding to one client address.
- **OPTIONAL** — `-e OBWEB_REO_CODE='REO1-username-<32-hex-characters>'` to import an existing account using the complete code from **Settings > Online > Show my code**.
- **OPTIONAL** — `-e OBWEB_WSS_URL=wss://outbreakweb.com/eth` to override the default WSS endpoint.
- **OPTIONAL** — `-e OBWEB_WSS_ORIGIN=https://outbreakweb.com` to override the default WSS origin.
- **OPTIONAL** — `-e OBWEB_RUNTIME_DIR=/var/lib/obweb-bridge/runtime` to change the runtime state path; keep it inside `/var/lib/obweb-bridge` so the Docker volume persists it.

The launcher prepares the Outbreak Web login, shows a network plan, and asks for `sudo` to enable temporary routing. Wait for **READY**. The login helper can create a username or import an existing account with its transfer code; it displays the game password for manual entry. Keep that screen private.

The client and Linux computer must share the same LAN, and Wi-Fi client isolation must be off. For a PC or Android client, set the device's default gateway and DNS to the Linux computer's LAN IP printed by the bridge. For a real PS2, use the in-game network settings below.

### 2. Configure the game and network

Even when using an emulator, create a **new in-game network configuration** instead of reusing an old one, and set its network fields to **Automatic**. In the emulator's own Ethernet settings, enable Ethernet, choose **Online / Sockets**, and set primary and secondary DNS manually to the Linux computer's LAN IP. In ARMSX2, these are the emulator's Ethernet settings.

For a physical PS2, create a new network configuration in the game's Network Play setup and enter:

- **IP address:** an unused address on the same LAN as the Linux computer. Do not use the Linux computer's IP, another device's IP, or an address inside the router's DHCP pool.
- **Subnet mask:** the mask used by your LAN (commonly `255.255.255.0` for a `/24` network).
- **Gateway:** the Linux computer's LAN IP printed by the bridge.
- **Primary DNS (DNS1):** the same Linux computer LAN IP.
- **Secondary DNS (DNS2):** set it to the Linux computer's LAN IP if the setup requires a value.

Save the profile and select it for Network Play. This static console setup has been confirmed working with a real PS2.

Do not enter the remote DHCP address shown by the bridge into the console's network settings.

### 3. Play

Use the patched image, boot the game from a full start, choose NETWORK PLAY, and enter the username and password from the login helper. Press Ctrl+C in the bridge terminal when finished; restore the client's original gateway/DNS settings afterward.

## What it does

The bridge routes IPv4 traffic from the configured client LAN subnet through an isolated Linux namespace, generic NAT, TAP, and the binary WSS connection. The remote DHCP response supplies the tunnel address, gateway, DNS, and lease. DNS requests are forwarded to that remote DNS without domain-specific rules. The transport does not select game IPs, domains, or application ports.

In ARMSX2 Sockets mode, the emulator terminates the virtual PS2 network on Android. This program is therefore an IPv4 gateway with NAT, not a layer-2 bridge from the PS2 Ethernet adapter. It does not implement DNAS or game services; the DNAS bypass is in the patched game image.

The gateway does not change the Linux computer's default route. IPv6, VPN, mobile data, direct same-LAN traffic, DHCP lease renewal, and classless DHCP routes are outside the current path. The session stops if WSS disconnects or before 90% of the remote DHCP lease expires. Ordinary Internet access through the client may be limited to services available through WSS.

## Diagnostics

With the bridge running, use another terminal:

```sh
sudo .venv/bin/python diagnose.py --lan-interface INTERFACE --seconds 45
```

The diagnostic reports traffic counts and DNS metadata without logging packet payloads, arbitrary DNS names, credentials, or remote IP addresses.
