# obweb-bridge

[English](README.md) · [Português (Brasil)](README.PTBR.md) · [Español](README.ES.md)

Una puerta de enlace IPv4 para Linux que transporta el tráfico del cliente a Outbreak Web mediante su transporte Ethernet sobre WebSocket. Los clientes pueden ser ARMSX2 en Android, una PS2 real u otro equipo en la misma LAN. No es necesario modificar el emulador. Aún no está implementado el soporte para alojar el bridge en Windows o WSL2.

## Configuración

### 0. Requisitos previos

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

Antes de iniciar el bridge, inicia sesión en Outbreak Web y:

1. Abre **Settings > Online > Show my code** y copia tu código de transferencia REO. El inicio de sesión del bridge te pedirá que lo pegues al elegir **Import**.
2. Abre **Saves > Export save (.ps2)** y guarda el archivo exportado en un lugar seguro para configurar el emulador o la consola.

Mantén en privado el código REO y el archivo guardado exportado. No los incluyas en capturas de pantalla ni los compartas con el proyecto del bridge.

### 1. Prepara el bridge de Linux y enruta el cliente a través de él

El bridge se ejecuta en un equipo Linux. Instala Python 3.10+, `iproute2`, `nftables` y soporte para TUN/TAP. En Debian o Ubuntu:

```sh
sudo apt install python3-venv iproute2 nftables procps
```

El iniciador nativo pregunta qué interfaz Linux está conectada a la LAN del cliente. Algunos nombres habituales son `enp3s0` o `eno1` para Ethernet y `wlp2s0` o `wlan0` para Wi-Fi. Muestra la dirección IPv4 de cada interfaz para que elijas la correcta.

```sh
./start-local.sh
```

Ejecuta el iniciador nativo como usuario normal; solo solicita `sudo` para la configuración temporal de red. El host del bridge requiere Linux. Un PC con Windows puede actuar como cliente si usa como gateway y DNS la IP LAN del bridge Linux.

#### Ejecuta la imagen publicada del contenedor

Usa Docker Engine en Linux. La red del host enruta únicamente el tráfico del cliente; Windows puede ser cliente, pero no puede alojar este backend.

El contenedor requiere `OBWEB_LAN_INTERFACE` (la interfaz Linux conectada a la LAN del cliente) y `OBWEB_USERNAME`. `OBWEB_RUN_MODE` es interno y se configura automáticamente. En Compose, pasa las mismas variables en `environment:`.

Docker crea el volumen con nombre en el primer uso y lo conserva entre ejecuciones. El directorio del espacio de nombres de red se crea dentro del contenedor.

```bash
docker run --rm --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --device /dev/net/tun:/dev/net/tun \
  --security-opt seccomp=unconfined \
  --mount type=volume,src=obweb-bridge-data,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=wlp2s0 \
  -e OBWEB_USERNAME=tu_usuario \
  ghcr.io/zenaror/obweb-bridge:latest
```

Sustituye `wlp2s0` por el nombre de tu interfaz Linux. Omite el código REO para crear una cuenta nueva; el nombre de usuario del código debe coincidir con `OBWEB_USERNAME`. El contenedor muestra las credenciales del juego. Si el nombre de usuario ya existe y no se proporciona un código coincidente, el inicio mostrará un error. El volumen Docker `obweb-bridge-data` conserva los datos de la cuenta y de recuperación entre ejecuciones; añade `--cleanup` después del nombre de la imagen para recuperar la red tras una interrupción forzada. Los pull requests compilan la imagen; los pushes a `main` y las etiquetas de versión la publican.

Añade estas opciones `-e` antes del nombre de la imagen solo cuando las necesites:

- **OPCIONAL** — `-e OBWEB_LAN_IP=192.168.1.10` si la interfaz seleccionada tiene varias direcciones IPv4 locales.
- **OPCIONAL** — `-e OBWEB_CLIENT_IP=192.168.1.114` para restringir el reenvío a una sola dirección de cliente.
- **OPCIONAL** — `-e OBWEB_REO_CODE='REO1-username-<32-hex-characters>'` para importar una cuenta existente con el código completo de **Settings > Online > Show my code**.
- **OPCIONAL** — `-e OBWEB_WSS_URL=wss://outbreakweb.com/eth` para sustituir el endpoint WSS predeterminado.
- **OPCIONAL** — `-e OBWEB_WSS_ORIGIN=https://outbreakweb.com` para sustituir el origen WSS predeterminado.
- **OPCIONAL** — `-e OBWEB_RUNTIME_DIR=/var/lib/obweb-bridge/runtime` para cambiar la ruta de estado de ejecución; mantenla dentro de `/var/lib/obweb-bridge` para que el volumen Docker la conserve.

