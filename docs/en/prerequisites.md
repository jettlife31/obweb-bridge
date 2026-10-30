# Prerequisites: game patch, Python and account

[Guide index](../../README.md) · [English](../en/prerequisites.md) · [Português (Brasil)](../pt-br/prerequisites.md) · [Español](../es/prerequisites.md)

## 1. Install Python for native use

Install Python 3.10 or newer from the [official Python website](https://www.python.org/downloads/). On Windows, ensure the `py` command is available; reopen PowerShell after installation and check with `py -3 --version`. On Linux, use your distribution's Python packages, including `venv`, following the [Linux](linux.md) or [LAN gateway](lan.md) guide, and check with `python3 --version`.

The launchers use your installed Python and automatically create `.venv` and install the required libraries. The container already includes Python.

## 2. Patch your game image

Use the matching xdelta patch for your own USA game image:

- Outbreak USA v2.00: [Resident Evil - Outbreak (USA) (v2.00).xdelta](../../xdelta/Resident%20Evil%20-%20Outbreak%20%28USA%29%20%28v2.00%29.xdelta)
  - Original ISO SHA-256: `69ae2c48e6f01e2605659feabb54eb9b82c63a809bdc8a78ad2d160b3c59a4a1`
  - Patched ISO SHA-256: `0a6b912d873cb262e991f359125e37dde4848864d905c888f822ed98cf9bc0c1`
- Outbreak File #2 USA: [Resident Evil - Outbreak - File 2 (USA).xdelta](../../xdelta/Resident%20Evil%20-%20Outbreak%20-%20File%202%20%28USA%29.xdelta)
  - Original ISO SHA-256: `bf33c7bcd727868abe6866d747a930c3c54bb7395ab8ebdfce1f7137641f6759`
  - Patched ISO SHA-256: `6363263595ea0a4d12308b3c05e2a9c53cc92e96469c0509ee7952b97c09c970`

Apply the patch to a copy of the matching original image and keep the original unchanged. The SHA-256 values above were verified against the source and patched ISO files. For example, with `xdelta3`:

```sh
xdelta3 -d -s "original.iso" "patch.xdelta" "outbreak-web.iso"
```

## 3. Prepare your Outbreak Web account

The account is required by the game, not by the bridge transport. If your game/save is already configured, start the bridge without creating or importing an account on the bridge computer. The account tools below are optional conveniences.

You can create an account through the bridge launcher. Once registration succeeds, it displays the username, password and REO1 code and generates `outbreak-file1.ps2` and `outbreak-file2.ps2`. Native launches save the cards in `generated-memcards/` inside the application directory.

To import an existing Outbreak Web account:

1. Open **Settings > Online > Show my code** and copy your REO transfer code. Choose **Import** in the bridge login and paste that code.
2. Open **Saves > Export save (.ps2)** to export your memory card with existing progress.

During native import, the launcher asks whether to generate cards and remembers your choice. You can use the card exported from the website. Existing cards for the same account are preserved; when changing the account used by the fixed filenames, previous cards are saved in `generated-memcards/backups/`.

Keep the REO code, password and memory cards private.

## Choose your setup

- [PCSX2 on the same Windows computer](windows.md)
- [PCSX2 on the same Linux computer](linux.md)
- [ARMSX2 on Android](android.md)
- [Physical PlayStation 2](ps2.md)
- [Container on Linux](container.md)

---

Related guides: [PCSX2 on the same Windows computer](windows.md) · [PCSX2 on the same Linux computer](linux.md) · [ARMSX2 on Android](android.md) · [Physical PlayStation 2](ps2.md) · [Container on Linux](container.md)
