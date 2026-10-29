# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

Uma ponte que conecta consoles e emuladores ao Outbreak Web pelo transporte Ethernet via WebSocket. Execute-a no Windows ou no Linux para usar o PCSX2 no mesmo computador, ou use o modo gateway para conectar Android, PS2 real e outros clientes pela LAN. O emulador não precisa ser modificado.

## Configuração

### 0. Pré-requisitos

#### Aplique o patch à imagem do jogo

Use o patch xdelta correspondente à sua imagem original dos EUA:

- Outbreak USA v2.00: `xdelta/Resident Evil - Outbreak (USA) (v2.00).xdelta`
  - SHA-256 da ISO original: `69ae2c48e6f01e2605659feabb54eb9b82c63a809bdc8a78ad2d160b3c59a4a1`
  - SHA-256 da ISO com patch: `0a6b912d873cb262e991f359125e37dde4848864d905c888f822ed98cf9bc0c1`
- Outbreak File #2 USA: `xdelta/Resident Evil - Outbreak - File 2 (USA).xdelta`
  - SHA-256 da ISO original: `bf33c7bcd727868abe6866d747a930c3c54bb7395ab8ebdfce1f7137641f6759`
  - SHA-256 da ISO com patch: `6363263595ea0a4d12308b3c05e2a9c53cc92e96469c0509ee7952b97c09c970`

Aplique o patch a uma cópia da imagem correspondente e mantenha a original intacta. Os hashes SHA-256 acima foram verificados nas ISOs de origem e nas ISOs com patch. Por exemplo, usando `xdelta3`:

```sh
xdelta3 -d -s "original.iso" "patch.xdelta" "outbreak-web.iso"
```

#### Prepare sua conta do Outbreak Web

Você pode criar uma conta pelo inicializador da ponte. Ao confirmar o cadastro, ele exibe usuário, senha e código REO1 e gera `outbreak-file1.ps2` e `outbreak-file2.ps2`. Na execução nativa, os cartões ficam em `generated-memcards/`, na pasta do aplicativo.

Para importar uma conta existente do Outbreak Web:

1. Abra **Settings > Online > Show my code** e copie seu código de transferência REO. Ao escolher **Import**, o login da ponte pedirá esse código.
2. Abra **Saves > Export save (.ps2)** para exportar seu memory card com o progresso existente.

Na importação nativa, o inicializador pergunta se você deseja gerar os cartões e guarda essa escolha. Você pode usar o cartão exportado do site. Cartões já gerados para a mesma conta são preservados; ao trocar a conta dos arquivos fixos, os cartões anteriores são guardados em `generated-memcards/backups/`.

Mantenha o código REO, a senha e os cartões em sigilo.

### 1. Inicie a ponte

Escolha o modo correspondente à sua configuração:

| Uso | Sistema do computador da ponte | Inicializador |
|---|---|---|
| PCSX2 no mesmo computador | Windows | `start-ethernet.ps1` |
| PCSX2 no mesmo computador | Linux | `start-ethernet.sh` |
| Android, PS2 real ou outro PC pela LAN | Linux | `start-local.sh` ou Docker |

O gateway da LAN encaminha os dispositivos da sub-rede selecionada; `OBWEB_CLIENT_IP`, quando informado no container, restringe a um cliente. Partidas simultâneas de vários dispositivos ainda não foram validadas. O modo Ethernet local atende um único emulador por instância.

#### PCSX2 local — Windows

Instale Python 3.10+, Npcap e o driver TAP-Windows6 com `tapctl.exe` do OpenVPN. Abra o PowerShell como Administrador e execute:

```powershell
.\start-ethernet.ps1
```

Para usar uma TAP-Windows6 dedicada existente, execute `.\start-ethernet.ps1 -Adapter "SUA INTERFACE TAP"`. Esse modo ainda precisa de validação em Windows real.

#### PCSX2 local — Linux

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

O comando usa `setpriv` do pacote `util-linux` e executa o PCSX2 como seu usuário, com as permissões de rede necessárias. Se extrair em outro diretório, ajuste os três caminhos. Configure o PCAP conforme o passo 2.

#### Cliente em outro aparelho pela LAN

