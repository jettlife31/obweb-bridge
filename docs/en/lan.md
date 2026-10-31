# LAN gateway

[Guide index](../../README.md) · [English](../en/lan.md) · [Português (Brasil)](../pt-br/lan.md) · [Español](../es/lan.md)

Before starting, complete the [prerequisites](prerequisites.md). Run commands from the application folder.


For the experimental Windows host backend, follow [Native Windows LAN gateway](windows-lan.md). The Linux instructions below remain unchanged.
## 1. Start a LAN gateway

The GUI LAN gateway host requires Linux. Install the dependencies, then run the GUI as your regular user:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1
./start-gui.sh
```

In **Connection**, select **Another device on the LAN**, choose the interface connected to the clients. Click **Start bridge**, approve network authorization and wait for **Ready**. The window shows the client gateway/DNS IP. Do not change the bridge computer's own gateway or DNS. Clients must share its LAN, with Wi-Fi client isolation disabled.

## 2. Continue

Continue with [Android / ARMSX2](android.md) or [physical PS2](ps2.md). For another computer over LAN, set its network gateway and DNS to the bridge computer and select Sockets in the emulator.

For counters and protocol metadata on a Linux bridge, see [Diagnostics](diagnostics.md).

For the older terminal launchers, see [Other ways to run](terminal.md).

---

Related guides: [Prerequisites: game patch, Python and account](prerequisites.md) · [PCSX2 on the same Windows computer](windows.md) · [PCSX2 on the same Linux computer](linux.md) · [ARMSX2 on Android](android.md) · [Physical PlayStation 2](ps2.md) · [Container on Linux](container.md)
