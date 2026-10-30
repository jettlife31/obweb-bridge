# Physical PlayStation 2

[Guide index](../../README.md) · [English](../en/ps2.md) · [Português (Brasil)](../pt-br/ps2.md) · [Español](../es/ps2.md)

Before starting, complete the [prerequisites](prerequisites.md). Run commands from the application folder.

## 1. Start a LAN gateway

First [start the LAN gateway](lan.md), either natively or with the [container](container.md). Wait for **READY** before changing the client network.

## 2. Select the memory card

Use a physical memory card containing the account save for the same Outbreak Web account. If it was prepared on a PC, transfer the save using your PS2 memory-card tools.

## 3. Configure the physical PS2

Connect the PS2 to the same LAN as the bridge computer. In the game, create a new network configuration under **Network Play**, enter these fields manually, save it and select it for Network Play.

- **IP address:** an unused address on the same LAN as the computer running the bridge. Do not use the bridge computer's IP.
- **Subnet mask:** the mask used by your LAN (commonly `255.255.255.0` for a `/24` network).
- **Gateway:** the LAN IP of the computer running the bridge, shown by the bridge.
- **Primary DNS (DNS1):** the same LAN IP of the computer running the bridge.
- **Secondary DNS (DNS2):** use the LAN IP of the computer running the bridge if the configuration requires a value.

## 4. Play and stop the bridge

Use the patched image and the memory card for the same account, boot the game from a full start, choose NETWORK PLAY and then **Go Online**, and enter the password from the login helper. The bridge can stay open without players, with no duration or inactivity limit. If WSS disconnects, it automatically retries; an active match may need to be reconnected in the game.

Press Ctrl+C to stop the bridge. If you used gateway mode, restore the client gateway and DNS when finished.

---

Related guides: [Prerequisites: game patch, Python and account](prerequisites.md) · [PCSX2 on the same Windows computer](windows.md) · [PCSX2 on the same Linux computer](linux.md) · [ARMSX2 on Android](android.md) · [Container on Linux](container.md)
