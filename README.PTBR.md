# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

Uma ponte que conecta consoles e emuladores ao Outbreak Web pelo transporte Ethernet via WebSocket. Execute-a no Windows ou no Linux para usar o PCSX2 no mesmo computador, ou use o modo gateway para conectar Android, PS2 real e outros clientes pela LAN. O emulador não precisa ser modificado.

## Índice dos guias

Comece pelos pré-requisitos e depois siga o guia da sua configuração.

**[0. Pré-requisitos](docs/pt-br/prerequisites.md)**

**[Interface gráfica (Windows e Linux)](docs/pt-br/gui.md)**

| Sua configuração | Guia |
|---|---|
| PCSX2 no mesmo computador Windows | [Continuar](docs/pt-br/windows.md) |
| PCSX2 no mesmo computador Linux | [Continuar](docs/pt-br/linux.md) |
| ARMSX2 no Android | [Continuar](docs/pt-br/android.md) |
| PlayStation 2 real | [Continuar](docs/pt-br/ps2.md) |
| Container no Linux | [Continuar](docs/pt-br/container.md) |

O gateway da LAN encaminha os dispositivos da sub-rede selecionada; `OBWEB_CLIENT_IP`, quando informado no container, restringe a um cliente. Partidas simultâneas de vários dispositivos ainda não foram validadas. O modo Ethernet local atende um único emulador por instância.

## Guias relacionados

- [Gateway da LAN](docs/pt-br/lan.md)
- [Diagnóstico (Linux)](docs/pt-br/diagnostics.md)
