# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

Un bridge que conecta consolas y emuladores a Outbreak Web mediante su transporte Ethernet sobre WebSocket. Ejecútalo en Windows o Linux para usar PCSX2 en el mismo equipo, o usa el modo gateway LAN para Android, una PS2 real y otros clientes. No hace falta modificar el emulador.

## Configuración

### 0. Requisitos previos

#### Instalar Python para la ejecución nativa

Instala Python 3.10 o posterior desde el [sitio oficial de Python](https://www.python.org/downloads/). En Windows, asegúrate de que el comando `py` esté disponible; vuelve a abrir PowerShell tras instalarlo y comprueba con `py -3 --version`. En Linux, usa los paquetes Python de tu distribución, incluido `venv`, como en los ejemplos siguientes, y comprueba con `python3 --version`.

Los iniciadores usan el Python instalado en el equipo y crean `.venv` e instalan las bibliotecas necesarias automáticamente. El contenedor ya incluye Python.

#### Aplica el parche a la imagen del juego

Usa el parche xdelta correspondiente a tu imagen original de EE. UU.:

- Outbreak USA v2.00: `xdelta/Resident Evil - Outbreak (USA) (v2.00).xdelta`
  - SHA-256 de la ISO original: `69ae2c48e6f01e2605659feabb54eb9b82c63a809bdc8a78ad2d160b3c59a4a1`
  - SHA-256 de la ISO parcheada: `0a6b912d873cb262e991f359125e37dde4848864d905c888f822ed98cf9bc0c1`
- Outbreak File #2 USA: `xdelta/Resident Evil - Outbreak - File 2 (USA).xdelta`
  - SHA-256 de la ISO original: `bf33c7bcd727868abe6866d747a930c3c54bb7395ab8ebdfce1f7137641f6759`
  - SHA-256 de la ISO parcheada: `6363263595ea0a4d12308b3c05e2a9c53cc92e96469c0509ee7952b97c09c970`

Aplica el parche a una copia de la imagen original correspondiente y conserva intacto el original. Los valores SHA-256 anteriores se verificaron con las imágenes originales y parcheadas. Por ejemplo, con `xdelta3`:

```sh
xdelta3 -d -s "original.iso" "patch.xdelta" "outbreak-web.iso"
```

#### Prepara tu cuenta de Outbreak Web

Puedes crear una cuenta mediante el iniciador del bridge. Al confirmar el registro, muestra el usuario, la contraseña y el código REO1 y genera `outbreak-file1.ps2` y `outbreak-file2.ps2`. En la ejecución nativa, los archivos se guardan en `generated-memcards/`, dentro de la carpeta de la aplicación.

Para importar una cuenta existente de Outbreak Web:

1. Abre **Settings > Online > Show my code** y copia tu código de transferencia REO. Elige **Import** en el inicio de sesión del bridge y pega ese código.
2. Abre **Saves > Export save (.ps2)** para exportar tu memory card con el progreso existente.

Al importar de forma nativa, el iniciador pregunta si quieres generar las tarjetas y recuerda tu elección. Puedes usar la tarjeta exportada del sitio. Las tarjetas existentes de la misma cuenta se conservan; al cambiar la cuenta de los archivos con nombres fijos, las anteriores se guardan en `generated-memcards/backups/`.

Mantén en privado el código REO, la contraseña y las tarjetas.

### 1. Inicia el bridge

Elige el modo para tu configuración:

| Uso | Sistema del equipo del bridge | Iniciador |
|---|---|---|
| PCSX2 en el mismo equipo | Windows | `start-ethernet.ps1` |
| PCSX2 en el mismo equipo | Linux | `start-ethernet.sh` |
| Android, PS2 real u otro PC por LAN | Linux | `start-local.sh` o Docker |

El gateway LAN reenvía los dispositivos de la subred seleccionada; `OBWEB_CLIENT_IP` en el contenedor lo restringe a un cliente. Todavía no se han validado partidas simultáneas de varios dispositivos. El modo Ethernet local atiende un solo emulador por instancia.

#### PCSX2 local — Windows

Instala Python 3.10+ y Npcap. Descarga [OpenVPN Community Edition](https://openvpn.net/community/) (no OpenVPN Connect). En el instalador, selecciona tanto el componente de la aplicación OpenVPN (que proporciona `tapctl.exe`) como el controlador TAP-Windows6. Instalar solo el controlador puede dejar únicamente `tapinstall.exe`, que el bridge no utiliza. Extraer el MSI por sí solo no instala el controlador. Si el bridge no encuentra `tapctl.exe`, solicita la ruta del archivo o de la carpeta. Abre PowerShell como Administrador y ejecuta:

```powershell
.\start-ethernet.ps1
```

Para usar una TAP-Windows6 dedicada existente, ejecuta `.\start-ethernet.ps1 -Adapter "TU INTERFAZ TAP"`. Este modo todavía necesita validación en un equipo Windows.

#### PCSX2 local — Linux

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

El comando usa `setpriv` de `util-linux` y ejecuta PCSX2 como tu usuario con los permisos de red necesarios. Si extraes en otra carpeta, ajusta las tres rutas. Configura PCAP según el paso 2.

#### Otro dispositivo por LAN

El modo gateway LAN está disponible en Linux y mediante WSL2 en Windows. Instala Python 3.10+, `iproute2`, `nftables` y soporte para TUN/TAP. En Debian o Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
./start-local.sh
```

Ejecuta como usuario normal. Elige la interfaz conectada a la LAN del cliente, como `enp3s0` o `wlp2s0`; el iniciador muestra cada IPv4 y solicita `sudo` para configurar la red temporal. El cliente debe compartir la LAN, con el aislamiento Wi-Fi desactivado. Usa la IP LAN del equipo que ejecuta el bridge como gateway y DNS del cliente. Para una PS2 real, configura esos campos dentro del juego según el paso 2.

#### Ejecuta la imagen del contenedor

El contenedor ofrece solo el modo gateway LAN y requiere Docker Engine en Linux con `--network host`. Para PCSX2 en el mismo equipo, usa `start-ethernet.sh` en Linux o `start-ethernet.ps1` en Windows.

El contenedor requiere `OBWEB_LAN_INTERFACE` (la interfaz conectada a la LAN del cliente) y `OBWEB_USERNAME`. `OBWEB_RUN_MODE` es interno y se configura automáticamente. En Compose, pasa las mismas variables en `environment:`.

Antes de ejecutar la imagen por primera vez, identifica la interfaz que vas a usar mediante el siguiente comando para listar las interfaces disponibles:

```bash
docker run --rm --network host \
  ghcr.io/zenaror/obweb-bridge:latest --list-interfaces
```

Deberías obtener una salida similar a esta:
```text
Available interfaces in the container network namespace:
  enp3s0: 192.168.1.10/24
  wlo1: 192.168.10.183/24
Choose the interface on the client LAN. Use Docker Engine on Linux with --network host.
Docker Desktop may show only VM interfaces; these do not expose the physical LAN to this gateway.
Example: -e OBWEB_LAN_INTERFACE=enp3s0 (replace with the client LAN interface).
```

Docker crea el volumen con nombre en el primer uso y lo conserva entre ejecuciones. El directorio del espacio de nombres de red se crea dentro del contenedor.

```bash
docker run --rm --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --device /dev/net/tun:/dev/net/tun \
  --security-opt seccomp=unconfined \
  --mount type=volume,src=obweb-bridge-data,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=enp3s0 \
  -e OBWEB_USERNAME=tu_usuario \
  ghcr.io/zenaror/obweb-bridge:latest
```

Sustituye `enp3s0` por el nombre de una interfaz que Docker pueda usar. Omite el código REO para crear una cuenta nueva; el nombre de usuario del código debe coincidir con `OBWEB_USERNAME`. El contenedor muestra las credenciales del juego. Si el nombre de usuario ya existe y no se proporciona un código coincidente, el inicio mostrará un error. El volumen Docker `obweb-bridge-data` conserva los datos de la cuenta y de recuperación entre ejecuciones; añade `--cleanup` después del nombre de la imagen para recuperar la red tras una interrupción forzada.

Añade estas opciones `-e` antes del nombre de la imagen solo cuando las necesites:

- **OPCIONAL** — `-e OBWEB_LAN_IP=192.168.1.10` si la interfaz seleccionada tiene varias direcciones IPv4 locales.
- **OPCIONAL** — `-e OBWEB_CLIENT_IP=192.168.1.114` para restringir el reenvío a una sola dirección de cliente.
- **OPCIONAL** — `-e OBWEB_REO_CODE='REO1-username-<32-hex-characters>'` para importar una cuenta existente con el código completo de **Settings > Online > Show my code**.
- **OPCIONAL** — `-e OBWEB_WSS_URL=wss://outbreakweb.com/eth` para sustituir el endpoint WSS predeterminado.
- **OPCIONAL** — `-e OBWEB_WSS_ORIGIN=https://outbreakweb.com` para sustituir el origen WSS predeterminado.
- **OPCIONAL** — `-e OBWEB_RUNTIME_DIR=/var/lib/obweb-bridge/runtime` para cambiar la ruta de estado de ejecución; mantenla dentro de `/var/lib/obweb-bridge` para que el volumen Docker la conserve.

En Docker, las tarjetas se generan solo al crear una cuenta nueva. Importar con `OBWEB_REO_CODE` o reutilizar una cuenta guardada no genera nuevas tarjetas. Los archivos creados quedan en el volumen persistente; los logs muestran sus rutas y los comandos para copiarlos. Por ejemplo, mientras el contenedor está en ejecución:

```bash
docker cp CONTAINER_NAME:/var/lib/obweb-bridge/state/outbreak-web-login/memcards/outbreak-file1.ps2 ./outbreak-file1.ps2
docker cp CONTAINER_NAME:/var/lib/obweb-bridge/state/outbreak-web-login/memcards/outbreak-file2.ps2 ./outbreak-file2.ps2
```

Sustituye `CONTAINER_NAME` por el nombre mostrado en `docker ps` y usa las rutas indicadas en los logs.

Los iniciadores piden un usuario o código REO y muestran el usuario, la contraseña del juego y el código de transferencia REO1; en el contenedor, usa variables de entorno. Espera **READY** antes de conectar. Mantén las credenciales en privado.

### 2. Configura el juego y la red

Antes de configurar la red, selecciona en el emulador la tarjeta de la misma cuenta: `outbreak-file1.ps2` para Outbreak o `outbreak-file2.ps2` para File #2. Si importaste una cuenta y rechazaste la generación de tarjetas, usa tu memory card exportado.

Aunque uses un emulador, crea una **nueva configuración de red dentro del juego** en vez de reutilizar una antigua y deja sus campos de red en **Automatic**.

#### ARMSX2 en Android y consolas PS2

Activa Ethernet, selecciona **Online / Sockets** e introduce manualmente la IP LAN del equipo que ejecuta el bridge como DNS primario y secundario (recuerda configurarlos como MANUAL y no AUTO). También debes configurar la conexión Wi-Fi de Android como ESTÁTICA de la siguiente manera:

- **Dirección IP:** una dirección libre en la misma LAN que el equipo que ejecuta el bridge. No uses la IP del equipo del bridge.
- **Máscara de subred:** la máscara utilizada por tu LAN (normalmente `255.255.255.0` en una red `/24`).
- **Gateway:** la IP LAN del equipo que ejecuta el bridge, mostrada por el bridge.
- **DNS primario (DNS1):** la misma IP LAN del equipo que ejecuta el bridge.
- **DNS secundario (DNS2):** usa la IP LAN del equipo que ejecuta el bridge si la configuración exige un valor.

En una PS2 real, crea una nueva configuración de red en la opción Network Play del juego e introduce manualmente las direcciones descritas arriba. Guarda el perfil y selecciónalo para Network Play.

#### PCSX2 en el mismo equipo que aloja el bridge

Usa la interfaz virtual dedicada creada por el iniciador, usando `start-ethernet`. Espera **READY** y abre o reinicia PCSX2 para actualizar la lista de dispositivos. En **Settings > Network & HDD**:

- Activa Ethernet y elige **PCAP Switched** (**PCAP Trocado** en algunas traducciones).
- Selecciona **obw-pcsx2** o la TAP dedicada elegida en Windows.
- Desactiva **Intercept DHCP**. Deja los modos DNS en **Automático** y desactiva las entradas DNS internas personalizadas.
- Crea un perfil de red nuevo dentro del juego con todos los campos **Automáticos**.

El DHCP remoto asigna IP de PS2, máscara, gateway y DNS. Deja esos campos en automático en este modo. El iniciador configura la interfaz virtual; usa una TAP dedicada en lugar de una interfaz física o una TAP usada por VPN.

Mantén el bridge abierto mientras juegas. Una interfaz creada por el iniciador se elimina al cerrar; una TAP Windows existente se conserva.

### 3. Juega

Usa la imagen parcheada y la tarjeta de la misma cuenta, inicia el juego desde cero, elige NETWORK PLAY y después **Go Online**, e introduce la contraseña del asistente. El bridge puede permanecer abierto sin jugadores, sin límite de duración o inactividad. Si WSS se desconecta, reintenta automáticamente; una partida activa puede necesitar reconexión dentro del juego.

Pulsa Ctrl+C para cerrar el bridge. Si usaste el modo gateway, restaura el gateway y DNS del cliente al terminar.

## Diagnóstico (Linux)

Con el bridge en ejecución, usa otra terminal:

```sh
sudo .venv/bin/python diagnose.py --lan-interface INTERFACE --pcsx2-ip IP_DE_LA_PS2 --seconds 45
```

En el modo Ethernet local, usa la IP de la PS2 asignada por DHCP remoto, visible en la configuración de red del juego. El diagnóstico supervisa solo `obw-pcsx2` para esa IP e informa contadores de interfaz y metadatos de protocolo sin guardar payloads, direcciones MAC, nombres DNS, credenciales ni direcciones IP. Para mostrar en la terminal solo los nombres consultados por DNS en esa captura de la PS2, añade explícitamente `--show-dns-names`; no se guardan. Para un cliente LAN independiente, omite `--pcsx2-ip` y usa `--client-ip IP_DEL_CLIENTE` para limitar la captura a ese dispositivo.
