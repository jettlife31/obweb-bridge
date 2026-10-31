# Gateway LAN nativo en Windows — experimental

[Índice de guías](../../README.ES.md) · [English](../en/windows-lan.md) · [Português (Brasil)](../pt-br/windows-lan.md) · [Español](../es/windows-lan.md)

Este modo experimental está en `feature/windows-native-gateway`. Conecta Android, una PS2 real u otro PC de la LAN sin WSL ni contenedores. La captura en la tarjeta de red de Windows y las partidas todavía necesitan validación en hardware real. Para PCSX2 en este equipo, sigue usando el [modo Ethernet local](windows.md), que ya funciona.

## 1. Prepara Windows

Completa los [requisitos previos](prerequisites.md), instala Python de 64 bits e instala [Npcap por separado](https://npcap.com/#download). Descarga el paquete oficial [WinDivert 2.2 x64](https://github.com/basil00/WinDivert/releases/tag/v2.2.2). Mantén `WinDivert.dll` y su controlador firmado `WinDivert64.sys` juntos en la carpeta `third_party/WinDivert/x64` de la aplicación, o selecciona la DLL cuando se solicite. La aplicación no descarga ni redistribuye estos controladores. OpenVPN solo se necesita para Ethernet local de PCSX2.

Deja desactivados el uso compartido de Internet y el reenvío IP de Windows en la interfaz seleccionada. No cambies la puerta de enlace, DNS ni rutas del propio PC.

## 2. Abre la GUI

Ejecuta `start-gui.ps1` como usuario normal. Si PowerShell bloquea el script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-gui.ps1
```

En **Connection**, elige **Another device on the LAN** y la interfaz física conectada a los clientes. Pulsa **Start bridge**, aprueba la elevación del auxiliar de red y localiza `WinDivert.dll` si se solicita. **Ready** confirma que la captura local está abierta; los contadores de envío y recepción confirman el camino de datos WSS cuando aumentan.

## 3. Conecta un cliente

El PC y el cliente deben compartir la LAN, sin aislamiento entre clientes. Configura la puerta de enlace y DNS del cliente con la IP del PC indicada por la GUI; usa una IP libre para el cliente y la máscara de la LAN. Sigue la guía de [Android](android.md) o [PS2](ps2.md) para el resto. Continúa usando la ISO parcheada y la cuenta/save correspondiente. Preparar la cuenta en el bridge sigue siendo opcional.

Este modo captura solo tramas de clientes dirigidas al PC como gateway y consultas al DNS local. Npcap transporta las tramas; WinDivert impide respuestas DNS y errores de enrutamiento conflictivos de Windows. No crea adaptadores, rutas, ajustes DNS ni reglas persistentes del firewall, y no activa el reenvío IP de Windows. Excluye el tráfico de Internet del PC. Cada cliente recibe caminos WSS separados para IPv4 reenviado y DNS, con reconexión y renovación DHCP automáticas. Conserva hasta 32 direcciones de clientes hasta pulsar Stop; las partidas simultáneas no están validadas. Esta versión no admite consultas DNS locales fragmentadas; implementa DNS UDP/TCP ordinario y fragmentos IPv4 reenviados.

## 4. Detén o informa de un fallo

Pulsa **Stop** o cierra la GUI y espera al auxiliar. Se cierran los recursos sin restaurar ajustes de red porque no se modifican los del host. Si el Firewall de Windows o el controlador impide capturar/inyectar, no desactives todo el firewall: comparte **Copy diagnostic report**, el tipo de interfaz y la configuración del cliente. Los contadores por sí solos no demuestran que una partida funcione.

[Volver a la GUI](gui.md) · [Gateway LAN en Linux](lan.md)
