# Interfaz gráfica — Windows y Linux

[Índice de guías](../../README.ES.md) · [English](../en/gui.md) · [Português (Brasil)](../pt-br/gui.md) · [Español](../es/gui.md)

La misma ventana Python controla ambos sistemas. Los iniciadores de terminal siguen disponibles. El contenedor no utiliza la GUI.

## 1. Instala los requisitos

Completa los [requisitos de parche del juego y cuenta](prerequisites.md).

- **Windows:** instala Python desde su sitio oficial, [Npcap](https://npcap.com/#download) por separado y [OpenVPN Community](https://openvpn.net/community/) con **Install Now**. OpenVPN Connect es otro producto.
- **Linux:** instala Tkinter y un agente de autorización del escritorio, además de las dependencias del modo del bridge. En Debian/Ubuntu:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1
```

## 2. Abre la aplicación

Ejecuta desde la carpeta de la aplicación como usuario normal. La configuración de red solicita autorización de administrador por separado.

**Windows — PowerShell:**

```powershell
.\start-gui.ps1
```

Si la directiva de ejecución bloquea el iniciador, usa:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-gui.ps1
```

**Linux:**

```sh
./start-gui.sh
```

Los iniciadores preparan `.venv` e instalan las bibliotecas Python automáticamente. En **Setup**, comprueba las dependencias y abre las páginas oficiales de descarga.

## 3. Prepara la cuenta

En **Account & memory cards**, selecciona una cuenta guardada, crea un usuario nuevo o pega un código REO1 existente. Pulsa **Prepare account**. El código permanece visible al pegarlo.

Las cuentas nuevas generan las dos tarjetas automáticamente. Al importar, marca **Generate memory cards when importing this account** solo si lo necesitas. El progreso existente se conserva según las [reglas de la cuenta](prerequisites.md). La ventana muestra usuario, contraseña del juego, código REO1 y rutas de las tarjetas, con botones para copiar. Mantén estos datos privados.

Con **Saved account** seleccionado, pulsa **Create memory cards** para generar las tarjetas de esa cuenta sin importarla otra vez. Funciona sin conexión y conserva las tarjetas y el progreso existentes. **Open memory-card folder** abre el gestor de archivos del sistema.

## 4. Conecta

En **Connection**, elige:

- **PCSX2 on this computer:** disponible en Windows y Linux. Consulta [Windows](windows.md) o [Linux](linux.md) para configurar el emulador: **PCAP Switched**, `obw-pcsx2`, interceptación DHCP desactivada, DNS automático y un perfil automático nuevo dentro del juego.
- **Another device on the LAN:** alojar el gateway actualmente requiere Linux. Selecciona la interfaz conectada a los clientes; la ventana muestra la IP del gateway/DNS tras iniciar. Configura [Android](android.md), [PS2 real](ps2.md) u otro cliente LAN según la [guía del gateway](lan.md).

En Windows, el nombre de una TAP dedicada existente es opcional. Si no se encuentra `tapctl.exe`, una ventana permite localizar el archivo.

Pulsa **Start bridge** y acepta la solicitud del sistema. Espera **Ready** antes de conectar el juego. Usa la tarjeta correspondiente y la contraseña mostrada en la pestaña de la cuenta.

## 5. Cierra y diagnostica

**Stop** y cerrar la ventana solicitan la misma limpieza de red. La ventana espera a que termine el auxiliar; no fuerces el cierre durante la limpieza. No hay apagado por duración o inactividad.

El estado de conexión y los contadores aparecen en el área de actividad. **Copy diagnostic report** copia información de la plataforma y mensajes de actividad, excluyendo los campos de la cuenta. Las partidas y la elevación en Windows aún necesitan validación real; se comprobaron la ventana Linux y la limpieza del auxiliar en un entorno aislado. Esta es una branch de desarrollo y no sustituye los iniciadores existentes.
