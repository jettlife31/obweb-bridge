# Desktop GUI — Windows and Linux

[Guide index](../../README.md) · [English](../en/gui.md) · [Português (Brasil)](../pt-br/gui.md) · [Español](../es/gui.md)

The GUI is the default for native Windows and Linux. The same Python window controls both systems; terminal launchers remain under [Other ways to run](terminal.md). The container does not use the GUI.


Windows also offers **Another device on the LAN** as an experimental mode with Npcap + WinDivert; use the [Windows LAN guide](windows-lan.md). The Linux LAN and local Ethernet modes retain their existing setup.

Use **Patch game** to prepare your original USA ISO before playing. It recognizes both supported games by SHA-256 and verifies the patched copy without requiring xdelta3. See [game patch prerequisites](prerequisites.md#2-patch-your-game-image) for supported revisions and hashes.

## 1. Install prerequisites

Complete the [game patch and account prerequisites](prerequisites.md).

- **Windows:** install Python from its official website, [Npcap](https://npcap.com/#download) separately, and [OpenVPN Community](https://openvpn.net/community/) using **Install Now**. OpenVPN Connect is a different product.
- **Linux:**

On Linux, give the launcher **execute** permission once with `chmod +x start-gui.sh`. Then open it with your file manager and choose **Run** or **Run in Terminal**, if offered. Some file managers require enabling executable scripts in their preferences. The terminal command below always remains available. install Tkinter and a desktop authorization agent in addition to the dependencies for your bridge mode. On Debian/Ubuntu:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1
```

## 2. Open the application

Run from the application folder as your regular user. Network setup requests administrator approval separately.

**Windows:**

Double-click **start-gui.bat** in the application folder as a regular user. It opens PowerShell with `-ExecutionPolicy Bypass` for that process only. You can also start it manually from PowerShell:

```powershell
.\start-gui.ps1
```

If the execution policy blocks the launcher, use:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-gui.ps1
```

**Linux:**

On Linux, give the launcher **execute** permission once with `chmod +x start-gui.sh`. Then open it with your file manager and choose **Run** or **Run in Terminal**, if offered. Some file managers require enabling executable scripts in their preferences. The terminal command below always remains available.

```sh
chmod +x start-gui.sh
./start-gui.sh
```

The launchers prepare `.venv` and install the Python libraries automatically. Use **Setup** to check dependencies and open their official download pages.

### Permission errors from earlier administrator runs

Run the GUI as a **regular user on both Windows and Linux**: do not use Run as Administrator for the GUI on Windows or sudo for the GUI on Linux. Approve elevation only for the network helper after clicking **Start bridge**.

Account files or memory-card folders created earlier as Administrator/root or under another user can cause **PermissionError** when the GUI later runs as a regular user. The error dialog identifies the affected path. Preserve your REO1 code and saved files, and correct access only for that application folder/file for your current user. Do not delete the entire `.local` directory or change permissions for unrelated folders. See also the [native Windows setup](windows.md).

## 3. Prepare the account (optional)

Account setup is independent of packet forwarding. You can click **Start bridge** directly without opening this tab or loading saved credentials. Use these optional tools only to create/import an account, view its login details or generate memory cards. The game still requires its own valid account and matching save.

In **Account & memory cards**, select a saved account, create a new username or paste an existing REO1 code. Click **Prepare account**. The code remains visible while pasting.

New accounts generate the two memory cards automatically. On import, select **Generate memory cards when importing this account** only if needed. Existing progress is preserved according to the [account rules](prerequisites.md). The window shows the username, game password, REO1 code and card paths, with copy buttons. Keep these details private.

With **Saved account** selected, click **Create memory cards** to generate cards for that account without importing it again. This works offline and preserves existing cards and progress. **Open memory-card folder** opens the system file manager. **Open credentials folder** opens the folder containing the saved account file (`identities.json`).

## 4. Connect

In **Connection**, choose:

- **PCSX2 on this computer:** available on Windows and Linux. Use the [Windows](windows.md) or [Linux](linux.md) guide for the emulator settings: **PCAP Switched**, `obw-pcsx2`, DHCP interception off, automatic DNS and a new automatic in-game profile.
- **Another device on the LAN:** Linux hosting is validated; experimental Windows hosting uses the [Windows LAN guide](windows-lan.md). Select the interface connected to the clients; the window shows the gateway/DNS IP after startup. Configure [Android](android.md), a [physical PS2](ps2.md) or another LAN client following the [gateway guide](lan.md).

On Windows, an existing dedicated TAP name is optional. If `tapctl.exe` cannot be found, a file picker asks for it.

Click **Start bridge** and approve the system prompt. Wait for **Ready** before connecting the game. Use your matching memory card and game password; showing them in the account tab is optional.

## 5. Stop and diagnose

**Stop** and closing the window request the same network cleanup. The window waits for the worker to exit; do not force-close it while cleanup is running. No session or idle shutdown is imposed.

Connection status and counters appear in the activity area. **Copy diagnostic report** copies platform information and activity messages, excluding the account fields.

During Stop, the activity log distinguishes command delivery, acknowledgement by the network worker, driver cancellation and adapter removal. If it remains stuck, use **Copy diagnostic report** after the waiting messages appear. It includes the worker PID, code fingerprints, current phase, heartbeat ages and application function locations, without packet contents, account data or local variables.

The report also identifies the command receiver and which Stop signal the worker recognized. Windows has an additional per-session native Stop signal independent of the TCP control channel; both request the same cleanup.
