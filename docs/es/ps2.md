# PlayStation 2 real

[Índice de guías](../../README.ES.md) · [English](../en/ps2.md) · [Português (Brasil)](../pt-br/ps2.md) · [Español](../es/ps2.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

## 1. Inicia un gateway LAN

Primero [inicia el gateway LAN](lan.md), con la GUI o con el [contenedor](container.md). Espera **READY** antes de cambiar la red del cliente.

## 2. Selecciona la tarjeta de memoria

Usa una tarjeta de memoria física con el save de la misma cuenta de Outbreak Web. Si se preparó en un PC, transfiere el save con tus herramientas de tarjeta de memoria de PS2.

## 3. Configura la PS2 real

Conecta la PS2 a la misma LAN del equipo del bridge. En el juego, crea una configuración de red nueva en **Network Play**, introduce los campos siguientes manualmente, guarda el perfil y selecciónalo para Network Play.

- **Dirección IP:** una dirección libre en la misma LAN que el equipo que ejecuta el bridge. No uses la IP del equipo del bridge.
- **Máscara de subred:** la máscara utilizada por tu LAN (normalmente `255.255.255.0` en una red `/24`).
- **Gateway:** la IP LAN del equipo que ejecuta el bridge, mostrada por el bridge.
- **DNS primario (DNS1):** la misma IP LAN del equipo que ejecuta el bridge.
- **DNS secundario (DNS2):** usa la IP LAN del equipo que ejecuta el bridge si la configuración exige un valor.

## 4. Juega y cierra el bridge

Usa la imagen parcheada y la tarjeta de la misma cuenta, inicia el juego desde cero, elige NETWORK PLAY y después **Go Online**, e introduce la contraseña del asistente. El bridge puede permanecer abierto sin jugadores, sin límite de duración o inactividad. Si WSS se desconecta, reintenta automáticamente; una partida activa puede necesitar reconexión dentro del juego.

Pulsa **Stop** o cierra la ventana para detener el bridge. Si usaste el modo gateway, restaura el gateway y DNS del cliente al terminar.

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Windows](windows.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [ARMSX2 en Android](android.md) · [Contenedor en Linux](container.md)
