# Otras formas de ejecutar

[Índice de guías](../../README.ES.md) · [English](../en/terminal.md) · [Português (Brasil)](../pt-br/terminal.md) · [Español](../es/terminal.md)

La [interfaz gráfica](gui.md) es la opción predeterminada para Windows y Linux nativos. Estos iniciadores de terminal siguen disponibles como alternativas. Para un contenedor sin GUI, sigue la [guía del contenedor](container.md). Ejecuta los comandos desde la carpeta de la aplicación.


El menú de cuenta es opcional: pulsa **Enter** o **S** para omitirlo e iniciar el bridge, **N** para crear una cuenta, **I** para importar un código REO1 o **V** para consultar la última cuenta guardada. Omitirlo no lee credenciales guardadas ni contacta con el servicio de cuentas. El acceso al juego sigue usando tu propia cuenta.

## Windows — terminal

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

## Linux — terminal

Instala Python 3.10+, `iproute2` y soporte para TUN/TAP. En Debian o Ubuntu:

```sh
sudo apt install python3-venv iproute2
./start-ethernet.sh
```

Ejecuta el iniciador como usuario normal; solicita `sudo` para preparar la interfaz virtual.

Para usar PCAP con el AppImage de PCSX2, extráelo y ejecuta el binario extraído con permisos de captura. El build usado incluye PCAP; la captura requiere permisos adicionales. En otra terminal, este ejemplo supone `~/Downloads/PCSX2.AppImage` — cambia el nombre por el archivo descargado:

```sh
cd "$HOME/Downloads"
./PCSX2.AppImage --appimage-extract
```

Cuando el bridge muestre **READY**, abre PCSX2 con:

```bash
sudo -E setpriv --reuid="$(id -u)" --regid="$(id -g)" --init-groups \
  --inh-caps=+net_raw,+net_admin \
  --ambient-caps=+net_raw,+net_admin \
  --no-new-privs \
  env APPDIR="$HOME/Downloads/squashfs-root" \
      LD_LIBRARY_PATH="$HOME/Downloads/squashfs-root/usr/lib" \
      "$HOME/Downloads/squashfs-root/usr/bin/pcsx2-qt"
```

El comando usa `setpriv` de `util-linux` y ejecuta PCSX2 como tu usuario con los permisos de red necesarios. Si extraes en otra carpeta, ajusta las tres rutas. Configura PCAP como se indica a continuación.

## Gateway LAN — terminal

El modo gateway LAN está disponible en Linux y mediante WSL2 en Windows. Instala Python 3.10+, `iproute2`, `nftables` y soporte para TUN/TAP. En Debian o Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
./start-local.sh
```

Ejecuta como usuario normal. Elige la interfaz conectada a la LAN del cliente, como `enp3s0` o `wlp2s0`; el iniciador muestra cada IPv4 y solicita `sudo` para configurar la red temporal. El cliente debe compartir la LAN, con el aislamiento Wi-Fi desactivado. Usa la IP LAN del equipo que ejecuta el bridge como gateway y DNS del cliente. Para una PS2 real, configura esos campos dentro del juego según la guía del cliente.

Para configurar el emulador, consulta [Windows](windows.md) o [Linux](linux.md). Para otro cliente, sigue [Android](android.md) o [PS2 real](ps2.md). Cierra las sesiones de terminal con Ctrl+C.
