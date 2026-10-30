# ARMSX2 en Android

[Índice de guías](../../README.ES.md) · [English](../en/android.md) · [Português (Brasil)](../pt-br/android.md) · [Español](../es/android.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

## 1. Inicia un gateway LAN

Primero [inicia el gateway LAN](lan.md), con la GUI o con el [contenedor](container.md). Espera **READY** antes de cambiar la red del cliente.

## 2. Selecciona la tarjeta de memoria

Antes de configurar la red, selecciona en el emulador la tarjeta de la misma cuenta: `outbreak-file1.ps2` para Outbreak o `outbreak-file2.ps2` para File #2. Si importaste una cuenta y rechazaste la generación de tarjetas, usa tu memory card exportado.

Aunque uses un emulador, crea una **nueva configuración de red dentro del juego** en vez de reutilizar una antigua y deja sus campos de red en **Automatic**.

## 3. Configura Android y ARMSX2

Activa Ethernet, selecciona **Online / Sockets** e introduce manualmente la IP LAN del equipo que ejecuta el bridge como DNS primario y secundario (recuerda configurarlos como MANUAL y no AUTO). También debes configurar la conexión Wi-Fi de Android como ESTÁTICA de la siguiente manera:

- **Dirección IP:** una dirección libre en la misma LAN que el equipo que ejecuta el bridge. No uses la IP del equipo del bridge.
- **Máscara de subred:** la máscara utilizada por tu LAN (normalmente `255.255.255.0` en una red `/24`).
- **Gateway:** la IP LAN del equipo que ejecuta el bridge, mostrada por el bridge.
- **DNS primario (DNS1):** la misma IP LAN del equipo que ejecuta el bridge.
- **DNS secundario (DNS2):** usa la IP LAN del equipo que ejecuta el bridge si la configuración exige un valor.

## 4. Juega y cierra el bridge

Usa la imagen parcheada y la tarjeta de la misma cuenta, inicia el juego desde cero, elige NETWORK PLAY y después **Go Online**, e introduce la contraseña del asistente. El bridge puede permanecer abierto sin jugadores, sin límite de duración o inactividad. Si WSS se desconecta, reintenta automáticamente; una partida activa puede necesitar reconexión dentro del juego.

Pulsa **Stop** o cierra la ventana para detener el bridge. Si usaste el modo gateway, restaura el gateway y DNS del cliente al terminar.

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Windows](windows.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [PlayStation 2 real](ps2.md) · [Contenedor en Linux](container.md)
