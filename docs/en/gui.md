# Desktop GUI — Windows and Linux

[Guide index](../../README.md) · [English](../en/gui.md) · [Português (Brasil)](../pt-br/gui.md) · [Español](../es/gui.md)

The same Python window controls both systems. Existing terminal launchers remain available. The container does not use the GUI.

## 1. Install prerequisites

Complete the [game patch and account prerequisites](prerequisites.md).

- **Windows:** install Python from its official website, [Npcap](https://npcap.com/#download) separately, and [OpenVPN Community](https://openvpn.net/community/) using **Install Now**. OpenVPN Connect is a different product.
- **Linux:** install Tkinter and a desktop authorization agent in addition to the dependencies for your bridge mode. On Debian/Ubuntu:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1
```

## 2. Open the application

Run from the application folder as your regular user. Network setup requests administrator approval separately.

**Windows — PowerShell:**

```powershell
.\start-gui.ps1
```

If the execution policy blocks the launcher, use:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-gui.ps1
```

**Linux:**

```sh
./start-gui.sh
```

The launchers prepare `.venv` and install the Python libraries automatically. Use **Setup** to check dependencies and open their official download pages.

## 3. Prepare the account

In **Account & memory cards**, select a saved account, create a new username or paste an existing REO1 code. Click **Prepare account**. The code remains visible while pasting.

New accounts generate the two memory cards automatically. On import, select **Generate memory cards when importing this account** only if needed. Existing progress is preserved according to the [account rules](prerequisites.md). The window shows the username, game password, REO1 code and card paths, with copy buttons. Keep these details private.

With **Saved account** selected, click **Create memory cards** to generate cards for that account without importing it again. This works offline and preserves existing cards and progress. **Open memory-card folder** opens the system file manager.

## 4. Connect

In **Connection**, choose:

- **PCSX2 on this computer:** available on Windows and Linux. Use the [Windows](windows.md) or [Linux](linux.md) guide for the emulator settings: **PCAP Switched**, `obw-pcsx2`, DHCP interception off, automatic DNS and a new automatic in-game profile.
- **Another device on the LAN:** hosting currently requires Linux. Select the interface connected to the clients; the window shows the gateway/DNS IP after startup. Configure [Android](android.md), a [physical PS2](ps2.md) or another LAN client following the [gateway guide](lan.md).

On Windows, an existing dedicated TAP name is optional. If `tapctl.exe` cannot be found, a file picker asks for it.

Click **Start bridge** and approve the system prompt. Wait for **Ready** before connecting the game. Use the matching memory card and the game password shown in the account tab.

## 5. Stop and diagnose

**Stop** and closing the window request the same network cleanup. The window waits for the worker to exit; do not force-close it while cleanup is running. No session or idle shutdown is imposed.

Connection status and counters appear in the activity area. **Copy diagnostic report** copies platform information and activity messages, excluding the account fields. Windows gameplay and elevation still need runtime validation; Linux UI and isolated worker cleanup have been checked. This is a development branch, not a replacement for the existing launchers.
