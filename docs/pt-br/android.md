# ARMSX2 no Android

[Índice dos guias](../../README.PTBR.md) · [English](../en/android.md) · [Português (Brasil)](../pt-br/android.md) · [Español](../es/android.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.

## 1. Inicie um gateway da LAN

Primeiro [inicie o gateway da LAN](lan.md), pela GUI ou pelo [container](container.md). Aguarde **READY** antes de alterar a rede do cliente.

## 2. Selecione o memory card

Antes de configurar a rede, selecione o memory card da mesma conta no emulador: `outbreak-file1.ps2` para Outbreak ou `outbreak-file2.ps2` para File #2. Se importou uma conta e optou por não gerar cartões, use seu memory card exportado.

Mesmo usando um emulador, crie uma **nova configuração de rede dentro do jogo** em vez de reutilizar uma antiga e deixe os campos de rede em **Automatic**.

## 3. Configure o Android e o ARMSX2

Ative Ethernet, escolha **Online / Sockets** e informe manualmente o IP LAN do computador que executa a ponte como DNS primário e secundário, (lembre de defini-los como MANUAL e não AUTO). Também é necessario que configure a sua conexão Wi-Fi do Android para ESTÁTICO da seguinte maneira:

- **Endereço IP:** um endereço livre na mesma LAN do computador que executa a ponte. Não use o IP do computador que executa a ponte.
- **Máscara de sub-rede:** a máscara usada pela sua LAN (normalmente `255.255.255.0` em uma rede `/24`).
- **Gateway:** o IP LAN do computador que executa a ponte exibido pela ponte.
- **DNS primário (DNS1):** o mesmo IP LAN do computador que executa a ponte.
- **DNS secundário (DNS2):** use o IP LAN do computador que executa a ponte se a configuração exigir um valor.

## 4. Jogue e encerre a ponte

Use a imagem com patch e o memory card da mesma conta, inicie o jogo do zero, escolha NETWORK PLAY e depois **Go Online**, informando a senha exibida pelo assistente. A ponte pode ficar aberta sem jogadores, sem limite de duração ou inatividade. Se o WSS cair, ela tentará reconectar automaticamente; uma partida em andamento pode precisar ser reconectada pelo jogo.

Para encerrar a ponte, clique em **Stop** ou feche a janela. Se usou o modo gateway, restaure o gateway e DNS originais do cliente quando terminar.

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Windows](windows.md) · [PCSX2 no mesmo computador Linux](linux.md) · [PlayStation 2 real](ps2.md) · [Container no Linux](container.md)
