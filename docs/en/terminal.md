# Other ways to run

[Guide index](../../README.md) · [English](../en/terminal.md) · [Português (Brasil)](../pt-br/terminal.md) · [Español](../es/terminal.md)

The [desktop GUI](gui.md) is the default for native Windows and Linux. These terminal launchers remain available as alternatives. For a container without a GUI, follow the [container guide](container.md). Run commands from the application folder.


The account menu is optional: press **Enter** or **S** to skip it and start the bridge, **N** to create an account, **I** to import a REO1 code, or **V** to view the last saved account. Skipping does not read saved credentials or contact the account service. You still log into the game with your own account.

## Windows — terminal

Close PCSX2 before installing the prerequisites:

1. Install Python 3.10+ following the [Python instructions](prerequisites.md#1-install-python-for-native-use).
2. Download and install [Npcap from its official website](https://npcap.com/#download). It is required for the `obw-pcsx2` adapter to appear in the PCSX2 PCAP list.
3. Download [OpenVPN Community Edition](https://openvpn.net/community/) (not OpenVPN Connect), open the installer and click **Install Now**.

After installing all prerequisites, open PowerShell as Administrator and run:

```powershell
.\start-ethernet.ps1
```

If PowerShell blocks the script because of its execution policy, run this alternative from the same Administrator terminal. It applies to this process only and does not permanently change the system policy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-ethernet.ps1
```

Wait for **READY**, then open PCSX2.

To use a dedicated existing TAP-Windows6 adapter, run `.\start-ethernet.ps1 -Adapter "YOUR TAP ADAPTER"`. Windows gameplay still requires validation.

## Linux — terminal

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

The command uses `setpriv` from `util-linux` and runs PCSX2 as your user with the required network permissions. If you extract elsewhere, adjust all three paths. Configure PCAP as described below.

## LAN gateway — terminal

LAN gateway mode is available on Linux and through WSL2 on Windows. Install Python 3.10+, `iproute2`, `nftables`, and TUN/TAP support. On Debian or Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
./start-local.sh
```

Run as a regular user. Select the interface connected to the client LAN, such as `enp3s0` or `wlp2s0`; the launcher shows each IPv4 address and requests `sudo` to configure temporary networking. The client must share the LAN, with Wi-Fi client isolation disabled. Use the LAN IP of the computer running the bridge as the client gateway and DNS. For a physical PS2, set these fields in the game as described in the client guide.

For the emulator settings, use the [Windows](windows.md) or [Linux](linux.md) guide. For a separate client, follow [Android](android.md) or [physical PS2](ps2.md). Stop terminal sessions with Ctrl+C.
