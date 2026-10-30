# Pré-requisitos: patch do jogo, Python e conta

[Índice dos guias](../../README.PTBR.md) · [English](../en/prerequisites.md) · [Português (Brasil)](../pt-br/prerequisites.md) · [Español](../es/prerequisites.md)

## 1. Instalar Python para execução nativa

Instale Python 3.10 ou mais recente pelo [site oficial do Python](https://www.python.org/downloads/). No Windows, garanta que o comando `py` esteja disponível; reabra o PowerShell após instalar e confira com `py -3 --version`. No Linux, use os pacotes Python da sua distribuição, incluindo `venv`, seguindo o guia de [Linux](linux.md) ou [gateway da LAN](lan.md), e confira com `python3 --version`.

Os inicializadores usam o Python instalado na máquina e criam a `.venv` e instalam as bibliotecas necessárias automaticamente. O container já inclui Python.

## 2. Aplique o patch à imagem do jogo

Use o patch xdelta correspondente à sua imagem original dos EUA:

- Outbreak USA v2.00: [Resident Evil - Outbreak (USA) (v2.00).xdelta](../../xdelta/Resident%20Evil%20-%20Outbreak%20%28USA%29%20%28v2.00%29.xdelta)
  - SHA-256 da ISO original: `69ae2c48e6f01e2605659feabb54eb9b82c63a809bdc8a78ad2d160b3c59a4a1`
  - SHA-256 da ISO com patch: `0a6b912d873cb262e991f359125e37dde4848864d905c888f822ed98cf9bc0c1`
- Outbreak File #2 USA: [Resident Evil - Outbreak - File 2 (USA).xdelta](../../xdelta/Resident%20Evil%20-%20Outbreak%20-%20File%202%20%28USA%29.xdelta)
  - SHA-256 da ISO original: `bf33c7bcd727868abe6866d747a930c3c54bb7395ab8ebdfce1f7137641f6759`
  - SHA-256 da ISO com patch: `6363263595ea0a4d12308b3c05e2a9c53cc92e96469c0509ee7952b97c09c970`

Aplique o patch a uma cópia da imagem correspondente e mantenha a original intacta. Os hashes SHA-256 acima foram verificados nas ISOs de origem e nas ISOs com patch. Por exemplo, usando `xdelta3`:

```sh
xdelta3 -d -s "original.iso" "patch.xdelta" "outbreak-web.iso"
```

## 3. Prepare sua conta do Outbreak Web

Você pode criar uma conta pelo inicializador da ponte. Ao confirmar o cadastro, ele exibe usuário, senha e código REO1 e gera `outbreak-file1.ps2` e `outbreak-file2.ps2`. Na execução nativa, os cartões ficam em `generated-memcards/`, na pasta do aplicativo.

Para importar uma conta existente do Outbreak Web:

1. Abra **Settings > Online > Show my code** e copie seu código de transferência REO. Ao escolher **Import**, o login da ponte pedirá esse código.
2. Abra **Saves > Export save (.ps2)** para exportar seu memory card com o progresso existente.

Na importação nativa, o inicializador pergunta se você deseja gerar os cartões e guarda essa escolha. Você pode usar o cartão exportado do site. Cartões já gerados para a mesma conta são preservados; ao trocar a conta dos arquivos fixos, os cartões anteriores são guardados em `generated-memcards/backups/`.

Mantenha o código REO, a senha e os cartões em sigilo.

## Escolha sua configuração

- [PCSX2 no mesmo computador Windows](windows.md)
- [PCSX2 no mesmo computador Linux](linux.md)
- [ARMSX2 no Android](android.md)
- [PlayStation 2 real](ps2.md)
- [Container no Linux](container.md)

---

Guias relacionados: [PCSX2 no mesmo computador Windows](windows.md) · [PCSX2 no mesmo computador Linux](linux.md) · [ARMSX2 no Android](android.md) · [PlayStation 2 real](ps2.md) · [Container no Linux](container.md)