El iniciador prepara el inicio de sesión de Outbreak Web, muestra un plan de red y solicita `sudo` para activar el enrutamiento temporal. Espera a que aparezca **READY**. El asistente de inicio de sesión puede crear un nombre de usuario o importar una cuenta existente con su código de transferencia; muestra la contraseña del juego para introducirla manualmente. Mantén esa pantalla en privado.

El cliente y el equipo Linux deben estar en la misma LAN, y el aislamiento de clientes Wi-Fi debe estar desactivado. En un cliente PC o Android, configura la puerta de enlace predeterminada y el DNS del dispositivo con la IP LAN del equipo Linux que muestra el bridge. Para una PS2 real, usa la configuración de red del juego que se indica a continuación.

### 2. Configura el juego y la red

Aunque uses un emulador, crea una **nueva configuración de red dentro del juego** en vez de reutilizar una antigua y deja sus campos de red en **Automatic**. En los ajustes Ethernet del propio emulador, activa Ethernet, selecciona **Online / Sockets** e introduce manualmente la IP LAN del equipo Linux como DNS primario y secundario. En ARMSX2, estos son los ajustes Ethernet del emulador.

En una PS2 real, crea una nueva configuración de red en la opción Network Play del juego e introduce:

- **Dirección IP:** una dirección libre en la misma LAN que el equipo Linux. No uses la IP del equipo Linux, la IP de otro dispositivo ni una dirección dentro del rango DHCP del router.
- **Máscara de subred:** la máscara utilizada por tu LAN (normalmente `255.255.255.0` en una red `/24`).
- **Gateway:** la IP LAN del equipo Linux que muestra el bridge.
- **DNS primario (DNS1):** la misma IP LAN del equipo Linux.
- **DNS secundario (DNS2):** usa la IP LAN del equipo Linux si la configuración exige un valor.

Guarda el perfil y selecciónalo para Network Play. Esta configuración estática se confirmó como funcional en una PS2 real.

No introduzcas la dirección DHCP remota que muestra el bridge en la configuración de red de la consola.

### 3. Juega

Usa la imagen parcheada, inicia el juego desde cero, selecciona NETWORK PLAY e introduce el nombre de usuario y la contraseña que muestra el asistente de inicio de sesión. Al terminar, pulsa Ctrl+C en la terminal del bridge y restaura la configuración original de gateway/DNS del cliente.

## Cómo funciona

El bridge enruta el tráfico IPv4 de la subred LAN configurada del cliente a través de un espacio de nombres Linux aislado, NAT genérico, TAP y la conexión WSS binaria. La respuesta DHCP remota proporciona la dirección del túnel, el gateway, el DNS y el tiempo de concesión. Las consultas DNS se reenvían a ese DNS remoto, sin reglas específicas por dominio. El transporte no selecciona IP de juegos, dominios ni puertos de aplicación.

En modo Sockets de ARMSX2, el emulador termina la red de la PS2 virtual en Android. Por eso, este programa actúa como gateway IPv4 con NAT, no como puente de capa 2 para el adaptador Ethernet de la PS2. No implementa DNAS ni los servicios del juego; el bypass de DNAS está en la imagen parcheada.

El gateway no cambia la ruta predeterminada del equipo Linux. IPv6, VPN, datos móviles, tráfico directo dentro de la misma LAN, renovación de la concesión DHCP y rutas DHCP classless quedan fuera del recorrido actual. La sesión se detiene si se desconecta WSS o antes de que venza el 90 % de la concesión DHCP remota. El acceso habitual a Internet desde el cliente puede limitarse a los servicios disponibles a través de WSS.

## Diagnóstico

Con el bridge en ejecución, usa otra terminal:

```sh
sudo .venv/bin/python diagnose.py --lan-interface INTERFACE --seconds 45
```

El diagnóstico muestra contadores de tráfico y metadatos DNS sin registrar payloads de paquetes, nombres DNS arbitrarios, credenciales ni IP remotas.
