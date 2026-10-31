# Contenedor en Linux

[Índice de guías](../../README.ES.md) · [English](../en/container.md) · [Português (Brasil)](../pt-br/container.md) · [Español](../es/container.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

## 1. Ejecuta la imagen del contenedor

El contenedor ofrece solo el modo gateway LAN y requiere Docker Engine en Linux con `--network host`. Para PCSX2 en el mismo equipo, usa la [interfaz gráfica](gui.md). El contenedor sigue ejecutándose por terminal.

El gateway LAN requiere un runtime **rootful**: un daemon Docker con privilegios de root o **`sudo podman run`**. Podman/Docker rootless no pueden administrar la red del host incluso con `--cap-add`. Para Podman, sustituye `docker run` abajo por `sudo podman run`. El montaje bind de `/proc/sys/net` permite los ajustes de red necesarios para el bridge; no cambia la ruta predeterminada del equipo. El inicio comprueba los permisos antes de preparar cuentas o modificar la red.

Si el inicio indica **OS error 13 (permiso denegado)** en sysctl incluso con ese montaje, una política de seguridad del contenedor puede estar bloqueando el acceso. Para diagnosticarlo, añade `--security-opt apparmor=unconfined` al mismo comando. Esto desactiva el confinamiento AppArmor solo para ese contenedor; no desactiva AppArmor en el equipo. Es independiente de `seccomp=unconfined`. Si el error persiste, consulta los registros de seguridad del host en lugar de añadir `--privileged`.

El contenedor requiere `OBWEB_LAN_INTERFACE` (la interfaz conectada a la LAN del cliente). La preparación de cuenta es opcional: omite `OBWEB_USERNAME` y `OBWEB_REO_CODE` para iniciar solo el bridge. `OBWEB_RUN_MODE` es interno y se configura automáticamente. En Compose, pasa las mismas variables en `environment:`.

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
  --mount type=bind,src=/proc/sys/net,dst=/proc/sys/net \
  --security-opt seccomp=unconfined \
  --mount type=volume,src=obweb-bridge-data,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=enp3s0 \
  ghcr.io/zenaror/obweb-bridge:latest
```

Sustituye `enp3s0` por el nombre de una interfaz que Docker pueda usar. Cuando se configura `OBWEB_USERNAME`, omite el código REO para crear una cuenta nueva; el nombre de usuario del código debe coincidir con `OBWEB_USERNAME`. El contenedor muestra las credenciales del juego. Si el nombre de usuario ya existe y no se proporciona un código coincidente, el inicio mostrará un error. El volumen Docker `obweb-bridge-data` conserva los datos de la cuenta y de recuperación entre ejecuciones; añade `--cleanup` después del nombre de la imagen para recuperar la red tras una interrupción forzada.

Añade estas opciones `-e` antes del nombre de la imagen solo cuando las necesites:

- **OPCIONAL** — `-e OBWEB_USERNAME=tu_usuario` para preparar una cuenta y mostrar sus credenciales del juego. Sin código REO, se crea una cuenta nueva o se reutiliza la identidad guardada.
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

## 2. Continuar

Cuando aparezca **READY**, sigue las instrucciones del cliente: [Android / ARMSX2](android.md) o [PS2 real](ps2.md).

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Windows](windows.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [ARMSX2 en Android](android.md) · [PlayStation 2 real](ps2.md)
