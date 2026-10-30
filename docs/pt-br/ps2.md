# PlayStation 2 real

[Índice dos guias](../../README.PTBR.md) · [English](../en/ps2.md) · [Português (Brasil)](../pt-br/ps2.md) · [Español](../es/ps2.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.

## 1. Inicie um gateway da LAN

Primeiro [inicie o gateway da LAN](lan.md), pela GUI ou pelo [container](container.md). Aguarde **READY** antes de alterar a rede do cliente.

## 2. Selecione o memory card

Use um memory card físico com o save da mesma conta do Outbreak Web. Se foi preparado no PC, transfira o save usando suas ferramentas de memory card do PS2.

## 3. Configure o PS2 real

Conecte o PS2 à mesma LAN do computador da ponte. Dentro do jogo, crie uma nova configuração de rede em **Network Play**, preencha os campos abaixo manualmente, salve o perfil e selecione-o para Network Play.

- **Endereço IP:** um endereço livre na mesma LAN do computador que executa a ponte. Não use o IP do computador que executa a ponte.
- **Máscara de sub-rede:** a máscara usada pela sua LAN (normalmente `255.255.255.0` em uma rede `/24`).
- **Gateway:** o IP LAN do computador que executa a ponte exibido pela ponte.
- **DNS primário (DNS1):** o mesmo IP LAN do computador que executa a ponte.
- **DNS secundário (DNS2):** use o IP LAN do computador que executa a ponte se a configuração exigir um valor.

## 4. Jogue e encerre a ponte

Use a imagem com patch e o memory card da mesma conta, inicie o jogo do zero, escolha NETWORK PLAY e depois **Go Online**, informando a senha exibida pelo assistente. A ponte pode ficar aberta sem jogadores, sem limite de duração ou inatividade. Se o WSS cair, ela tentará reconectar automaticamente; uma partida em andamento pode precisar ser reconectada pelo jogo.

Para encerrar a ponte, clique em **Stop** ou feche a janela. Se usou o modo gateway, restaure o gateway e DNS originais do cliente quando terminar.

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Windows](windows.md) · [PCSX2 no mesmo computador Linux](linux.md) · [ARMSX2 no Android](android.md) · [Container no Linux](container.md)