O modo gateway está disponível no Linux e via WSL2 no Windows. Instale Python 3.10+, `iproute2`, `nftables` e suporte a TUN/TAP. No Debian ou Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
./start-local.sh
```

Execute como usuário comum. Escolha a interface conectada à LAN do cliente, como `enp3s0` ou `wlp2s0`; o inicializador mostra o IPv4 de cada uma e solicita `sudo` para configurar a rede temporária. O cliente deve estar na mesma LAN, com isolamento de clientes Wi-Fi desativado. Use o IP LAN do computador que executa a ponte como gateway e DNS do cliente. No PS2 real, configure esses campos dentro do jogo, conforme o passo 2.

#### Execute a imagem do container

O container oferece somente o modo gateway da LAN e exige Docker Engine no Linux com `--network host`. Para PCSX2 no mesmo computador, use `start-ethernet.sh` no Linux ou `start-ethernet.ps1` no Windows.

O container exige `OBWEB_LAN_INTERFACE` (a interface conectada à LAN do cliente) e `OBWEB_USERNAME`. `OBWEB_RUN_MODE` é interno e configurado automaticamente. No Compose, informe as mesmas variáveis em `environment:`.

Antes de rodar a imagem pela primeira vez, é necessário identificar a interface a ser usada, para isso, execute o comando abaixo para listar as interfaces disponíveis:

```bash
docker run --rm --network host \
  ghcr.io/zenaror/obweb-bridge:latest --list-interfaces
```

Você deve obter uma saída parecida com isso:
```text
Available interfaces in the container network namespace:
  enp3s0: 192.168.1.10/24
  wlo1: 192.168.10.183/24
Choose the interface on the client LAN. Use Docker Engine on Linux with --network host.
Docker Desktop may show only VM interfaces; these do not expose the physical LAN to this gateway.
Example: -e OBWEB_LAN_INTERFACE=enp3s0 (replace with the client LAN interface).
```

O Docker cria o volume nomeado na primeira execução e o mantém entre execuções. O diretório do namespace de rede é criado dentro do container.

```bash
docker run --rm --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --device /dev/net/tun:/dev/net/tun \
  --security-opt seccomp=unconfined \
  --mount type=volume,src=obweb-bridge-data,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=enp3s0 \
  -e OBWEB_USERNAME=seu_usuario \
  ghcr.io/zenaror/obweb-bridge:latest
```

Troque `enp3s0` pelo nome da sua interface que o Docker consegue usar. Omita o código REO para criar uma conta nova; o nome de usuário do código deve corresponder a `OBWEB_USERNAME`. O container exibe as credenciais do jogo. Se o nome de usuário já existir e não houver um código correspondente, a inicialização informa um erro. O volume Docker `obweb-bridge-data` mantém os dados da conta e da recuperação entre execuções; acrescente `--cleanup` após o nome da imagem para recuperar a rede depois de uma interrupção forçada.

Acrescente estas opções `-e` antes do nome da imagem somente quando necessário:

- **OPCIONAL** — `-e OBWEB_LAN_IP=192.168.1.10` se a interface selecionada tiver vários endereços IPv4 locais.
- **OPCIONAL** — `-e OBWEB_CLIENT_IP=192.168.1.114` para restringir o encaminhamento a um único endereço de cliente.
- **OPCIONAL** — `-e OBWEB_REO_CODE='REO1-username-<32-hex-characters>'` para importar uma conta existente usando o código completo de **Settings > Online > Show my code**.
- **OPCIONAL** — `-e OBWEB_WSS_URL=wss://outbreakweb.com/eth` para substituir o endpoint WSS padrão.
- **OPCIONAL** — `-e OBWEB_WSS_ORIGIN=https://outbreakweb.com` para substituir a origem WSS padrão.
- **OPCIONAL** — `-e OBWEB_RUNTIME_DIR=/var/lib/obweb-bridge/runtime` para alterar o diretório de estado em tempo de execução; mantenha-o dentro de `/var/lib/obweb-bridge` para persistir no volume Docker.

No Docker, os MCs são gerados somente ao criar uma conta nova. Importar uma conta com `OBWEB_REO_CODE` ou reutilizar uma conta salva não gera novos cartões. Os arquivos criados ficam no volume persistente; os logs mostram seus caminhos e os comandos para copiá-los. Com o container em execução, por exemplo:

```bash
docker cp CONTAINER_NAME:/var/lib/obweb-bridge/state/outbreak-web-login/memcards/outbreak-file1.ps2 ./outbreak-file1.ps2
docker cp CONTAINER_NAME:/var/lib/obweb-bridge/state/outbreak-web-login/memcards/outbreak-file2.ps2 ./outbreak-file2.ps2
```

