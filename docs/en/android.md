# ARMSX2 on Android

[Guide index](../../README.md) · [English](../en/android.md) · [Português (Brasil)](../pt-br/android.md) · [Español](../es/android.md)

Before starting, complete the [prerequisites](prerequisites.md). Run commands from the application folder.

## 1. Start a LAN gateway

First [start the LAN gateway](lan.md), either natively or with the [container](container.md). Wait for **READY** before changing the client network.

## 2. Select the memory card

Before configuring the network, select the memory card for the same account in your emulator: `outbreak-file1.ps2` for Outbreak or `outbreak-file2.ps2` for File #2. If you imported an account and declined card generation, use your exported memory card.

Even when using an emulator, create a **new in-game network configuration** instead of reusing an old one, and set its network fields to **Automatic**.

## 3. Configure Android and ARMSX2

Enable Ethernet, choose **Online / Sockets**, and manually enter the LAN IP of the computer running the bridge as primary and secondary DNS (remember to set them to MANUAL rather than AUTO). You also need to set your Android Wi-Fi connection to STATIC as follows:

- **IP address:** an unused address on the same LAN as the computer running the bridge. Do not use the bridge computer's IP.
- **Subnet mask:** the mask used by your LAN (commonly `255.255.255.0` for a `/24` network).
- **Gateway:** the LAN IP of the computer running the bridge, shown by the bridge.
- **Primary DNS (DNS1):** the same LAN IP of the computer running the bridge.
- **Secondary DNS (DNS2):** use the LAN IP of the computer running the bridge if the configuration requires a value.

## 4. Play and stop the bridge

Use the patched image and the memory card for the same account, boot the game from a full start, choose NETWORK PLAY and then **Go Online**, and enter the password from the login helper. The bridge can stay open without players, with no duration or inactivity limit. If WSS disconnects, it automatically retries; an active match may need to be reconnected in the game.

Press Ctrl+C to stop the bridge. If you used gateway mode, restore the client gateway and DNS when finished.

---

Related guides: [Prerequisites: game patch, Python and account](prerequisites.md) · [PCSX2 on the same Windows computer](windows.md) · [PCSX2 on the same Linux computer](linux.md) · [Physical PlayStation 2](ps2.md) · [Container on Linux](container.md)
