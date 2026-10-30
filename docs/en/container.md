# Container on Linux

[Guide index](../../README.md) · [English](../en/container.md) · [Português (Brasil)](../pt-br/container.md) · [Español](../es/container.md)

Before starting, complete the [prerequisites](prerequisites.md). Run commands from the application folder.

## 1. Run the container image

The container provides only the LAN gateway mode and requires Docker Engine on Linux with `--network host`. For PCSX2 on the same computer, use the [desktop GUI](gui.md). The container remains a terminal-only workflow.

The container requires `OBWEB_LAN_INTERFACE` (the interface connected to the client LAN) and `OBWEB_USERNAME`. `OBWEB_RUN_MODE` is internal and set automatically. Compose users can pass the same variables under `environment:`.

Before running the image for the first time, identify the interface to use by running the following command to list the available interfaces:

```bash
docker run --rm --network host \
  ghcr.io/zenaror/obweb-bridge:latest --list-interfaces
```

You should see output similar to this:
```text
Available interfaces in the container network namespace:
  enp3s0: 192.168.1.10/24
  wlo1: 192.168.10.183/24
Choose the interface on the client LAN. Use Docker Engine on Linux with --network host.
Docker Desktop may show only VM interfaces; these do not expose the physical LAN to this gateway.
Example: -e OBWEB_LAN_INTERFACE=enp3s0 (replace with the client LAN interface).
```

Docker creates the named volume on first use and keeps it between runs. The network namespace directory is created inside the container.

```bash
docker run --rm --network host \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --device /dev/net/tun:/dev/net/tun \
  --security-opt seccomp=unconfined \
  --mount type=volume,src=obweb-bridge-data,dst=/var/lib/obweb-bridge \
  -e OBWEB_LAN_INTERFACE=enp3s0 \
  -e OBWEB_USERNAME=your_username \
  ghcr.io/zenaror/obweb-bridge:latest
```

Replace `enp3s0` with the name of an interface Docker can use. Omit the REO code to create a new account; the code's username must match `OBWEB_USERNAME`. The container prints the game credentials. An existing username without a matching code produces an error. The `obweb-bridge-data` Docker volume keeps account and cleanup state between runs; add `--cleanup` after the image name to recover from a forced stop.

Add these `-e` flags before the image name only when needed:

- **OPTIONAL** — `-e OBWEB_LAN_IP=192.168.1.10` when the selected interface has multiple local IPv4 addresses.
- **OPTIONAL** — `-e OBWEB_CLIENT_IP=192.168.1.114` to restrict forwarding to one client address.
- **OPTIONAL** — `-e OBWEB_REO_CODE='REO1-username-<32-hex-characters>'` to import an existing account using the complete code from **Settings > Online > Show my code**.
- **OPTIONAL** — `-e OBWEB_WSS_URL=wss://outbreakweb.com/eth` to override the default WSS endpoint.
- **OPTIONAL** — `-e OBWEB_WSS_ORIGIN=https://outbreakweb.com` to override the default WSS origin.
- **OPTIONAL** — `-e OBWEB_RUNTIME_DIR=/var/lib/obweb-bridge/runtime` to change the runtime state path; keep it inside `/var/lib/obweb-bridge` so the Docker volume persists it.

In Docker, MCs are generated only when creating a new account. Importing with `OBWEB_REO_CODE` or reusing a saved account does not generate new cards. Generated files are stored in the persistent volume; the logs show their paths and copy commands. For example, while the container is running:

```bash
docker cp CONTAINER_NAME:/var/lib/obweb-bridge/state/outbreak-web-login/memcards/outbreak-file1.ps2 ./outbreak-file1.ps2
docker cp CONTAINER_NAME:/var/lib/obweb-bridge/state/outbreak-web-login/memcards/outbreak-file2.ps2 ./outbreak-file2.ps2
```

Replace `CONTAINER_NAME` with the name shown by `docker ps` and use the paths printed in the logs.

The launchers ask for a username or REO code and display the username, game password and REO1 transfer code; use environment variables in the container. Wait for **READY** before connecting. Keep the credentials private.

## 2. Continue

Once **READY** appears, follow the client instructions: [Android / ARMSX2](android.md) or [physical PS2](ps2.md).

---

Related guides: [Prerequisites: game patch, Python and account](prerequisites.md) · [PCSX2 on the same Windows computer](windows.md) · [PCSX2 on the same Linux computer](linux.md) · [ARMSX2 on Android](android.md) · [Physical PlayStation 2](ps2.md)
