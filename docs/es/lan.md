# Gateway LAN

[Índice de guías](../../README.ES.md) · [English](../en/lan.md) · [Português (Brasil)](../pt-br/lan.md) · [Español](../es/lan.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

## 1. Inicia un gateway LAN

Alojar el gateway LAN con la GUI requiere Linux. Instala las dependencias y ejecuta la GUI como usuario normal:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1
./start-gui.sh
```

En **Connection**, selecciona **Another device on the LAN**, elige la interfaz conectada a los clientes y prepara la cuenta. Pulsa **Start bridge**, acepta la autorización de red y espera **Ready**. La ventana muestra la IP del gateway/DNS para los clientes. No cambies el gateway ni DNS del propio equipo del bridge. Los clientes deben compartir la LAN, con el aislamiento Wi-Fi desactivado.

## 2. Continuar

Continúa con [Android / ARMSX2](android.md) o [PS2 real](ps2.md). Para otro equipo por LAN, establece el gateway y DNS de su red en la IP del equipo del bridge y selecciona Sockets en el emulador.

Para contadores y metadatos de protocolo del bridge Linux, consulta [Diagnóstico](diagnostics.md).

Para los iniciadores anteriores de terminal, consulta [Otras formas de ejecutar](terminal.md).

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Windows](windows.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [ARMSX2 en Android](android.md) · [PlayStation 2 real](ps2.md) · [Contenedor en Linux](container.md)
