# Diagnóstico (Linux)

[Índice de guías](../../README.ES.md) · [English](../en/diagnostics.md) · [Português (Brasil)](../pt-br/diagnostics.md) · [Español](../es/diagnostics.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

Con el bridge en ejecución, usa otra terminal:

```sh
sudo .venv/bin/python app/diagnose.py --lan-interface INTERFACE --pcsx2-ip IP_DE_LA_PS2 --seconds 45
```

En el modo Ethernet local, usa la IP de la PS2 asignada por DHCP remoto, visible en la configuración de red del juego. El diagnóstico supervisa solo `obw-pcsx2` para esa IP e informa contadores de interfaz y metadatos de protocolo sin guardar payloads, direcciones MAC, nombres DNS, credenciales ni direcciones IP. Para mostrar en la terminal solo los nombres consultados por DNS en esa captura de la PS2, añade explícitamente `--show-dns-names`; no se guardan. Para un cliente LAN independiente, omite `--pcsx2-ip` y usa `--client-ip IP_DEL_CLIENTE` para limitar la captura a ese dispositivo.

Continúa con [Android / ARMSX2](android.md) o [PS2 real](ps2.md). Para otro equipo por LAN, establece el gateway y DNS de su red en la IP del equipo del bridge y selecciona Sockets en el emulador.

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Windows](windows.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [ARMSX2 en Android](android.md) · [PlayStation 2 real](ps2.md) · [Contenedor en Linux](container.md)
