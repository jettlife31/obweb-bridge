# Interface gráfica — Windows e Linux

[Índice dos guias](../../README.PTBR.md) · [English](../en/gui.md) · [Português (Brasil)](../pt-br/gui.md) · [Español](../es/gui.md)

A GUI é o padrão para execução nativa no Windows e no Linux. A mesma janela Python controla os dois sistemas; os inicializadores de terminal continuam em [Outras formas de executar](terminal.md). O container não usa a GUI.


Nesta branch experimental, o Windows também oferece **Another device on the LAN** com Npcap + WinDivert; siga o [guia de LAN no Windows](windows-lan.md). Os modos LAN no Linux e Ethernet local mantêm a configuração existente.
## 1. Instale os pré-requisitos

Conclua os [pré-requisitos de patch do jogo e conta](prerequisites.md).

- **Windows:** instale Python pelo site oficial, [Npcap](https://npcap.com/#download) separadamente e [OpenVPN Community](https://openvpn.net/community/) usando **Install Now**. OpenVPN Connect é outro produto.
- **Linux:** instale Tkinter e um agente de autorização do desktop, além das dependências do modo da ponte. No Debian/Ubuntu:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1
```

## 2. Abra o aplicativo

Execute na pasta do aplicativo como usuário comum. A configuração de rede pede autorização de administrador separadamente.

**Windows — PowerShell:**

```powershell
.\start-gui.ps1
```

Se a política de execução bloquear o inicializador, use:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-gui.ps1
```

**Linux:**

```sh
./start-gui.sh
```

Os inicializadores preparam a `.venv` e instalam as bibliotecas Python automaticamente. Em **Setup**, confira as dependências e abra as páginas oficiais de download.

### Erros de permissão após execuções como administrador

Execute a GUI como **usuário comum tanto no Windows quanto no Linux**: não use Executar como Administrador para a GUI no Windows nem sudo para a GUI no Linux. Aprove a elevação apenas do auxiliar de rede ao clicar em **Start bridge**.

Arquivos de conta ou pastas de memory cards criados antes como Administrador/root ou por outro usuário podem causar **PermissionError** quando a GUI passa a rodar como usuário comum. A mensagem de erro identifica o caminho afetado. Preserve o REO1 e os arquivos salvos e corrija o acesso somente à pasta/arquivo desse aplicativo para o seu usuário atual. Não apague a pasta `.local` inteira nem altere permissões de pastas não relacionadas. Consulte também o [setup nativo no Windows](windows.md).

## 3. Prepare a conta (opcional)

A preparação da conta é independente do encaminhamento de pacotes. Você pode clicar em **Start bridge** diretamente, sem abrir essa aba nem carregar credenciais salvas. Use essas ferramentas opcionais apenas para criar/importar conta, consultar os dados de login ou gerar memory cards. O jogo continua exigindo sua própria conta válida e o save correspondente.

Em **Account & memory cards**, selecione uma conta salva, crie um novo usuário ou cole um código REO1 existente. Clique em **Prepare account**. O código fica visível ao colar.

Contas novas geram os dois cartões automaticamente. Ao importar, marque **Generate memory cards when importing this account** somente se precisar. O progresso existente é preservado conforme as [regras da conta](prerequisites.md). A janela exibe usuário, senha do jogo, código REO1 e caminhos dos cartões, com botões de cópia. Mantenha esses dados privados.

Com **Saved account** selecionado, clique em **Create memory cards** para gerar os cartões dessa conta sem importá-la novamente. Isso funciona offline e preserva cartões e progresso existentes. **Open memory-card folder** abre o gerenciador de arquivos do sistema. **Open credentials folder** abre a pasta do arquivo de contas salvas (`identities.json`).

## 4. Conecte

Em **Connection**, escolha:

- **PCSX2 on this computer:** disponível no Windows e no Linux. Consulte [Windows](windows.md) ou [Linux](linux.md) para configurar o emulador: **PCAP Switched**, `obw-pcsx2`, interceptação DHCP desligada, DNS automático e novo perfil automático dentro do jogo.
- **Another device on the LAN:** o host Linux está validado; o host Windows experimental usa o [guia de LAN no Windows](windows-lan.md). Selecione a interface conectada aos clientes; a janela mostra o IP do gateway/DNS após iniciar. Configure o [Android](android.md), [PS2 real](ps2.md) ou outro cliente pela LAN conforme o [guia do gateway](lan.md).

No Windows, o nome de uma TAP dedicada existente é opcional. Se o `tapctl.exe` não for encontrado, uma janela permite localizar o arquivo.

Clique em **Start bridge** e aprove a solicitação do sistema. Aguarde **Ready** antes de conectar o jogo. Use seu memory card correspondente e sua senha do jogo; exibi-los na aba da conta é opcional.

## 5. Encerre e diagnostique

**Stop** e o fechamento da janela solicitam a mesma limpeza de rede. A janela aguarda o auxiliar encerrar; não force o fechamento durante a limpeza. Não há desligamento por duração ou inatividade.

O estado da conexão e os contadores aparecem na área de atividade. **Copy diagnostic report** copia informações da plataforma e mensagens de atividade, excluindo os campos da conta. Partidas e elevação no Windows ainda precisam de validação real; a janela Linux e a limpeza do auxiliar em ambiente isolado foram verificadas.
