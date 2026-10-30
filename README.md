# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

A bridge that connects consoles and emulators to Outbreak Web over its Ethernet WebSocket transport. Run it on Windows or Linux for PCSX2 on the same computer, or use LAN gateway mode for Android, a physical PS2 and other clients. The emulator does not need to be modified.

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
