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

Set `OBWEB_LAN_INTERFACE` to skip the interface menu, and optionally set `OBWEB_LAN_IP` when that interface has more than one local IPv4 address. `OBWEB_CLIENT_IP` optionally restricts the forwarded client to one address. The WSS endpoint and origin can be overridden with `OBWEB_WSS_URL` and `OBWEB_WSS_ORIGIN`. Leave them unset for the service defaults. For example:

```sh
export OBWEB_LAN_INTERFACE=YOUR_LAN_INTERFACE
export OBWEB_LAN_IP=192.168.1.10
./start-local.sh
```

Without `OBWEB_LAN_INTERFACE`, choose the interface from the menu. The native launcher starts as a regular user and requests `sudo` only for temporary network setup.

```sh
./start-local.sh
```

#### Run the published container image

The container uses host networking so it can see the Linux host's actual LAN interface and IP. It applies routing only to forwarded client traffic; the host's own connections keep their normal route. Host networking and the packet/TAP operations require a Linux Docker Engine. Docker Desktop's host mode is not suitable for this bridge's packet-forwarding path.

Create persistent state directories and the namespace mount point once:

```sh
sudo mkdir -p /var/lib/obweb-bridge /run/netns
```

Then run the image (replace the interface and LAN IP with values from your Linux host):

```sh
docker run --rm -it --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --device /dev/net/tun:/dev/net/tun \
  --security-opt seccomp=unconfined \
  --mount type=bind,src=/run/netns,dst=/run/netns,bind-propagation=rshared \
  --mount type=bind,src=/var/lib/obweb-bridge,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=YOUR_LAN_INTERFACE \
  -e OBWEB_LAN_IP=192.168.1.10 \
  ghcr.io/zenaror/obweb-bridge:latest
```

The image stores account credentials and interrupted-run cleanup state under `/var/lib/obweb-bridge`. Keep this directory between runs. `OBWEB_CLIENT_IP`, `OBWEB_WSS_URL`, and `OBWEB_WSS_ORIGIN` can also be passed with `-e`. On a pull request, GitHub Actions builds the image without publishing it. Pushes to `main` publish `latest`, `main`, and a commit tag; version tags publish versioned images. The GHCR image is public and can be pulled without signing in.

The container needs `NET_ADMIN` to add the client-specific route/firewall rules and `SYS_ADMIN` for the temporary network namespace. The default seccomp filter blocks the namespace operations used by this implementation, so the example disables that filter. Run only an image you trust. If the container is forcibly terminated and does not clean up, recover its saved networking state with:

```sh
docker run --rm --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --security-opt seccomp=unconfined \
  --mount type=bind,src=/run/netns,dst=/run/netns,bind-propagation=rshared \
  --mount type=bind,src=/var/lib/obweb-bridge,dst=/var/lib/obweb-bridge \
  ghcr.io/zenaror/obweb-bridge:latest --cleanup
```

Use this only after confirming the bridge container is stopped. On abrupt host power loss, inspect the host's network state before restarting.

The launcher prepares the Outbreak Web login, shows a network plan, and asks for `sudo` to enable temporary routing. The container does the same with its required capabilities. Wait for **READY**. The login helper can create a username or import an existing account with its transfer code; it displays the game password in the terminal for manual entry. Keep that screen private.

Configure the client to use the Linux computer's LAN IP as its **default gateway and DNS server**. Keep the client IP address and subnet mask valid for that LAN. This means setting the network gateway on Android, Windows, or Linux, or setting the PS2 IP, subnet mask, and gateway in the PS2 game's network configuration. The client and Linux computer must share the LAN, and Wi-Fi client isolation must be off.

### 2. Configure the game and network

Even when using an emulator, create a **new in-game network configuration** instead of reusing an old one, and set its network fields to **Automatic**. In the emulator's own Ethernet settings, enable Ethernet, choose **Online / Sockets**, and set primary and secondary DNS manually to the Linux computer's LAN IP. In ARMSX2, these are the emulator's Ethernet settings.

For a physical PS2, create a network configuration with a valid PS2 IP and subnet mask, set its gateway to the Linux computer's LAN IP, and set primary DNS to that same Linux IP. Set secondary DNS to the same address if the game requires one.

Use the Linux LAN IP printed by the bridge. Do not enter the remote DHCP address shown by the bridge into the client's LAN settings.

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
