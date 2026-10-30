# PCSX2 no mesmo computador Linux

[Índice dos guias](../../README.PTBR.md) · [English](../en/linux.md) · [Português (Brasil)](../pt-br/linux.md) · [Español](../es/linux.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.

## 1. Instale os pré-requisitos e inicie a ponte

Instale Python 3.10+, Tkinter, `iproute2`, suporte a TUN/TAP e um agente de autorização do desktop. No Debian/Ubuntu:

```sh
sudo apt install python3-venv python3-tk iproute2 policykit-1
./start-gui.sh
```

Execute a GUI como usuário comum, sem sudo. Escolha **PCSX2 on this computer**, prepare a conta e clique em **Start bridge**. O auxiliar de rede pede autorização separadamente.

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

## 2. Selecione o memory card

Antes de configurar a rede, selecione o memory card da mesma conta no emulador: `outbreak-file1.ps2` para Outbreak ou `outbreak-file2.ps2` para File #2. Se importou uma conta e optou por não gerar cartões, use seu memory card exportado.

## 3. Configure o PCSX2

Em **Settings > Network & HDD**:

- Ative Ethernet e escolha **PCAP Switched** (**PCAP Trocado** em algumas traduções).
- Selecione **obw-pcsx2** ou a TAP dedicada escolhida no Windows.
- Desative **Intercept DHCP**. Deixe os modos DNS em **Automático** e desative entradas DNS internas personalizadas.
- Crie um novo perfil de rede dentro do jogo com todos os campos **Automáticos**.

O DHCP remoto fornece IP do PS2, subrede, gateway e DNS. Nesse modo, deixe esses campos em automático. O inicializador configura a interface virtual; use uma TAP dedicada, sem selecionar sua interface física ou uma TAP de VPN.

Mantenha a ponte aberta enquanto joga. A interface criada por ela é removida ao encerrar; uma TAP Windows preexistente é preservada.

## 4. Jogue e encerre a ponte

Use a imagem com patch e o memory card da mesma conta, inicie o jogo do zero, escolha NETWORK PLAY e depois **Go Online**, informando a senha exibida pelo assistente. A ponte pode ficar aberta sem jogadores, sem limite de duração ou inatividade. Se o WSS cair, ela tentará reconectar automaticamente; uma partida em andamento pode precisar ser reconectada pelo jogo.

Para encerrar a ponte, clique em **Stop** ou feche a janela.

Para contadores e metadados de protocolo na ponte Linux, consulte [Diagnóstico](diagnostics.md).

Para os inicializadores antigos de terminal, consulte [Outras formas de executar](terminal.md).

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Windows](windows.md) · [ARMSX2 no Android](android.md) · [PlayStation 2 real](ps2.md) · [Container no Linux](container.md)
