# Gateway da LAN

[Índice dos guias](../../README.PTBR.md) · [English](../en/lan.md) · [Português (Brasil)](../pt-br/lan.md) · [Español](../es/lan.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.

## 1. Inicie um gateway da LAN

O gateway LAN da GUI usa o backend Linux. Linux nativo é suportado; no Windows, a GUI pode iniciá-lo pela **integração experimental com WSL 2**, descrita abaixo. No Linux nativo, instale as dependências e execute a GUI como usuário comum:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps pkexec polkitd
./start-gui.sh
```

Em **Connection**, selecione **Another device on the LAN**, escolha a interface conectada aos clientes e prepare a conta. Clique em **Start bridge**, aprove a autorização da rede e aguarde **Ready**. A janela mostra o IP do gateway/DNS dos clientes. Não altere o gateway ou DNS do próprio computador da ponte. Os clientes devem estar na mesma LAN, com isolamento de clientes Wi-Fi desativado.

## Windows via WSL 2 (experimental)

A GUI do Windows detecta o WSL, lista as distribuições instaladas e inicia o gateway Linux na distribuição escolhida. Esse caminho ainda não foi validado com clientes da LAN no Windows. **WSL backend ready não confirma que o tráfego do console/Android chega à ponte.** Linux nativo continua sendo o host LAN validado.

1. Instale e inicialize uma distribuição Linux na sua conta comum do Windows seguindo o [guia oficial do WSL](https://learn.microsoft.com/en-us/windows/wsl/install). A GUI informa se o WSL ou as distribuições estão ausentes; ela não instala recursos do Windows nem reinicia o computador.
2. Use Windows 11 22H2+ com WSL 2 atualizado e **rede espelhada (mirrored)** ativa, seguindo o [guia de rede da Microsoft](https://learn.microsoft.com/en-us/windows/wsl/networking). O modo NAT padrão é bloqueado nesse fluxo. Editar `.wslconfig` só tem efeito depois que o WSL aplica a configuração; reiniciar o WSL interrompe seus aplicativos em execução.
3. Na distribuição, instale Python 3.10+ e as dependências Linux. No Ubuntu:

```sh
sudo apt install python3 python3-venv python3-pip iproute2 nftables procps
```

4. Abra a GUI do Windows normalmente. Escolha **Another device on the LAN**, selecione a **WSL distribution** e clique em **Prepare WSL**. Isso cria `.venv-wsl` junto dos arquivos do aplicativo e instala as bibliotecas Python como usuário padrão da distribuição. Mantenha esse usuário sem privilégios. O `.venv` do Windows não é reutilizado. **Refresh** repete as verificações sem instalar nada.
5. Escolha a interface da LAN dos clientes apresentada pelo WSL, prepare sua conta e clique em **Start bridge**. Só o auxiliar de rede roda como root no Linux. **Stop** aguarda a limpeza; não desliga a distribuição. Os arquivos de conta e memory cards continuam sendo gerenciados pela GUI do Windows.

As verificações cobrem modo mirrored ativo, dependências e interfaces IPv4. Elas **não** comprovam o encaminhamento de pacotes arbitrários da LAN pelo Windows/Hyper-V até o WSL. O aplicativo não altera rotas do Windows, modo de rede do WSL ou regras de firewall. Se o backend inicia e os contadores dos clientes continuam zerados, o caminho Windows–WSL ainda precisa ser investigado; alcançar o DNS não basta. Não redirecione a Internet do próprio computador da ponte nem use regras de portas específicas do jogo como contorno. Use [Linux nativo](#1-inicie-um-gateway-da-lan) quando precisar da configuração LAN já validada.

## 2. Continuar

Continue em [Android / ARMSX2](android.md) ou [PS2 real](ps2.md). Para outro computador pela LAN, defina o gateway e DNS da rede dele como o IP do computador da ponte e selecione Sockets no emulador.

Para contadores e metadados de protocolo na ponte Linux, consulte [Diagnóstico](diagnostics.md).

Para os inicializadores antigos de terminal, consulte [Outras formas de executar](terminal.md).

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Windows](windows.md) · [PCSX2 no mesmo computador Linux](linux.md) · [ARMSX2 no Android](android.md) · [PlayStation 2 real](ps2.md) · [Container no Linux](container.md)
