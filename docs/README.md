# 🛰️ Falix-Relay Setup Guide

**Keep it simple:) — MHDLabs**

[🇮🇷 راهنمای فارسی](README-fa.md) · [Project repository](https://github.com/MHDLabs/Falix-Relay)

Falix-Relay is a lightweight **VLESS + WebSocket** relay powered by official Xray-core. This guide covers the published Docker image. No setup wizard, management panel, or project-side helper service is required.

> [!IMPORTANT]
> In the current configuration, Xray does not terminate TLS itself. Public traffic must pass through a TLS-enabled ingress or reverse proxy that supports WebSocket. Do not expose the plain WebSocket port directly to an untrusted public network.

## 🧭 Contents

- [Requirements](#-requirements)
- [1. Generate a private UUID](#1-generate-a-private-uuid)
- [2. Pull the image](#2-pull-the-image)
- [3. Run the container](#3-run-the-container)
- [4. Verify the service](#4-verify-the-service)
- [Configuration](#️-configuration)
- [Build a client URI](#-build-a-client-uri)
- [Troubleshooting](#-troubleshooting)
- [Update or remove](#-update-or-remove)

## 📦 Requirements

- Docker Engine and access to GitHub Container Registry (GHCR)
- A domain and TLS ingress/reverse proxy that supports WebSocket
- A network path from the public ingress to the service's internal port

Published image: **`ghcr.io/mhdlabs/falix-relay:latest`**  
Published architectures: **Linux amd64** and **Linux arm64**.

<!-- Screenshot 01 — add the image-pull page or terminal screenshot here later. -->

## 1️⃣ Generate a private UUID

Generate a random, private UUID for every deployment. On Linux:

```sh
cat /proc/sys/kernel/random/uuid
```

Or, when `uuidgen` is installed:

```sh
uuidgen
```

On Windows PowerShell:

```powershell
[guid]::NewGuid().ToString()
```

Do not put your UUID in a public repository, public screenshot, or public message. The example below keeps it in an environment variable instead of typing the secret directly into the Docker command history.

## 2️⃣ Pull the image

```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```

<!-- Screenshot 02 — add the successful image-pull screenshot here later. -->

## 3️⃣ Run the container

The following example is for a host where the **TLS reverse proxy runs on the same machine**. Docker publishes the service only on `127.0.0.1`, so the container port is not directly reachable from the public internet.

```sh
XRAY_UUID="$(cat /proc/sys/kernel/random/uuid)"

docker run -d \
  --name falix-relay \
  --restart unless-stopped \
  --env XRAY_UUID="$XRAY_UUID" \
  --env PORT=8080 \
  --env WS_PATH=/relay \
  --publish 127.0.0.1:8080:8080/tcp \
  ghcr.io/mhdlabs/falix-relay:latest

unset XRAY_UUID
```

If you already generated a UUID, replace the generation line with your private value. Configure the TLS-enabled ingress to forward WebSocket requests to **`127.0.0.1:8080`** and preserve the **`/relay`** path.

> [!NOTE]
> If your host injects a port variable such as `PORT`, the internal listening port and the host's port mapping must agree. The command above is a general Docker example; networking options vary between hosting platforms.

<!-- Screenshot 03 — add the port configuration or running-container screenshot here later. -->

## 4️⃣ Verify the service

Check the container:

```sh
docker ps --filter name=falix-relay
```

Read recent logs:

```sh
docker logs --tail 100 falix-relay
```

Validate the configuration using Xray:

```sh
docker exec falix-relay /usr/local/bin/falix-relay check
```

Inspect the Xray version:

```sh
docker exec falix-relay /usr/local/bin/falix-relay version
```

The `check` command validates the generated configuration. It does not verify public DNS, the TLS certificate, firewall rules, or end-to-end client connectivity.

<!-- Screenshot 04 — add a healthy-container or successful check screenshot here later. -->

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `XRAY_UUID` | None | Private VLESS client UUID; required to run. |
| `PORT` | `8080` | Container TCP listen port; because the process runs as non-root, use `1024`–`65535`. |
| `WS_PATH` | `/relay` | WebSocket path; it must match the ingress and client URI. |

This release has no web panel, database, user management, quotas, or traffic counter.

## 🔗 Build a client URI

For a hostname whose public ingress terminates TLS, use this URI shape:

```text
vless://<XRAY_UUID>@<PUBLIC_HOST>:443?encryption=none&security=tls&sni=<PUBLIC_HOST>&type=ws&host=<PUBLIC_HOST>&path=%2Frelay#Falix-Relay
```

Replace the placeholders:

- `<XRAY_UUID>`: the same private UUID configured in the container
- `<PUBLIC_HOST>`: your actual public hostname
- Port `443`, TLS SNI, Host header, and path must match the TLS ingress/reverse-proxy configuration.

The URI's `%2Frelay` is the URL-encoded form of the `/relay` path.

<!-- Screenshot 05 — add a client-configuration screenshot with all secrets removed here later. -->

## 🧰 Troubleshooting

| Symptom | What to check |
|---|---|
| Container will not start | Run `docker logs --tail 100 falix-relay`; confirm the UUID and port. |
| Connection error or HTTP 502 | Check the reverse-proxy destination port and whether WebSocket Upgrade is forwarded. |
| TLS connection fails | Verify public DNS and the ingress certificate; TLS is not enabled inside this Xray configuration. |
| Client cannot connect | Match the UUID, `/relay` path, Host/SNI, public port, and ingress settings. |
| Port is already in use | Change the host-side port and keep the internal `PORT` and Docker mapping consistent. |

## 🔄 Update or remove

Pull the latest published image:

```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```

To replace a running version, stop and remove the current container, then run the same `docker run` command with the updated image. This project does not store persistent application data in the container; make sure you still have your private UUID before removing it.

```sh
docker stop falix-relay
docker rm falix-relay
```

> [!CAUTION]
> `docker rm` removes the container. Prepare the replacement run command first if you need to keep the service available.

---

**More:** [Persian project README](../README-fa.md) · [English project README](../README.md) · [Source code](https://github.com/MHDLabs/Falix-Relay)
