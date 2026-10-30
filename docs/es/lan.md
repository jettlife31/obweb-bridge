# Gateway LAN

[Índice de guías](../../README.ES.md) · [English](../en/lan.md) · [Português (Brasil)](../pt-br/lan.md) · [Español](../es/lan.md)

Antes de empezar, completa los [requisitos previos](prerequisites.md). Ejecuta los comandos desde la carpeta de la aplicación.

## 1. Inicia un gateway LAN

El gateway LAN de la GUI usa el backend Linux. Linux nativo está soportado; Windows puede iniciarlo mediante la **integración experimental con WSL 2**, descrita abajo. En Linux nativo, instala las dependencias y ejecuta la GUI como usuario normal:

```sh
sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1
./start-gui.sh
```

En **Connection**, selecciona **Another device on the LAN**, elige la interfaz conectada a los clientes y prepara la cuenta. Pulsa **Start bridge**, acepta la autorización de red y espera **Ready**. La ventana muestra la IP del gateway/DNS para los clientes. No cambies el gateway ni DNS del propio equipo del bridge. Los clientes deben compartir la LAN, con el aislamiento Wi-Fi desactivado.

## Windows mediante WSL 2 (experimental)

La GUI de Windows detecta WSL, enumera las distribuciones instaladas e inicia el gateway Linux en la distribución elegida. Esta ruta todavía no se ha validado con clientes LAN en Windows. **WSL backend ready no confirma que el tráfico de la consola/Android llegue al bridge.** Linux nativo sigue siendo el host LAN validado.

1. Instala e inicializa una distribución Linux con tu cuenta normal de Windows siguiendo la [guía oficial de WSL](https://learn.microsoft.com/en-us/windows/wsl/install). La GUI informa si faltan WSL o distribuciones; no instala funciones de Windows ni reinicia el equipo.
2. Usa Windows 11 22H2+ con WSL 2 actualizado y **red reflejada (mirrored)** activa, siguiendo la [guía de red de Microsoft](https://learn.microsoft.com/en-us/windows/wsl/networking). El modo NAT predeterminado se bloquea para este flujo. Editar `.wslconfig` solo tiene efecto cuando WSL aplica el cambio; reiniciar WSL interrumpe sus aplicaciones activas.
3. En la distribución, instala Python 3.10+ y las dependencias Linux. En Ubuntu:

```sh
sudo apt install python3 python3-venv python3-pip iproute2 nftables procps
```

4. Abre la GUI de Windows normalmente. Elige **Another device on the LAN**, selecciona **WSL distribution** y pulsa **Prepare WSL**. Esto crea `.venv-wsl` junto a los archivos de la aplicación e instala las bibliotecas Python como el usuario predeterminado de la distribución. Mantén ese usuario sin privilegios. No se reutiliza `.venv` de Windows. **Refresh** repite las comprobaciones sin instalar nada.
5. Selecciona la interfaz LAN de los clientes que muestra WSL, prepara la cuenta y pulsa **Start bridge**. Solo el auxiliar de red se ejecuta como root de Linux. **Stop** espera la limpieza; no apaga la distribución. La GUI de Windows sigue gestionando los archivos de cuenta y memory cards.

Las comprobaciones cubren el modo mirrored activo, las dependencias y las interfaces IPv4. **No** verifican el reenvío de paquetes LAN arbitrarios a través de Windows/Hyper-V hacia WSL. La aplicación no cambia rutas de Windows, el modo de red de WSL ni reglas de firewall. Si el backend inicia pero los contadores de clientes siguen en cero, todavía hay que investigar la ruta Windows–WSL; alcanzar el DNS no basta. No redirijas Internet del propio equipo del bridge ni uses reglas de puertos específicas del juego como solución. Usa Linux nativo si necesitas la configuración LAN ya validada.

## 2. Continuar

Continúa con [Android / ARMSX2](android.md) o [PS2 real](ps2.md). Para otro equipo por LAN, establece el gateway y DNS de su red en la IP del equipo del bridge y selecciona Sockets en el emulador.

Para contadores y metadatos de protocolo del bridge Linux, consulta [Diagnóstico](diagnostics.md).

Para los iniciadores anteriores de terminal, consulta [Otras formas de ejecutar](terminal.md).

---

Guías relacionadas: [Requisitos previos: parche del juego, Python y cuenta](prerequisites.md) · [PCSX2 en el mismo equipo Windows](windows.md) · [PCSX2 en el mismo equipo Linux](linux.md) · [ARMSX2 en Android](android.md) · [PlayStation 2 real](ps2.md) · [Contenedor en Linux](container.md)
