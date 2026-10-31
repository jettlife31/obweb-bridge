# Gateway da LAN

[Índice dos guias](../../README.PTBR.md) · [English](../en/lan.md) · [Português (Brasil)](../pt-br/lan.md) · [Español](../es/lan.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.


Para o backend experimental com host Windows, siga [Gateway LAN nativo no Windows](windows-lan.md). As instruções Linux abaixo continuam válidas.
## 1. Inicie um gateway da LAN

Hospedar o gateway da LAN pela GUI exige Linux. Instale as dependências e execute a GUI como usuário comum:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1
./start-gui.sh
```

Em **Connection**, selecione **Another device on the LAN**, escolha a interface conectada aos clientes. Clique em **Start bridge**, aprove a autorização da rede e aguarde **Ready**. A janela mostra o IP do gateway/DNS dos clientes. Não altere o gateway ou DNS do próprio computador da ponte. Os clientes devem estar na mesma LAN, com isolamento de clientes Wi-Fi desativado.

## 2. Continuar

Continue em [Android / ARMSX2](android.md) ou [PS2 real](ps2.md). Para outro computador pela LAN, defina o gateway e DNS da rede dele como o IP do computador da ponte e selecione Sockets no emulador.

Para contadores e metadados de protocolo na ponte Linux, consulte [Diagnóstico](diagnostics.md).

Para os inicializadores antigos de terminal, consulte [Outras formas de executar](terminal.md).

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Windows](windows.md) · [PCSX2 no mesmo computador Linux](linux.md) · [ARMSX2 no Android](android.md) · [PlayStation 2 real](ps2.md) · [Container no Linux](container.md)