Substitua `CONTAINER_NAME` pelo nome exibido em `docker ps` e use os caminhos informados nos logs.

Os inicializadores pedem o usuário ou código REO e exibem o usuário, a senha do jogo e o código de transferência REO1; no container, use as variáveis de ambiente. Aguarde **READY** antes de conectar. Mantenha as credenciais privadas.

### 2. Configure o jogo e a rede

Antes de configurar a rede, selecione o memory card da mesma conta no emulador: `outbreak-file1.ps2` para Outbreak ou `outbreak-file2.ps2` para File #2. Se importou uma conta e optou por não gerar cartões, use seu memory card exportado.

Mesmo usando um emulador, crie uma **nova configuração de rede dentro do jogo** em vez de reutilizar uma antiga e deixe os campos de rede em **Automatic**.

#### ARMSX2 no Android e consoles PS2

Ative Ethernet, escolha **Online / Sockets** e informe manualmente o IP LAN do computador que executa a ponte como DNS primário e secundário, (lembre de defini-los como MANUAL e não AUTO). Também é necessario que configure a sua conexão Wi-Fi do Android para ESTÁTICO da seguinte maneira:

- **Endereço IP:** um endereço livre na mesma LAN do computador que executa a ponte. Não use o IP do computador que executa a ponte.
- **Máscara de sub-rede:** a máscara usada pela sua LAN (normalmente `255.255.255.0` em uma rede `/24`).
- **Gateway:** o IP LAN do computador que executa a ponte exibido pela ponte.
- **DNS primário (DNS1):** o mesmo IP LAN do computador que executa a ponte.
- **DNS secundário (DNS2):** use o IP LAN do computador que executa a ponte se a configuração exigir um valor.

Em um PS2 real crie uma nova configuração de rede e defina os endereços manualmente conforme mencionado acima na opção Network Play do jogo. Salve o perfil e selecione-o para Network Play.

#### PCSX2 no mesmo computador da ponte

Use a interface virtual dedicada criada pelo inicializador, usando o `start-ethernet`. Aguarde **READY** e abra ou reinicie o PCSX2 para atualizar a lista de dispositivos. Em **Settings > Network & HDD**:

- Ative Ethernet e escolha **PCAP Switched** (**PCAP Trocado** em algumas traduções).
- Selecione **obw-pcsx2** ou a TAP dedicada escolhida no Windows.
- Desative **Intercept DHCP**. Deixe os modos DNS em **Automático** e desative entradas DNS internas personalizadas.
- Crie um novo perfil de rede dentro do jogo com todos os campos **Automáticos**.

O DHCP remoto fornece IP do PS2, subrede, gateway e DNS. Nesse modo, deixe esses campos em automático. O inicializador configura a interface virtual; use uma TAP dedicada, sem selecionar sua interface física ou uma TAP de VPN.

Mantenha a ponte aberta enquanto joga. A interface criada por ela é removida ao encerrar; uma TAP Windows preexistente é preservada.

### 3. Jogue

Use a imagem com patch e o memory card da mesma conta, inicie o jogo do zero, escolha NETWORK PLAY e depois **Go Online**, informando a senha exibida pelo assistente. A ponte pode ficar aberta sem jogadores, sem limite de duração ou inatividade. Se o WSS cair, ela tentará reconectar automaticamente; uma partida em andamento pode precisar ser reconectada pelo jogo.

Para encerrar a ponte, pressione Ctrl+C. Se usou o modo gateway, restaure o gateway e DNS originais do cliente quando terminar.

## Diagnóstico (Linux)

Com a ponte em execução, use outro terminal:

```sh
sudo .venv/bin/python diagnose.py --lan-interface INTERFACE --pcsx2-ip IP_DO_PS2 --seconds 45
```

No modo Ethernet local, use o IP do PS2 atribuído pelo DHCP remoto, visível nas configurações de rede do jogo. O diagnóstico monitora apenas `obw-pcsx2` para esse IP e informa contadores da interface e metadados de protocolo sem registrar payloads, endereços MAC, nomes DNS, credenciais ou endereços IP. Para exibir no terminal somente os nomes consultados por DNS nessa captura do PS2, acrescente explicitamente `--show-dns-names`; eles não são salvos. Para um cliente separado na LAN, omita `--pcsx2-ip` e use `--client-ip IP_DO_CLIENTE` para limitar a captura a esse dispositivo.
