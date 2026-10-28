# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

Um gateway IPv4 para Linux que encaminha o tráfego do cliente ao Outbreak Web pelo transporte Ethernet via WebSocket. Os clientes podem ser o ARMSX2 no Android, um PS2 real ou outro computador na mesma LAN. Não é necessário modificar o emulador. O suporte para hospedar a ponte no Windows ou no WSL2 ainda não está implementado.

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

Antes de iniciar a ponte, entre no Outbreak Web e:

1. Abra **Settings > Online > Show my code** e copie seu código de transferência REO. Ao escolher **Import**, o login da ponte pedirá esse código.
2. Abra **Saves > Export save (.ps2)** e salve o arquivo exportado em um local seguro para configurar o emulador ou o console.

Mantenha o código REO e o save exportado em sigilo. Não os inclua em capturas de tela nem os compartilhe com o projeto da ponte.

### 1. Prepare a ponte Linux e encaminhe o cliente por ela

A ponte é executada em um computador Linux. Instale Python 3.10+, `iproute2`, `nftables` e suporte a TUN/TAP. No Debian ou Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
```

O inicializador nativo pergunta qual interface Linux está conectada à LAN do cliente. Nomes comuns são `enp3s0` ou `eno1` para Ethernet e `wlp2s0` ou `wlan0` para Wi-Fi. Ele mostra o endereço IPv4 de cada interface para você escolher a correta.

```sh
./start-local.sh
```

Execute o inicializador nativo como usuário comum; ele solicita `sudo` apenas para configurar temporariamente a rede. O host da ponte precisa ser Linux. Um PC com Windows pode ser cliente se usar o IP LAN da ponte Linux como gateway e DNS.

#### Execute a imagem publicada do container

Use o Docker Engine no Linux. A rede do host encaminha somente o tráfego do cliente; o Windows pode ser cliente, mas não pode hospedar este backend.

O container exige `OBWEB_LAN_INTERFACE` (a interface Linux conectada à LAN do cliente) e `OBWEB_USERNAME`. `OBWEB_RUN_MODE` é interno e configurado automaticamente. No Compose, informe as mesmas variáveis em `environment:`.

O Docker cria o volume nomeado na primeira execução e o mantém entre execuções. O diretório do namespace de rede é criado dentro do container.

```bash
docker run --rm --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --device /dev/net/tun:/dev/net/tun \
  --security-opt seccomp=unconfined \
  --mount type=volume,src=obweb-bridge-data,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=wlp2s0 \
  -e OBWEB_USERNAME=seu_usuario \
  ghcr.io/zenaror/obweb-bridge:latest
```

Troque `wlp2s0` pelo nome da sua interface Linux. Omita o código REO para criar uma conta nova; o nome de usuário do código deve corresponder a `OBWEB_USERNAME`. O container exibe as credenciais do jogo. Se o nome de usuário já existir e não houver um código correspondente, a inicialização informa um erro. O volume Docker `obweb-bridge-data` mantém os dados da conta e da recuperação entre execuções; acrescente `--cleanup` após o nome da imagem para recuperar a rede depois de uma interrupção forçada. Pull requests compilam a imagem; pushes para `main` e tags de versão a publicam.

Acrescente estas opções `-e` antes do nome da imagem somente quando necessário:

- **OPCIONAL** — `-e OBWEB_LAN_IP=192.168.1.10` se a interface selecionada tiver vários endereços IPv4 locais.
- **OPCIONAL** — `-e OBWEB_CLIENT_IP=192.168.1.114` para restringir o encaminhamento a um único endereço de cliente.
- **OPCIONAL** — `-e OBWEB_REO_CODE='REO1-username-<32-hex-characters>'` para importar uma conta existente usando o código completo de **Settings > Online > Show my code**.
- **OPCIONAL** — `-e OBWEB_WSS_URL=wss://outbreakweb.com/eth` para substituir o endpoint WSS padrão.
- **OPCIONAL** — `-e OBWEB_WSS_ORIGIN=https://outbreakweb.com` para substituir a origem WSS padrão.
- **OPCIONAL** — `-e OBWEB_RUNTIME_DIR=/var/lib/obweb-bridge/runtime` para alterar o diretório de estado em tempo de execução; mantenha-o dentro de `/var/lib/obweb-bridge` para persistir no volume Docker.

