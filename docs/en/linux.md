# PCSX2 on the same Linux computer

[Guide index](../../README.md) · [English](../en/linux.md) · [Português (Brasil)](../pt-br/linux.md) · [Español](../es/linux.md)

Before starting, complete the [prerequisites](prerequisites.md). Run commands from the application folder.

## 1. Install prerequisites and start the bridge

Install Python 3.10+, Tkinter, `iproute2`, TUN/TAP support and a desktop authorization agent. On Debian/Ubuntu:

```sh
sudo apt install python3-venv python3-tk iproute2 policykit-1
./start-gui.sh
```

Run the GUI as your regular user, without sudo. Select **PCSX2 on this computer**, prepare the account and click **Start bridge**. The network helper requests authorization separately.

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

## 2. Select the memory card

Before configuring the network, select the memory card for the same account in your emulator: `outbreak-file1.ps2` for Outbreak or `outbreak-file2.ps2` for File #2. If you imported an account and declined card generation, use your exported memory card.

## 3. Configure PCSX2

In **Settings > Network & HDD**:

- Enable Ethernet and select **PCAP Switched** (**PCAP Trocado** in some translations).
- Select **obw-pcsx2** or the dedicated TAP adapter selected on Windows.
- Disable **Intercept DHCP**. Set DNS modes to **Automatic** and disable custom internal DNS entries.
- Create a new in-game network profile with all fields **Automatic**.

Remote DHCP supplies the PS2 IP, subnet, gateway and DNS. Leave those fields automatic in this mode. The launcher configures the virtual adapter; use a dedicated TAP rather than a physical adapter or a TAP used by a VPN.

Keep the bridge open while playing. An adapter created by the launcher is removed on shutdown; an existing Windows TAP is retained.

## 4. Play and stop the bridge

Use the patched image and the memory card for the same account, boot the game from a full start, choose NETWORK PLAY and then **Go Online**, and enter the password from the login helper. The bridge can stay open without players, with no duration or inactivity limit. If WSS disconnects, it automatically retries; an active match may need to be reconnected in the game.

Click **Stop** or close the window to stop the bridge.

For counters and protocol metadata on a Linux bridge, see [Diagnostics](diagnostics.md).

For the older terminal launchers, see [Other ways to run](terminal.md).

---

Related guides: [Prerequisites: game patch, Python and account](prerequisites.md) · [PCSX2 on the same Windows computer](windows.md) · [ARMSX2 on Android](android.md) · [Physical PlayStation 2](ps2.md) · [Container on Linux](container.md)
