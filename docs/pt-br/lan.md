# Gateway da LAN

[Índice dos guias](../../README.PTBR.md) · [English](../en/lan.md) · [Português (Brasil)](../pt-br/lan.md) · [Español](../es/lan.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.

## 1. Inicie um gateway da LAN

O modo gateway está disponível no Linux e via WSL2 no Windows. Instale Python 3.10+, `iproute2`, `nftables` e suporte a TUN/TAP. No Debian ou Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
./start-local.sh
```

Execute como usuário comum. Escolha a interface conectada à LAN do cliente, como `enp3s0` ou `wlp2s0`; o inicializador mostra o IPv4 de cada uma e solicita `sudo` para configurar a rede temporária. O cliente deve estar na mesma LAN, com isolamento de clientes Wi-Fi desativado. Use o IP LAN do computador que executa a ponte como gateway e DNS do cliente. No PS2 real, configure esses campos dentro do jogo, conforme o guia do cliente.

## 2. Continuar

Continue em [Android / ARMSX2](android.md) ou [PS2 real](ps2.md). Para outro computador pela LAN, defina o gateway e DNS da rede dele como o IP do computador da ponte e selecione Sockets no emulador.

Para contadores e metadados de protocolo na ponte Linux, consulte [Diagnóstico](diagnostics.md).

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Windows](windows.md) · [PCSX2 no mesmo computador Linux](linux.md) · [ARMSX2 no Android](android.md) · [PlayStation 2 real](ps2.md) · [Container no Linux](container.md)
