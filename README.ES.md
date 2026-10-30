# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

Un bridge que conecta consolas y emuladores a Outbreak Web mediante su transporte Ethernet sobre WebSocket. Ejecútalo en Windows o Linux para usar PCSX2 en el mismo equipo, o usa el modo gateway LAN para Android, una PS2 real y otros clientes. No hace falta modificar el emulador.

## Índice de guías

Empieza por los requisitos previos y sigue la guía de tu configuración.

**[0. Requisitos previos](docs/es/prerequisites.md)**

| Tu configuración | Guía |
|---|---|
| PCSX2 en el mismo equipo Windows | [Continuar](docs/es/windows.md) |
| PCSX2 en el mismo equipo Linux | [Continuar](docs/es/linux.md) |
| ARMSX2 en Android | [Continuar](docs/es/android.md) |
| PlayStation 2 real | [Continuar](docs/es/ps2.md) |
| Contenedor en Linux | [Continuar](docs/es/container.md) |

El gateway LAN reenvía los dispositivos de la subred seleccionada; `OBWEB_CLIENT_IP` en el contenedor lo restringe a un cliente. Todavía no se han validado partidas simultáneas de varios dispositivos. El modo Ethernet local atiende un solo emulador por instancia.

## Guías relacionadas

- [Gateway LAN](docs/es/lan.md)
- [Diagnóstico (Linux)](docs/es/diagnostics.md)
