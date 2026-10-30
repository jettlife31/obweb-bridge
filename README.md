# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

A bridge that connects consoles and emulators to Outbreak Web over its Ethernet WebSocket transport. Run it on Windows or Linux for PCSX2 on the same computer, or use LAN gateway mode for Android, a physical PS2 and other clients. The emulator does not need to be modified.

## Setup

### 0. Prerequisites

#### Install Python for native use

Install Python 3.10 or newer from the [official Python website](https://www.python.org/downloads/). On Windows, ensure the `py` command is available; reopen PowerShell after installation and check with `py -3 --version`. On Linux, use your distribution's Python packages, including `venv`, as shown below, and check with `python3 --version`.

The launchers use your installed Python and automatically create `.venv` and install the required libraries. The container already includes Python.

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

You can create an account through the bridge launcher. Once registration succeeds, it displays the username, password and REO1 code and generates `outbreak-file1.ps2` and `outbreak-file2.ps2`. Native launches save the cards in `generated-memcards/` inside the application directory.

To import an existing Outbreak Web account:

1. Open **Settings > Online > Show my code** and copy your REO transfer code. Choose **Import** in the bridge login and paste that code.
2. Open **Saves > Export save (.ps2)** to export your memory card with existing progress.

During native import, the launcher asks whether to generate cards and remembers your choice. You can use the card exported from the website. Existing cards for the same account are preserved; when changing the account used by the fixed filenames, previous cards are saved in `generated-memcards/backups/`.

Keep the REO code, password and memory cards private.

### 1. Start the bridge

Choose the mode for your setup:

| Use | Bridge computer OS | Launcher |
|---|---|---|
| PCSX2 on the same computer | Windows | `start-ethernet.ps1` |
| PCSX2 on the same computer | Linux | `start-ethernet.sh` |
| Android, physical PS2 or another PC over LAN | Linux | `start-local.sh` or Docker |

The LAN gateway forwards devices in the selected subnet; setting `OBWEB_CLIENT_IP` in the container restricts it to one client. Simultaneous games from multiple devices have not been validated. Local Ethernet mode serves a single emulator per instance.

#### Local PCSX2 — Windows

Install Python 3.10+ and Npcap. Run the OpenVPN Community installer and select the TAP-Windows6 driver component, which includes `tapctl.exe`. Extracting the MSI alone does not install the driver. If the bridge cannot find `tapctl.exe`, it asks for the file or folder location. Open PowerShell as Administrator and run:

```powershell
.\start-ethernet.ps1
```

To use a dedicated existing TAP-Windows6 adapter, run `.\start-ethernet.ps1 -Adapter "YOUR TAP ADAPTER"`. This mode still requires validation on a Windows host.

#### Local PCSX2 — Linux

Install Python 3.10+, `iproute2`, and TUN/TAP support. On Debian or Ubuntu:

```sh
sudo apt install python3-venv iproute2
./start-ethernet.sh
```

Run the launcher as a regular user; it requests `sudo` to prepare the virtual adapter.

For PCAP with the PCSX2 AppImage, extract it and run the extracted binary with capture permissions. The build we used includes PCAP; capture requires additional permissions. In another terminal, this example assumes `~/Downloads/PCSX2.AppImage` — replace the filename with your download:

```sh
cd "$HOME/Downloads"
./PCSX2.AppImage --appimage-extract
```

After the bridge shows **READY**, launch PCSX2 with:

```bash
sudo -E setpriv --reuid="$(id -u)" --regid="$(id -g)" --init-groups \
  --inh-caps=+net_raw,+net_admin \
  --ambient-caps=+net_raw,+net_admin \
  --no-new-privs \
  env APPDIR="$HOME/Downloads/squashfs-root" \
      LD_LIBRARY_PATH="$HOME/Downloads/squashfs-root/usr/lib" \
      "$HOME/Downloads/squashfs-root/usr/bin/pcsx2-qt"
```

The command uses `setpriv` from `util-linux` and runs PCSX2 as your user with the required network permissions. If you extract elsewhere, adjust all three paths. Configure PCAP as described in step 2.

#### Another device over LAN

LAN gateway mode is available on Linux and through WSL2 on Windows. Install Python 3.10+, `iproute2`, `nftables`, and TUN/TAP support. On Debian or Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
./start-local.sh
```

Run as a regular user. Select the interface connected to the client LAN, such as `enp3s0` or `wlp2s0`; the launcher shows each IPv4 address and requests `sudo` to configure temporary networking. The client must share the LAN, with Wi-Fi client isolation disabled. Use the LAN IP of the computer running the bridge as the client gateway and DNS. For a physical PS2, set these fields in the game as described in step 2.

#### Run the container image

The container provides only the LAN gateway mode and requires Docker Engine on Linux with `--network host`. For PCSX2 on the same computer, use `start-ethernet.sh` on Linux or `start-ethernet.ps1` on Windows.

The container requires `OBWEB_LAN_INTERFACE` (the interface connected to the client LAN) and `OBWEB_USERNAME`. `OBWEB_RUN_MODE` is internal and set automatically. Compose users can pass the same variables under `environment:`.

Before running the image for the first time, identify the interface to use by running the following command to list the available interfaces:

```bash
docker run --rm --network host \
  ghcr.io/zenaror/obweb-bridge:latest --list-interfaces
```

You should see output similar to this:
```text
Available interfaces in the container network namespace:
  enp3s0: 192.168.1.10/24
  wlo1: 192.168.10.183/24
Choose the interface on the client LAN. Use Docker Engine on Linux with --network host.
Docker Desktop may show only VM interfaces; these do not expose the physical LAN to this gateway.
Example: -e OBWEB_LAN_INTERFACE=enp3s0 (replace with the client LAN interface).
```

Docker creates the named volume on first use and keeps it between runs. The network namespace directory is created inside the container.

```bash
docker run --rm --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --device /dev/net/tun:/dev/net/tun \
  --security-opt seccomp=unconfined \
  --mount type=volume,src=obweb-bridge-data,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=enp3s0 \
  -e OBWEB_USERNAME=your_username \
  ghcr.io/zenaror/obweb-bridge:latest
```

Replace `enp3s0` with the name of an interface Docker can use. Omit the REO code to create a new account; the code's username must match `OBWEB_USERNAME`. The container prints the game credentials. An existing username without a matching code produces an error. The `obweb-bridge-data` Docker volume keeps account and cleanup state between runs; add `--cleanup` after the image name to recover from a forced stop.

Add these `-e` flags before the image name only when needed:

- **OPTIONAL** — `-e OBWEB_LAN_IP=192.168.1.10` when the selected interface has multiple local IPv4 addresses.
- **OPTIONAL** — `-e OBWEB_CLIENT_IP=192.168.1.114` to restrict forwarding to one client address.
- **OPTIONAL** — `-e OBWEB_REO_CODE='REO1-username-<32-hex-characters>'` to import an existing account using the complete code from **Settings > Online > Show my code**.
- **OPTIONAL** — `-e OBWEB_WSS_URL=wss://outbreakweb.com/eth` to override the default WSS endpoint.
- **OPTIONAL** — `-e OBWEB_WSS_ORIGIN=https://outbreakweb.com` to override the default WSS origin.
- **OPTIONAL** — `-e OBWEB_RUNTIME_DIR=/var/lib/obweb-bridge/runtime` to change the runtime state path; keep it inside `/var/lib/obweb-bridge` so the Docker volume persists it.

In Docker, MCs are generated only when creating a new account. Importing with `OBWEB_REO_CODE` or reusing a saved account does not generate new cards. Generated files are stored in the persistent volume; the logs show their paths and copy commands. For example, while the container is running:

```bash
docker cp CONTAINER_NAME:/var/lib/obweb-bridge/state/outbreak-web-login/memcards/outbreak-file1.ps2 ./outbreak-file1.ps2
docker cp CONTAINER_NAME:/var/lib/obweb-bridge/state/outbreak-web-login/memcards/outbreak-file2.ps2 ./outbreak-file2.ps2
```

Replace `CONTAINER_NAME` with the name shown by `docker ps` and use the paths printed in the logs.

The launchers ask for a username or REO code and display the username, game password and REO1 transfer code; use environment variables in the container. Wait for **READY** before connecting. Keep the credentials private.

### 2. Configure the game and network

Before configuring the network, select the memory card for the same account in your emulator: `outbreak-file1.ps2` for Outbreak or `outbreak-file2.ps2` for File #2. If you imported an account and declined card generation, use your exported memory card.

Even when using an emulator, create a **new in-game network configuration** instead of reusing an old one, and set its network fields to **Automatic**.

#### ARMSX2 on Android and PS2 consoles

Enable Ethernet, choose **Online / Sockets**, and manually enter the LAN IP of the computer running the bridge as primary and secondary DNS (remember to set them to MANUAL rather than AUTO). You also need to set your Android Wi-Fi connection to STATIC as follows:

- **IP address:** an unused address on the same LAN as the computer running the bridge. Do not use the bridge computer's IP.
- **Subnet mask:** the mask used by your LAN (commonly `255.255.255.0` for a `/24` network).
- **Gateway:** the LAN IP of the computer running the bridge, shown by the bridge.
- **Primary DNS (DNS1):** the same LAN IP of the computer running the bridge.
- **Secondary DNS (DNS2):** use the LAN IP of the computer running the bridge if the configuration requires a value.

On a physical PS2, create a new network configuration in the game's Network Play setup and manually enter the addresses described above. Save the profile and select it for Network Play.

#### PCSX2 on the same computer as the bridge

Use the dedicated virtual adapter created by the launcher, using `start-ethernet`. Wait for **READY**, then open or restart PCSX2 to refresh the device list. In **Settings > Network & HDD**:

- Enable Ethernet and select **PCAP Switched** (**PCAP Trocado** in some translations).
- Select **obw-pcsx2** or the dedicated TAP adapter selected on Windows.
- Disable **Intercept DHCP**. Set DNS modes to **Automatic** and disable custom internal DNS entries.
- Create a new in-game network profile with all fields **Automatic**.

Remote DHCP supplies the PS2 IP, subnet, gateway and DNS. Leave those fields automatic in this mode. The launcher configures the virtual adapter; use a dedicated TAP rather than a physical adapter or a TAP used by a VPN.

Keep the bridge open while playing. An adapter created by the launcher is removed on shutdown; an existing Windows TAP is retained.

### 3. Play

Use the patched image and the memory card for the same account, boot the game from a full start, choose NETWORK PLAY and then **Go Online**, and enter the password from the login helper. The bridge can stay open without players, with no duration or inactivity limit. If WSS disconnects, it automatically retries; an active match may need to be reconnected in the game.

Press Ctrl+C to stop the bridge. If you used gateway mode, restore the client gateway and DNS when finished.

## Diagnostics (Linux)

With the bridge running, use another terminal:

```sh
sudo .venv/bin/python diagnose.py --lan-interface INTERFACE --pcsx2-ip PS2_IP --seconds 45
```

For local Ethernet mode, use the PS2 IP assigned by remote DHCP, visible in the game network settings. The diagnostic monitors only `obw-pcsx2` for that guest IP and reports link counters and protocol metadata without recording payloads, MAC addresses, DNS names, credentials, or IP addresses. To show only the DNS question names in the terminal for this PS2 capture, explicitly add `--show-dns-names`; this does not save them. For a separate LAN client, omit `--pcsx2-ip` and use `--client-ip CLIENT_IP` to limit the capture to that device.
