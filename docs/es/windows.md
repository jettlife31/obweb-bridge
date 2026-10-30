# PCSX2 en el mismo equipo Windows

[Índice de guías](../../README.ES.md) · [English](../en/windows.md) · [Português (Brasil)](../pt-br/windows.md) · [Español](../es/windows.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

## 1. Instala los requisitos e inicia el bridge

Cierra PCSX2 antes de instalar los requisitos:

1. Instala Python 3.10+ siguiendo las [instrucciones de Python](prerequisites.md#1-instalar-python-para-la-ejecución-nativa).
2. Descarga e instala [Npcap desde su sitio oficial](https://npcap.com/#download). Es necesario para que la interfaz `obw-pcsx2` aparezca en la lista PCAP de PCSX2.
3. Descarga [OpenVPN Community Edition](https://openvpn.net/community/) (no OpenVPN Connect), abre el instalador y haz clic en **Install Now**.

Después de instalar los requisitos, abre una ventana normal de PowerShell (sin Ejecutar como Administrador) y ejecuta:

```powershell
.\start-gui.ps1
```

Si la directiva de ejecución bloquea el iniciador, usa esta alternativa en la misma terminal de usuario normal. Solo cambia la directiva para ese proceso:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-gui.ps1
```

Elige **PCSX2 on this computer** y pulsa **Start bridge**. Acepta la autorización independiente del auxiliar de red, espera **Ready** y abre PCSX2.

Para reutilizar una TAP-Windows6 dedicada existente, introduce su nombre en la configuración de conexión de la GUI.

### Permisos

Ejecuta la GUI como **usuario normal tanto en Windows como en Linux**: no uses Ejecutar como Administrador para la GUI en Windows ni sudo para la GUI en Linux. Acepta la elevación solo para el auxiliar de red al pulsar **Start bridge**.

Los archivos de cuenta o carpetas de tarjetas creados antes como Administrador/root o por otro usuario pueden provocar **PermissionError** al ejecutar la GUI como usuario normal. El mensaje de error identifica la ruta afectada. Conserva el código REO1 y los archivos guardados, y corrige el acceso únicamente a la carpeta/archivo de esta aplicación para tu usuario actual. No borres todo el directorio `.local` ni cambies los permisos de carpetas no relacionadas.

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

Pulsa **Stop** o cierra la ventana para detener el bridge.

## Si la TAP no aparece en PCAP

Instala [Npcap desde su sitio oficial](https://npcap.com/#download) por separado de OpenVPN. Que la interfaz aparezca en Sockets o TAP no significa que PCAP pueda capturarla. Cierra PCSX2, mantén el bridge abierto en **READY** y vuelve a abrir PCSX2. Si Npcap se instaló con acceso restringido a administradores, ejecuta también PCSX2 como Administrador.

Usa otra ventana de PowerShell para consultar los vínculos de la interfaz sin modificarlos:

```powershell
Get-NetAdapterBinding -Name "obw-pcsx2" -AllBindings -IncludeHidden | Format-Table DisplayName,ComponentID,Enabled -AutoSize
```

Si el inicio falla, copia la línea que identifica el comando de Windows y los códigos de error. No incluyas las credenciales de la cuenta en las capturas.

Para los iniciadores anteriores de terminal, consulta [Otras formas de ejecutar](terminal.md).

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [ARMSX2 en Android](android.md) · [PlayStation 2 real](ps2.md) · [Contenedor en Linux](container.md)
