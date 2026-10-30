# Container no Linux

[Índice dos guias](../../README.PTBR.md) · [English](../en/container.md) · [Português (Brasil)](../pt-br/container.md) · [Español](../es/container.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.

## 1. Execute a imagem do container

O container oferece somente o modo gateway da LAN e exige Docker Engine no Linux com `--network host`. Para PCSX2 no mesmo computador, use a [interface gráfica](gui.md). O container continua sendo executado pelo terminal.

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

## 2. Continuar

Depois de aparecer **READY**, siga as instruções do cliente: [Android / ARMSX2](android.md) ou [PS2 real](ps2.md).

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Windows](windows.md) · [PCSX2 no mesmo computador Linux](linux.md) · [ARMSX2 no Android](android.md) · [PlayStation 2 real](ps2.md)
