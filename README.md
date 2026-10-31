# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

A bridge that connects consoles and emulators to Outbreak Web over its Ethernet WebSocket transport. Run it on Windows or Linux for PCSX2 on the same computer or for LAN clients such as Android and a physical PS2. The Windows LAN gateway is experimental; Linux also supports the gateway in a container. The emulator does not need to be modified.


Account and memory-card tools are optional. The bridge starts independently; your account is used when logging into the game.

## Current support

| Bridge version | PCSX2 on the same computer | Android / ARMSX2 over LAN | Physical PS2 over LAN | Another PC over LAN |
|---|---|---|---|---|
| Native Linux | Yes | Yes | Yes | Yes |
| Container on Linux | No | Yes | Yes | Yes |
| Native Windows | Yes | Experimental | Experimental | Experimental |

The native Windows LAN gateway remains **experimental**; see the [Windows LAN guide](docs/en/windows-lan.md).

The container provides only the LAN gateway and requires Docker Engine on Linux. Docker Desktop on Windows is not supported for this mode.

## Guide index

Start with the prerequisites, then follow the guide for your setup.

Use the **GUI by default** on Windows and Linux. The container uses terminal commands; native terminal launchers remain under Other ways to run.

**[0. Prerequisites](docs/en/prerequisites.md)**

**[Desktop GUI (Windows and Linux)](docs/en/gui.md)**

| Your setup | Guide |
|---|---|
| PCSX2 on the same Windows computer | [Continue](docs/en/windows.md) |
| PCSX2 on the same Linux computer | [Continue](docs/en/linux.md) |
| ARMSX2 on Android | [Continue](docs/en/android.md) |
| Physical PlayStation 2 | [Continue](docs/en/ps2.md) |
| Container on Linux | [Continue](docs/en/container.md) |

The LAN gateway forwards devices in the selected subnet; setting `OBWEB_CLIENT_IP` in the container restricts it to one client. Simultaneous games from multiple devices have not been validated. Local Ethernet mode serves a single emulator per instance.

## Related guides

- [LAN gateway](docs/en/lan.md)
- [Diagnostics (Linux)](docs/en/diagnostics.md)

- [Other ways to run](docs/en/terminal.md)

- [Experimental native Windows LAN gateway](docs/en/windows-lan.md)
