# LAN gateway

[Guide index](../../README.md) · [English](../en/lan.md) · [Português (Brasil)](../pt-br/lan.md) · [Español](../es/lan.md)

Before starting, complete the [prerequisites](prerequisites.md). Run commands from the application folder.

## 1. Start a LAN gateway

The GUI LAN gateway uses the Linux backend. Native Linux is supported; Windows can launch it through **experimental WSL 2 integration**, described below. On native Linux, install the dependencies and run the GUI as your regular user:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps pkexec polkitd
./start-gui.sh
```

In **Connection**, select **Another device on the LAN**, choose the interface connected to the clients and prepare the account. Click **Start bridge**, approve network authorization and wait for **Ready**. The window shows the client gateway/DNS IP. Do not change the bridge computer's own gateway or DNS. Clients must share its LAN, with Wi-Fi client isolation disabled.

## Windows via WSL 2 (experimental)

The Windows GUI can detect WSL, list installed distributions and launch the Linux gateway in a selected distribution. This has not been validated with LAN clients on Windows. **WSL backend ready does not confirm that console/Android traffic reaches it.** Native Linux remains the validated LAN host.

1. Install and initialize a Linux distribution under your regular Windows account using the [official WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install). The GUI reports missing WSL or distributions; it does not install Windows features or reboot.
2. Use Windows 11 22H2+ with updated WSL 2 and active **mirrored networking**, following [Microsoft's networking guide](https://learn.microsoft.com/en-us/windows/wsl/networking). The default NAT mode is blocked for this workflow. Merely editing `.wslconfig` is insufficient until WSL applies it; restarting WSL interrupts its running applications.
3. In the distribution, install Python 3.10+ and the Linux dependencies. For Ubuntu:

```sh
sudo apt install python3 python3-venv python3-pip iproute2 nftables procps
```

4. Open the Windows GUI normally. Select **Another device on the LAN**, select the **WSL distribution**, then click **Prepare WSL**. This creates `.venv-wsl` next to the application files and installs the Python libraries as the distribution's default user. Keep the distribution's default user unprivileged. The Windows `.venv` is not reused. **Refresh** repeats the checks without installing anything.
5. Select the client LAN interface returned by WSL, prepare your account and click **Start bridge**. Only the network helper runs as Linux root. **Stop** waits for its cleanup; it does not shut down your distribution. Account and memory-card files remain managed by the Windows GUI.

The checks cover active mirrored mode, dependencies and IPv4 interfaces. They do **not** verify forwarding of arbitrary LAN packets through Windows/Hyper-V into WSL. The app does not change Windows routing, WSL networking mode or firewall rules. If the backend starts but client counters stay at zero, the Windows-to-WSL packet path still needs investigation; DNS reachability alone is insufficient. Do not redirect the bridge computer's own Internet traffic or use game-specific port-forwarding rules as a workaround. Use [native Linux](#1-start-a-lan-gateway) when you need the validated LAN setup.

## 2. Continue

Continue with [Android / ARMSX2](android.md) or [physical PS2](ps2.md). For another computer over LAN, set its network gateway and DNS to the bridge computer and select Sockets in the emulator.

For counters and protocol metadata on a Linux bridge, see [Diagnostics](diagnostics.md).

For the older terminal launchers, see [Other ways to run](terminal.md).

---

Related guides: [Prerequisites: game patch, Python and account](prerequisites.md) · [PCSX2 on the same Windows computer](windows.md) · [PCSX2 on the same Linux computer](linux.md) · [ARMSX2 on Android](android.md) · [Physical PlayStation 2](ps2.md) · [Container on Linux](container.md)
