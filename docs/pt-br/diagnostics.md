# Diagnóstico (Linux)

[Índice dos guias](../../README.PTBR.md) · [English](../en/diagnostics.md) · [Português (Brasil)](../pt-br/diagnostics.md) · [Español](../es/diagnostics.md)

Antes de começar, conclua os [pré-requisitos](prerequisites.md). Execute os comandos na pasta do aplicativo.

Com a ponte em execução, use outro terminal:

```sh
sudo .venv/bin/python diagnose.py --lan-interface INTERFACE --pcsx2-ip IP_DO_PS2 --seconds 45
```

No modo Ethernet local, use o IP do PS2 atribuído pelo DHCP remoto, visível nas configurações de rede do jogo. O diagnóstico monitora apenas `obw-pcsx2` para esse IP e informa contadores da interface e metadados de protocolo sem registrar payloads, endereços MAC, nomes DNS, credenciais ou endereços IP. Para exibir no terminal somente os nomes consultados por DNS nessa captura do PS2, acrescente explicitamente `--show-dns-names`; eles não são salvos. Para um cliente separado na LAN, omita `--pcsx2-ip` e use `--client-ip IP_DO_CLIENTE` para limitar a captura a esse dispositivo.

Continue em [Android / ARMSX2](android.md) ou [PS2 real](ps2.md). Para outro computador pela LAN, defina o gateway e DNS da rede dele como o IP do computador da ponte e selecione Sockets no emulador.

## Contadores da LAN no Windows

Para um gateway LAN via WSL, `diagnose.py` observa o lado Linux. Para verificar o que chega à placa LAN do Windows, execute o Python do Windows em um PowerShell como Administrador, na pasta do aplicativo. O Npcap deve estar instalado. Substitua os dois IPs de exemplo:

```powershell
.\.venv\Scripts\python.exe .\diagnose_windows.py --client-ip IP_DO_CLIENTE --lan-ip IP_DO_PC_DA_PONTE --seconds 45
```

Tente conectar durante a observação. O relatório conta protocolos/portas IPv4 e respostas ICMP de destino inalcançável, incluindo a porta de destino rejeitada quando presente. `peer_is_bridge` indica se a outra ponta é o IP da ponte escolhido; IPs não relacionados, MACs, nomes DNS e conteúdo dos aplicativos não são exibidos. Nenhum arquivo de pacotes é salvo e não são alteradas rotas, firewall ou configurações globais do Pktmon. A execução com Npcap no Windows ainda precisa de validação; os testes do analisador usam quadros sintéticos.

---

Guias relacionados: [Pré-requisitos: patch do jogo, Python e conta](prerequisites.md) · [PCSX2 no mesmo computador Windows](windows.md) · [PCSX2 no mesmo computador Linux](linux.md) · [ARMSX2 no Android](android.md) · [PlayStation 2 real](ps2.md) · [Container no Linux](container.md)
