# PCSX2 en el mismo equipo Windows

[Índice de guías](../../README.ES.md) · [English](../en/windows.md) · [Português (Brasil)](../pt-br/windows.md) · [Español](../es/windows.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

## 1. Instala los requisitos e inicia el bridge

Cierra PCSX2 antes de instalar los requisitos:

1. Instala Python 3.10+ siguiendo las [instrucciones de Python](prerequisites.md#1-instalar-python-para-la-ejecución-nativa).
2. Descarga e instala [Npcap desde su sitio oficial](https://npcap.com/#download). Es necesario para que la interfaz `obw-pcsx2` aparezca en la lista PCAP de PCSX2.
3. Descarga [OpenVPN Community Edition](https://openvpn.net/community/) (no OpenVPN Connect), abre el instalador y haz clic en **Install Now**.

Después de instalar todos los requisitos, abre PowerShell como Administrador y ejecuta:

```powershell
.\start-ethernet.ps1
```

Si PowerShell bloquea el script por la directiva de ejecución, usa esta alternativa desde la misma terminal como Administrador. Solo se aplica a este proceso y no cambia permanentemente la directiva del sistema:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-ethernet.ps1
```

Espera **READY** y después abre PCSX2.

Para usar una TAP-Windows6 dedicada existente, ejecuta `.\start-ethernet.ps1 -Adapter "TU INTERFAZ TAP"`. Las partidas en Windows todavía necesitan validación.

## 2. Selecciona la tarjeta de memoria

Antes de configurar la red, selecciona en el emulador la tarjeta de la misma cuenta: `outbreak-file1.ps2` para Outbreak o `outbreak-file2.ps2` para File #2. Si importaste una cuenta y rechazaste la generación de tarjetas, usa tu memory card exportado.

## 3. Configura PCSX2

En **Settings > Network & HDD**:

- Activa Ethernet y elige **PCAP Switched** (**PCAP Trocado** en algunas traducciones).
- Selecciona **obw-pcsx2** o la TAP dedicada elegida en Windows.
- Desactiva **Intercept DHCP**. Deja los modos DNS en **Automático** y desactiva las entradas DNS internas personalizadas.
- Crea un perfil de red nuevo dentro del juego con todos los campos **Automáticos**.

El DHCP remoto asigna IP de PS2, máscara, gateway y DNS. Deja esos campos en automático en este modo. El iniciador configura la interfaz virtual; usa una TAP dedicada en lugar de una interfaz física o una TAP usada por VPN.

Mantén el bridge abierto mientras juegas. Una interfaz creada por el iniciador se elimina al cerrar; una TAP Windows existente se conserva.

## 4. Juega y cierra el bridge

Usa la imagen parcheada y la tarjeta de la misma cuenta, inicia el juego desde cero, elige NETWORK PLAY y después **Go Online**, e introduce la contraseña del asistente. El bridge puede permanecer abierto sin jugadores, sin límite de duración o inactividad. Si WSS se desconecta, reintenta automáticamente; una partida activa puede necesitar reconexión dentro del juego.

Pulsa Ctrl+C para cerrar el bridge.

## Si la TAP no aparece en PCAP

Instala [Npcap desde su sitio oficial](https://npcap.com/#download) por separado de OpenVPN. Que la interfaz aparezca en Sockets o TAP no significa que PCAP pueda capturarla. Cierra PCSX2, mantén el bridge abierto en **READY** y vuelve a abrir PCSX2. Si Npcap se instaló con acceso restringido a administradores, ejecuta también PCSX2 como Administrador.

Usa otra ventana de PowerShell para consultar los vínculos de la interfaz sin modificarlos:

```powershell
Get-NetAdapterBinding -Name "obw-pcsx2" -AllBindings -IncludeHidden | Format-Table DisplayName,ComponentID,Enabled -AutoSize
```

Si el inicio falla, copia la línea que identifica el comando de Windows y los códigos de error. No incluyas las credenciales de la cuenta en las capturas.

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [ARMSX2 en Android](android.md) · [PlayStation 2 real](ps2.md) · [Contenedor en Linux](container.md)
