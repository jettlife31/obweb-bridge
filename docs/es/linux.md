# PCSX2 en el mismo equipo Linux

[Índice de guías](../../README.ES.md) · [English](../en/linux.md) · [Português (Brasil)](../pt-br/linux.md) · [Español](../es/linux.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

## 1. Instala los requisitos e inicia el bridge

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

Para contadores y metadatos de protocolo del bridge Linux, consulta [Diagnóstico](diagnostics.md).

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Windows](windows.md) · [ARMSX2 en Android](android.md) · [PlayStation 2 real](ps2.md) · [Contenedor en Linux](container.md)
