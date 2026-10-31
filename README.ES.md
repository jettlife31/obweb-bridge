# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

Un bridge que conecta consolas y emuladores a Outbreak Web mediante su transporte Ethernet sobre WebSocket. Ejecútalo en Windows o Linux para usar PCSX2 en el mismo equipo, o ejecuta el gateway en Linux nativo o en un contenedor Linux para Android, una PS2 real y otros clientes. No hace falta modificar el emulador.


Las herramientas de cuenta y memory cards son opcionales. El bridge inicia de forma independiente; tu cuenta se utiliza al entrar en el juego.

## Compatibilidad actual

| Versión del bridge | PCSX2 en el mismo equipo | Android / ARMSX2 por LAN | PS2 real por LAN | Otro PC por LAN |
|---|---|---|---|---|
| Linux nativo | Sí | Sí | Sí | Sí |
| Contenedor en Linux | No | Sí | Sí | Sí |
| Windows nativo | Sí | No | No | No |
| LAN Windows (experimental) | — | Validación pendiente | Validación pendiente | Validación pendiente |

El backend LAN experimental para Windows está disponible en esta branch; consulta la [guía LAN nativa en Windows](docs/es/windows-lan.md). Todavía requiere validación de hardware y partidas en Windows.

El contenedor solo ofrece el gateway LAN y requiere Docker Engine en Linux. Docker Desktop en Windows no está soportado para este modo.

## Índice de guías

Empieza por los requisitos previos y sigue la guía de tu configuración.

Usa la **GUI como opción predeterminada** en Windows y Linux. El contenedor usa comandos de terminal; los iniciadores nativos de terminal siguen en Otras formas de ejecutar.

**[0. Requisitos previos](docs/es/prerequisites.md)**

**[Interfaz gráfica (Windows y Linux)](docs/es/gui.md)**

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

- [Otras formas de ejecutar](docs/es/terminal.md)

- [Gateway LAN nativo en Windows — experimental](docs/es/windows-lan.md)
