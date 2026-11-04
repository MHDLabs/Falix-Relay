# 🛰️ Falix-Relay — Setup Guide

[🇮🇷 راهنمای فارسی](README-fa.md) · [Project README](../README.md) · [GitHub repository](https://github.com/MHDLabs/Falix-Relay)

Falix-Relay runs the official Xray-core binary as a minimal VLESS + WebSocket service. This guide explains the required environment variables, Falix networking, client connection formats, and a generic Docker deployment.

> [!WARNING]
> **Falix Free servers may not be used to run VPN/proxy software or relay other people's traffic.** This is stated in Falix's [Acceptable Use Policy](https://falixnodes.net/acceptable-use-policy). Do not deploy this project on a Falix Free server. Check the terms of your specific plan before using another Falix plan.

## 🧭 Contents

- [Requirements](#-requirements)
- [Falix setup](#-falix-setup)
- [Connection profiles](#-connection-profiles)
- [Environment variables](#-environment-variables)
- [Run with Docker Compose](#-run-with-docker-compose)
- [Troubleshooting](#-troubleshooting)
- [Update and remove](#-update-and-remove)

## 📦 Requirements

- A Falix plan and server type whose terms and runtime support this workload
- A server runtime that can run the published container image: `ghcr.io/mhdlabs/falix-relay:latest`
- One public port allocation
- A private UUID
- For WSS, a Falix Reverse Proxy configured for the service's backend port

**Important runtime note:** Falix's custom Docker image option is only available on server types whose configuration exposes that option. The published GHCR image alone does not guarantee that every Falix server type can run it. See Falix's [Startup Configuration guide](https://kb.falixnodes.net/falix/dashboard/setup/startup-configuration).

## ☁️ Falix setup

### 1. Confirm the server runtime

Use a Falix server type that can run the Falix-Relay container image. If the server type does not expose a compatible custom image/runtime option, this image cannot be selected there directly.

### 2. Allocate a public port

Open **Network → Ports** in the Falix panel and note the assigned public port. Falix assigns the port; do not assume it will be `8080`.

The application listens on `0.0.0.0`, which is required for Falix's public port routing. See Falix's [network guide](https://client.falixnodes.net/guides/panel/network-page-deep).

### 3. Configure environment variables

In the server's Environment settings, configure:

| Variable | Value |
|---|---|
| `XRAY_UUID` | A newly generated private UUID |
| `PORT` | The exact numeric port assigned in **Network → Ports** |
| `WS_PATH` | `/relay` |

Falix exposes its assigned port as `SERVER_PORT`, while the current Falix-Relay entrypoint reads `PORT`. Set `PORT` to the same numeric value shown by Falix. The current image does not automatically map `SERVER_PORT` to `PORT`.

Generate a UUID on Linux:

```sh
cat /proc/sys/kernel/random/uuid
```

Keep the UUID private. Do not paste it into a public issue, screenshot, or repository.

### 4. Start the service

Start or restart the server from the Falix panel and inspect its Console. The service should print a startup line similar to:

```text
Falix-Relay: starting official Xray-core on TCP port 42669 (WebSocket path /relay)
```

The port in this example is illustrative. Use the port assigned to your own server.

### 5. Choose the network entry point

Falix offers different ways to reach a server:

- **Ports:** a raw public address and port. This does not provide TLS.
- **Falix subdomain:** a DNS name that still uses the assigned port; the subdomain alone does not provide TLS.
- **Reverse Proxy:** a domain with automatic TLS. Use this when you need secure WebSocket (WSS).

See Falix's [Domains and HTTPS guide](https://client.falixnodes.net/guides/web-apps/domains-and-https) and [WebSocket guide](https://client.falixnodes.net/guides/web-apps/websockets).

## 🔗 Connection profiles

The Xray inbound uses WebSocket without TLS. Choose the matching URI for the way you expose the service.

### Direct Falix address and port — plain WebSocket

Use the address and port from **Network → Ports**:

```text
vless://<XRAY_UUID>@<FALIX_ADDRESS>:<FALIX_PORT>?encryption=none&security=none&type=ws&host=<FALIX_ADDRESS>&path=%2Frelay#Falix-Relay
```

This connection does not use TLS. The client must support VLESS over plain WebSocket.

### Falix Reverse Proxy — secure WebSocket

If you configured a Falix Reverse Proxy and its TLS status is active, use the proxy domain and HTTPS port:

```text
vless://<XRAY_UUID>@<FALIX_DOMAIN>:443?encryption=none&security=tls&sni=<FALIX_DOMAIN>&type=ws&host=<FALIX_DOMAIN>&path=%2Frelay#Falix-Relay
```

Replace every placeholder with your own values. The reverse proxy must forward WebSocket upgrades to the same backend port used by `PORT`, and the path must remain `/relay`.

> [!NOTE]
> A Falix subdomain from the DNS/Subdomains section is not the same as a Reverse Proxy domain. A DNS-only subdomain does not add TLS. Use `security=none` for a raw port, or configure the Reverse Proxy before using `security=tls`.

## ⚙️ Environment variables

| Variable | Required | Default | Description |
|---|---:|---|---|
| `XRAY_UUID` | Yes for `run` and `check` | — | The private UUID for the single VLESS client |
| `PORT` | No | `8080` | TCP listen port; valid range is `1024`–`65535` |
| `WS_PATH` | No | `/relay` | WebSocket request path |

The current configuration has one VLESS inbound and a direct outbound. It has no account management, database, quota, traffic counter, web panel, QR service, or persistent application storage.

## 🐳 Run with Docker Compose

These steps are for a Docker host where you control the machine and can place a TLS reverse proxy on the same host. They are not a substitute for the Falix panel/runtime steps above.

1. Clone the repository and create the environment file:

```sh
git clone https://github.com/MHDLabs/Falix-Relay.git
cd Falix-Relay
cp .env.example .env
```

2. Generate a UUID and replace the example value of `XRAY_UUID` in `.env`. Never deploy with the example UUID.

3. Build and validate the image:

```sh
docker compose build
docker compose run --rm falix-relay check
```

4. Start the service and inspect its logs:

```sh
docker compose up -d
docker compose logs -f falix-relay
```

The supplied Compose file publishes the port only on `127.0.0.1`. Configure a TLS-enabled reverse proxy on the same host to forward WebSocket traffic to that local port. Do not change the binding to a public interface unless you understand and intend to expose plain WebSocket without TLS.

You can also pull the published image directly:

```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```

The image is built for Linux `amd64` and `arm64`. Anonymous pulls require the GHCR package to be Public.

## 🧰 Troubleshooting

| Symptom | Check |
|---|---|
| Container exits immediately | Confirm `XRAY_UUID` is set and valid; inspect the Falix Console or `docker logs`. |
| Connection is refused | Confirm the service is running and `PORT` matches the allocated Falix port. |
| Connection times out | Check the Falix port allocation and any firewall rules. |
| Direct connection fails | Use the exact Falix address and port; configure the client for plain WebSocket without TLS. |
| WSS connection fails | Confirm the Reverse Proxy is active, TLS is active, the backend port is correct, and WebSocket upgrades are forwarded. |
| Client reaches the service but does not authenticate | Check the UUID and the `/relay` path. |
| Docker Compose cannot start | Run `docker compose logs falix-relay` and `docker compose run --rm falix-relay check`. |

The `check` command runs Xray's own configuration test. It does not test public DNS, the Falix allocation, TLS status, firewall rules, or end-to-end client connectivity.

## 🔄 Update and remove

For a GHCR deployment, pull the new image and restart the server using the same environment values:

```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```

For Docker Compose:

```sh
docker compose pull
docker compose up -d
```

To stop and remove the Compose container:

```sh
docker compose down
```

Falix-Relay does not keep persistent application data inside the container. Keep a private copy of your UUID before replacing or removing the service.

---

**More:** [Project README](../README.md) · [Persian setup guide](README-fa.md) · [Source code](https://github.com/MHDLabs/Falix-Relay)
