# LAN gateway

[Guide index](../../README.md) · [English](../en/lan.md) · [Português (Brasil)](../pt-br/lan.md) · [Español](../es/lan.md)

Before starting, complete the [prerequisites](prerequisites.md). Run commands from the application folder.

## 1. Start a LAN gateway

LAN gateway mode is available on Linux and through WSL2 on Windows. Install Python 3.10+, `iproute2`, `nftables`, and TUN/TAP support. On Debian or Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
./start-local.sh
```

Run as a regular user. Select the interface connected to the client LAN, such as `enp3s0` or `wlp2s0`; the launcher shows each IPv4 address and requests `sudo` to configure temporary networking. The client must share the LAN, with Wi-Fi client isolation disabled. Use the LAN IP of the computer running the bridge as the client gateway and DNS. For a physical PS2, set these fields in the game as described in the client guide.

## 2. Continue

Continue with [Android / ARMSX2](android.md) or [physical PS2](ps2.md). For another computer over LAN, set its network gateway and DNS to the bridge computer and select Sockets in the emulator.

For counters and protocol metadata on a Linux bridge, see [Diagnostics](diagnostics.md).

---

Related guides: [Prerequisites: game patch, Python and account](prerequisites.md) · [PCSX2 on the same Windows computer](windows.md) · [PCSX2 on the same Linux computer](linux.md) · [ARMSX2 on Android](android.md) · [Physical PlayStation 2](ps2.md) · [Container on Linux](container.md)
