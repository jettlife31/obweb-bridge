# PCSX2 on the same Windows computer

[Guide index](../../README.md) · [English](../en/windows.md) · [Português (Brasil)](../pt-br/windows.md) · [Español](../es/windows.md)

Before starting, complete the [prerequisites](prerequisites.md). Run commands from the application folder.

## 1. Install prerequisites and start the bridge

Close PCSX2 before installing the prerequisites:

1. Install Python 3.10+ following the [Python instructions](prerequisites.md#1-install-python-for-native-use).
2. Download and install [Npcap from its official website](https://npcap.com/#download). It is required for the `obw-pcsx2` adapter to appear in the PCSX2 PCAP list.
3. Download [OpenVPN Community Edition](https://openvpn.net/community/) (not OpenVPN Connect), open the installer and click **Install Now**.

After installing all prerequisites, open PowerShell as Administrator and run:

```powershell
.\start-ethernet.ps1
```

Wait for **READY**, then open PCSX2.

To use a dedicated existing TAP-Windows6 adapter, run `.\start-ethernet.ps1 -Adapter "YOUR TAP ADAPTER"`. Windows gameplay still requires validation.

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

Press Ctrl+C to stop the bridge.

## If the TAP is missing from PCAP

Install [Npcap from its official website](https://npcap.com/#download) separately from OpenVPN. The adapter appearing in Sockets or TAP does not mean that PCAP can capture it. Close PCSX2, leave the bridge running at **READY**, then reopen PCSX2. If Npcap was installed with access restricted to administrators, PCSX2 also needs to run as Administrator.

Use another PowerShell window to inspect the adapter bindings without changing them:

```powershell
Get-NetAdapterBinding -Name "obw-pcsx2" -AllBindings -IncludeHidden | Format-Table DisplayName,ComponentID,Enabled -AutoSize
```

If startup fails, copy the error line identifying the Windows command and error codes. Keep account credentials out of screenshots.

---

Related guides: [Prerequisites: game patch, Python and account](prerequisites.md) · [PCSX2 on the same Linux computer](linux.md) · [ARMSX2 on Android](android.md) · [Physical PlayStation 2](ps2.md) · [Container on Linux](container.md)
