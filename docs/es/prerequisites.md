# Requisitos previos: parche del juego, Python y cuenta

[Índice de guías](../../README.ES.md) · [English](../en/prerequisites.md) · [Português (Brasil)](../pt-br/prerequisites.md) · [Español](../es/prerequisites.md)

## 1. Instalar Python para la ejecución nativa

Instala Python 3.10 o posterior desde el [sitio oficial de Python](https://www.python.org/downloads/). En Windows, asegúrate de que el comando `py` esté disponible; vuelve a abrir PowerShell tras instalarlo y comprueba con `py -3 --version`. En Linux, usa los paquetes Python de tu distribución, incluido `venv`, siguiendo la guía de [Linux](linux.md) o del [gateway LAN](lan.md), y comprueba con `python3 --version`.

Los iniciadores usan el Python instalado en el equipo y crean `.venv` e instalan las bibliotecas necesarias automáticamente. El contenedor ya incluye Python.

## 2. Aplica el parche a la imagen del juego

Usa el parche xdelta correspondiente a tu imagen original de EE. UU.:

- Outbreak USA v2.00: [Resident Evil - Outbreak (USA) (v2.00).xdelta](../../xdelta/Resident%20Evil%20-%20Outbreak%20%28USA%29%20%28v2.00%29.xdelta)
  - SHA-256 de la ISO original: `69ae2c48e6f01e2605659feabb54eb9b82c63a809bdc8a78ad2d160b3c59a4a1`
  - SHA-256 de la ISO parcheada: `0a6b912d873cb262e991f359125e37dde4848864d905c888f822ed98cf9bc0c1`
- Outbreak File #2 USA: [Resident Evil - Outbreak - File 2 (USA).xdelta](../../xdelta/Resident%20Evil%20-%20Outbreak%20-%20File%202%20%28USA%29.xdelta)
  - SHA-256 de la ISO original: `bf33c7bcd727868abe6866d747a930c3c54bb7395ab8ebdfce1f7137641f6759`
  - SHA-256 de la ISO parcheada: `6363263595ea0a4d12308b3c05e2a9c53cc92e96469c0509ee7952b97c09c970`

Aplica el parche a una copia de la imagen original correspondiente y conserva intacto el original. Los valores SHA-256 anteriores se verificaron con las imágenes originales y parcheadas. Por ejemplo, con `xdelta3`:

```sh
xdelta3 -d -s "original.iso" "patch.xdelta" "outbreak-web.iso"
```

## 3. Prepara tu cuenta de Outbreak Web

Puedes crear una cuenta mediante el iniciador del bridge. Al confirmar el registro, muestra el usuario, la contraseña y el código REO1 y genera `outbreak-file1.ps2` y `outbreak-file2.ps2`. En la ejecución nativa, los archivos se guardan en `generated-memcards/`, dentro de la carpeta de la aplicación.

Para importar una cuenta existente de Outbreak Web:

1. Abre **Settings > Online > Show my code** y copia tu código de transferencia REO. Elige **Import** en el inicio de sesión del bridge y pega ese código.
2. Abre **Saves > Export save (.ps2)** para exportar tu memory card con el progreso existente.

Al importar de forma nativa, el iniciador pregunta si quieres generar las tarjetas y recuerda tu elección. Puedes usar la tarjeta exportada del sitio. Las tarjetas existentes de la misma cuenta se conservan; al cambiar la cuenta de los archivos con nombres fijos, las anteriores se guardan en `generated-memcards/backups/`.

Mantén en privado el código REO, la contraseña y las tarjetas.

## Elige tu configuración

- [PCSX2 en el mismo equipo Windows](windows.md)
- [PCSX2 en el mismo equipo Linux](linux.md)
- [ARMSX2 en Android](android.md)
- [PlayStation 2 real](ps2.md)
- [Contenedor en Linux](container.md)

---

Guías relacionadas: [PCSX2 en el mismo equipo Windows](windows.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [ARMSX2 en Android](android.md) · [PlayStation 2 real](ps2.md) · [Contenedor en Linux](container.md)
