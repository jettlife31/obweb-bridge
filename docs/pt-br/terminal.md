# Outras formas de executar

[Índice dos guias](../../README.PTBR.md) · [English](../en/terminal.md) · [Português (Brasil)](../pt-br/terminal.md) · [Español](../es/terminal.md)

A [interface gráfica](gui.md) é o padrão para execução nativa no Windows e no Linux. Estes inicializadores de terminal continuam disponíveis como alternativas. Para um container sem GUI, siga o [guia do container](container.md). Execute os comandos na pasta do aplicativo.

## Windows — terminal

Feche o PCSX2 antes de instalar os pré-requisitos:

1. Instale Python 3.10+ seguindo as [instruções do Python](prerequisites.md#1-instalar-python-para-execução-nativa).
2. Baixe e instale o [Npcap pelo site oficial](https://npcap.com/#download). Ele é necessário para a interface `obw-pcsx2` aparecer na lista PCAP do PCSX2.
3. Baixe o [OpenVPN Community Edition](https://openvpn.net/community/) (não o OpenVPN Connect), abra o instalador e clique em **Install Now**.

Depois de instalar todos os pré-requisitos, abra o PowerShell como Administrador e execute:

```powershell
.\start-ethernet.ps1
```

Se o PowerShell bloquear o script pela política de execução, use esta alternativa no mesmo terminal como Administrador. Ela vale apenas para esse processo e não altera a política do sistema permanentemente:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-ethernet.ps1
```

Aguarde **READY** e depois abra o PCSX2.

Para usar uma TAP-Windows6 dedicada existente, execute `.\start-ethernet.ps1 -Adapter "SUA INTERFACE TAP"`. Partidas no Windows ainda precisam de validação.

## Linux — terminal

Instale Python 3.10+, `iproute2` e suporte a TUN/TAP. No Debian ou Ubuntu:

```sh
sudo apt install python3-venv iproute2
./start-ethernet.sh
```

Execute o inicializador como usuário comum; ele solicita `sudo` para preparar a interface virtual.

Para usar PCAP com o AppImage do PCSX2, extraia-o e execute o binário extraído com as permissões de captura. O build que usamos tem PCAP; a captura exige permissões adicionais. Em outro terminal, este exemplo considera o arquivo em `~/Downloads/PCSX2.AppImage` — ajuste o nome ao arquivo baixado:

```sh
cd "$HOME/Downloads"
./PCSX2.AppImage --appimage-extract
```

Depois que a ponte mostrar **READY**, abra o PCSX2 com:

```bash
sudo -E setpriv --reuid="$(id -u)" --regid="$(id -g)" --init-groups \
  --inh-caps=+net_raw,+net_admin \
  --ambient-caps=+net_raw,+net_admin \
  --no-new-privs \
  env APPDIR="$HOME/Downloads/squashfs-root" \
      LD_LIBRARY_PATH="$HOME/Downloads/squashfs-root/usr/lib" \
      "$HOME/Downloads/squashfs-root/usr/bin/pcsx2-qt"
```

O comando usa `setpriv` do pacote `util-linux` e executa o PCSX2 como seu usuário, com as permissões de rede necessárias. Se extrair em outro diretório, ajuste os três caminhos. Configure o PCAP conforme explicado abaixo.

## Gateway da LAN — terminal

O modo gateway está disponível no Linux e via WSL2 no Windows. Instale Python 3.10+, `iproute2`, `nftables` e suporte a TUN/TAP. No Debian ou Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
./start-local.sh
```

Execute como usuário comum. Escolha a interface conectada à LAN do cliente, como `enp3s0` ou `wlp2s0`; o inicializador mostra o IPv4 de cada uma e solicita `sudo` para configurar a rede temporária. O cliente deve estar na mesma LAN, com isolamento de clientes Wi-Fi desativado. Use o IP LAN do computador que executa a ponte como gateway e DNS do cliente. No PS2 real, configure esses campos dentro do jogo, conforme o guia do cliente.

Para configurar o emulador, consulte [Windows](windows.md) ou [Linux](linux.md). Para outro cliente, siga [Android](android.md) ou [PS2 real](ps2.md). Encerre as sessões de terminal com Ctrl+C.
