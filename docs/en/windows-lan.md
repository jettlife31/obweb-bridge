# Native Windows LAN gateway — experimental

[Guide index](../../README.md) · [English](../en/windows-lan.md) · [Português (Brasil)](../pt-br/windows-lan.md) · [Español](../es/windows-lan.md)

This **experimental** mode connects Android, a physical PS2 or another LAN computer without WSL or containers. Compatibility can vary with the network adapter and driver. For PCSX2 on this computer, keep using the proven [local Ethernet mode](windows.md).

## 1. Prepare Windows

Complete the [prerequisites](prerequisites.md), install 64-bit Python and install [Npcap separately](https://npcap.com/#download). Download the official [WinDivert 2.2 x64 package](https://github.com/basil00/WinDivert/releases/tag/v2.2.2). Keep `WinDivert.dll` and its signed `WinDivert64.sys` together in the application's `third_party/WinDivert/x64` folder, or select the DLL when asked. The application does not download or redistribute these drivers. OpenVPN is needed for local PCSX2 Ethernet mode only.

Leave Windows Internet Connection Sharing and IP forwarding disabled on the selected interface. Do not change the PC's own gateway, DNS or routes.

## 2. Start the GUI

Run `start-gui.ps1` as your regular user. If PowerShell blocks the script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-gui.ps1
```

In **Connection**, choose **Another device on the LAN** and the physical interface connected to your clients. Click **Start bridge**, approve the network helper's administrator prompt and locate `WinDivert.dll` if asked. **Ready** confirms local capture is open; increasing sent/received counters confirms the WSS data path.

## 3. Connect a client

The PC and client must share the same LAN with client isolation disabled. Configure the client's gateway and DNS as the PC IP shown by the GUI; use a free client IP and the LAN subnet mask. Follow the [Android](android.md) or [PS2](ps2.md) guide for the rest of the setup. Keep using the patched ISO and matching account/save. Account preparation in the bridge remains optional.

This endpoint captures only client Ethernet addressed to the PC as gateway and local DNS requests. Npcap carries frames; WinDivert prevents conflicting Windows DNS and routing-error replies. The endpoint adds no adapter, route, DNS setting or persistent firewall rule and does not enable Windows IP forwarding. Host Internet traffic is excluded. Each client gets separate WSS paths for forwarded IPv4 and DNS, with automatic reconnect and DHCP renewal. Up to 32 client addresses are retained until Stop; simultaneous gameplay is not validated. Fragmented local DNS requests are currently unsupported; ordinary UDP/TCP DNS and forwarded IPv4 fragments are implemented.

## 4. Stop or report a failure

Use **Stop** or close the GUI and wait for the helper to exit. Handles are closed without a network restoration step because host settings are never changed. If Windows Firewall or the NIC driver prevents capture/injection, do not disable the entire firewall: share **Copy diagnostic report**, the selected interface type and the client setup. Counters alone do not prove a game session works.

[Back to desktop setup](gui.md) · [Linux LAN gateway](lan.md)
