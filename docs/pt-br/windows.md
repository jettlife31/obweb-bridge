# PCSX2 no mesmo computador Windows

[Índice dos guias](../../README.PTBR.md) · [English](../en/windows.md) · [Português (Brasil)](../pt-br/windows.md) · [Español](../es/windows.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.

## 1. Instale os pré-requisitos e inicie a ponte

Feche o PCSX2 antes de instalar os pré-requisitos:

1. Instale Python 3.10+ seguindo as [instruções do Python](prerequisites.md#1-instalar-python-para-execução-nativa).
2. Baixe e instale o [Npcap pelo site oficial](https://npcap.com/#download). Ele é necessário para a interface `obw-pcsx2` aparecer na lista PCAP do PCSX2.
3. Baixe o [OpenVPN Community Edition](https://openvpn.net/community/) (não o OpenVPN Connect), abra o instalador e clique em **Install Now**.

Depois de instalar todos os pré-requisitos, abra o PowerShell como Administrador e execute:

```powershell
.\start-ethernet.ps1
```

Aguarde **READY** e depois abra o PCSX2.

Para usar uma TAP-Windows6 dedicada existente, execute `.\start-ethernet.ps1 -Adapter "SUA INTERFACE TAP"`. Partidas no Windows ainda precisam de validação.

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

Para encerrar a ponte, pressione Ctrl+C.

## Se a TAP não aparecer no PCAP

Instale o [Npcap pelo site oficial](https://npcap.com/#download) separadamente do OpenVPN. A interface aparecer em Sockets ou TAP não significa que o PCAP consegue capturá-la. Feche o PCSX2, mantenha a ponte aberta em **READY** e reabra o PCSX2. Se o Npcap foi instalado com acesso restrito a administradores, execute também o PCSX2 como Administrador.

Use outro PowerShell para consultar os vínculos da interface sem alterá-los:

```powershell
Get-NetAdapterBinding -Name "obw-pcsx2" -AllBindings -IncludeHidden | Format-Table DisplayName,ComponentID,Enabled -AutoSize
```

Se a inicialização falhar, copie a linha que identifica o comando do Windows e os códigos do erro. Mantenha as credenciais da conta fora das capturas de tela.

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Linux](linux.md) · [ARMSX2 no Android](android.md) · [PlayStation 2 real](ps2.md) · [Container no Linux](container.md)