O inicializador prepara o login do Outbreak Web, mostra um plano de rede e solicita `sudo` para ativar o encaminhamento temporário. Aguarde **READY**. O assistente de login pode criar um nome de usuário ou importar uma conta existente com o código de transferência; ele exibe a senha do jogo para inserção manual. Mantenha essa tela privada.

O cliente e o computador Linux precisam estar na mesma LAN, e o isolamento de clientes Wi-Fi deve estar desativado. Em um cliente PC ou Android, configure o gateway padrão e o DNS do dispositivo com o IP LAN do Linux exibido pela ponte. Em um PS2 real, use as configurações de rede do jogo abaixo.

### 2. Configure o jogo e a rede

Mesmo usando um emulador, crie uma **nova configuração de rede dentro do jogo** em vez de reutilizar uma antiga e deixe os campos de rede em **Automatic**. Nas configurações Ethernet do próprio emulador, ative Ethernet, escolha **Online / Sockets** e informe manualmente o IP LAN do Linux como DNS primário e secundário. No ARMSX2, essas são as configurações Ethernet do emulador.

Em um PS2 real, crie uma nova configuração de rede na opção Network Play do jogo e informe:

- **Endereço IP:** um endereço livre na mesma LAN do computador Linux. Não use o IP do Linux, o IP de outro dispositivo nem um endereço dentro do pool DHCP do roteador.
- **Máscara de sub-rede:** a máscara usada pela sua LAN (normalmente `255.255.255.0` em uma rede `/24`).
- **Gateway:** o IP LAN do computador Linux exibido pela ponte.
- **DNS primário (DNS1):** o mesmo IP LAN do Linux.
- **DNS secundário (DNS2):** use o IP LAN do Linux se a configuração exigir um valor.

Salve o perfil e selecione-o para Network Play. Essa configuração estática foi confirmada funcionando em um PS2 real.

Não informe nas configurações de rede do console o endereço DHCP remoto mostrado pela ponte.

### 3. Jogue

Use a imagem com patch, inicie o jogo do zero, escolha NETWORK PLAY e informe o nome de usuário e a senha exibidos pelo assistente de login. Quando terminar, pressione Ctrl+C no terminal da ponte e restaure as configurações originais de gateway/DNS do cliente.

## Como funciona

A ponte encaminha o tráfego IPv4 da sub-rede LAN do cliente configurada por um namespace Linux isolado, NAT genérico, TAP e a conexão WSS binária. A resposta DHCP remota fornece o endereço, o gateway, o DNS e a concessão do túnel. As consultas DNS são encaminhadas a esse DNS remoto, sem regras específicas por domínio. O transporte não seleciona IPs de jogos, domínios nem portas de aplicação.

No modo Sockets do ARMSX2, o emulador termina a rede do PS2 virtual no Android. Portanto, este programa funciona como gateway IPv4 com NAT, não como uma ponte de camada 2 para o adaptador Ethernet do PS2. Ele não implementa DNAS nem os serviços do jogo; o bypass de DNAS está na imagem com patch.

O gateway não altera a rota padrão do computador Linux. IPv6, VPN, dados móveis, tráfego direto na mesma LAN, renovação da concessão DHCP e rotas DHCP classless não fazem parte do caminho atual. A sessão é encerrada se o WSS desconectar ou antes de expirar 90% da concessão DHCP remota. O acesso comum à Internet pelo cliente pode ficar limitado aos serviços disponíveis pelo WSS.

## Diagnóstico

Com a ponte em execução, use outro terminal:

```sh
sudo .venv/bin/python diagnose.py --lan-interface INTERFACE --seconds 45
```

O diagnóstico informa contagens de tráfego e metadados DNS sem registrar payloads de pacotes, nomes DNS arbitrários, credenciais ou IPs remotos.
