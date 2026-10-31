# Gateway LAN nativo no Windows — experimental

[Índice dos guias](../../README.PTBR.md) · [English](../en/windows-lan.md) · [Português (Brasil)](../pt-br/windows-lan.md) · [Español](../es/windows-lan.md)

Este modo **experimental** conecta Android, PS2 real ou outro PC da LAN sem WSL ou container. A compatibilidade pode variar conforme a placa de rede e o driver. Para PCSX2 neste computador, continue usando o [modo Ethernet local](windows.md), que já funciona.

## 1. Prepare o Windows

Conclua os [pré-requisitos](prerequisites.md), instale Python de 64 bits e o [Npcap separadamente](https://npcap.com/#download). Baixe o pacote oficial [WinDivert 2.2 x64](https://github.com/basil00/WinDivert/releases/tag/v2.2.2). Mantenha `WinDivert.dll` e o driver assinado `WinDivert64.sys` juntos na pasta `third_party/WinDivert/x64` do aplicativo, ou selecione a DLL quando solicitado. O aplicativo não baixa nem redistribui esses drivers. OpenVPN só é necessário no modo Ethernet local do PCSX2.

Deixe o compartilhamento de Internet e o encaminhamento de IP do Windows desativados na interface selecionada. Não altere o gateway, DNS ou as rotas do próprio PC.

## 2. Abra a GUI

Execute `start-gui.ps1` como usuário normal. Se o PowerShell bloquear o script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-gui.ps1
```

Em **Connection**, escolha **Another device on the LAN** e a interface física conectada aos clientes. Clique em **Start bridge**, aprove a elevação do auxiliar de rede e localize `WinDivert.dll` se solicitado. **Ready** confirma que a captura local foi aberta; os contadores de envio e recebimento confirmam o caminho de dados pelo WSS quando aumentam.

## 3. Conecte um cliente

O PC e o cliente devem estar na mesma LAN, sem isolamento entre clientes. Configure gateway e DNS do cliente com o IP do PC mostrado pela GUI; use um IP livre para o cliente e a máscara da LAN. Siga o guia de [Android](android.md) ou [PS2](ps2.md) para os demais passos. Continue usando a ISO corrigida e a conta/save correspondente. Preparar a conta na ponte continua opcional.

Este modo captura apenas quadros de clientes endereçados ao PC como gateway e consultas ao DNS local. Npcap transporta os quadros; WinDivert impede respostas de DNS e erros de roteamento conflitantes do Windows. Nenhum adaptador, rota, configuração de DNS ou regra persistente de firewall é criado, e o encaminhamento de IP do Windows não é habilitado. A Internet do PC é excluída. Cada cliente recebe caminhos WSS separados para IPv4 encaminhado e DNS, com reconexão e renovação automática de DHCP. Até 32 endereços de clientes são mantidos até parar; partidas simultâneas ainda não foram validadas. Consultas ao DNS local fragmentadas não são suportadas nesta versão; DNS UDP/TCP comum e fragmentos IPv4 encaminhados estão implementados.

## 4. Pare ou relate uma falha

Use **Stop** ou feche a GUI e aguarde o auxiliar encerrar. Os recursos são fechados sem uma etapa de restauração de rede porque as configurações do host não são alteradas. Se o Firewall do Windows ou o driver da placa impedir captura/injeção, não desative o firewall inteiro: envie **Copy diagnostic report**, o tipo de interface selecionada e a configuração do cliente. Contadores, sozinhos, não comprovam uma partida funcionando.

[Voltar à GUI](gui.md) · [Gateway LAN no Linux](lan.md)
