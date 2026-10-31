# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

Uma ponte que conecta consoles e emuladores ao Outbreak Web pelo transporte Ethernet via WebSocket. Execute-a no Windows ou no Linux para usar o PCSX2 no mesmo computador ou conectar Android, PS2 real e outros clientes pela LAN. O gateway LAN do Windows é experimental; no Linux, o gateway também pode rodar em container. O emulador não precisa ser modificado.


As ferramentas de conta e memory cards são opcionais. A ponte inicia de forma independente; sua conta é usada no login dentro do jogo.

## Compatibilidade atual

| Versão da ponte | Emulador no mesmo computador | Outro dispositivo* pela LAN |
| --- | --- | --- |
| Linux nativo | Sim | Sim |
| Container no Linux | Não | Sim |
| Windows nativo | Sim | Experimental |

*Testado com PC (PCSX2 no Windows e Linux), Android (ARMSX2) e console PS2 real.

O gateway LAN nativo do Windows continua **experimental**; veja o [guia de LAN no Windows](docs/pt-br/windows-lan.md).

O container oferece apenas o gateway da LAN e exige Docker Engine no Linux. Docker Desktop no Windows não é suportado para esse modo.

## Índice dos guias

Comece pelos pré-requisitos e depois siga o guia da sua configuração.

Use a **GUI como padrão** no Windows e no Linux. O container usa comandos de terminal; os inicializadores nativos de terminal continuam em Outras formas de executar.

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

- [Outras formas de executar](docs/pt-br/terminal.md)

- [Gateway LAN nativo no Windows — experimental](docs/pt-br/windows-lan.md)
