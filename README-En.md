# 🛰️ Falix-Relay

A lightweight VLESS + WebSocket relay powered by the official Xray-core.

[🇮🇷 فارسی](README.md)

Falix-Relay keeps a small deployment simple. Set a few environment variables and run the service. No web panel or database is included.

## ✨ Features

- 🔐 One VLESS inbound with one UUID
- 🌐 WebSocket transport with a configurable path
- ⚙️ Configurable listening port
- 📦 Docker image for AMD64 and ARM64
- 🔒 Non-root runtime
- 🧪 Configuration check command

## 🧩 Project scope

- Uses the official Xray-core release, pinned to v26.10.31. This release disables MPTCP by default.
- Supports VLESS over WebSocket.
- Runs one inbound with one client UUID.
- Uses a direct outbound.
- Includes no web panel, bot, database, account system, quota manager, or traffic statistics.
- Stores no persistent application data inside the container.

## ☁️ Deploy on Falix

Falix-Relay requires a Falix server type with support for a custom Docker image. This option is not available on every server type. Check Falix's [Startup Configuration guide](https://kb.falixnodes.net/falix/dashboard/setup/startup-configuration) before deploying.

> [!WARNING]
> Falix Free servers are not permitted for running VPN or proxy server software, or for relaying other people's traffic. Do not run Falix-Relay on a Free server. Review the terms for your selected plan before deployment. See the [Falix Acceptable Use Policy](https://falixnodes.net/acceptable-use-policy).

### 1. Select the image

Set the following image in the server's Startup settings. If your server type has no custom image option, it does not support this deployment method.

```text
ghcr.io/mhdlabs/falix-relay:latest
```

### 2. Set the listening port

Falix injects the assigned port through `SERVER_PORT`. The current Falix-Relay release reads this variable directly and gives it priority over `PORT`. You do not need to set the port manually in Falix.

On other hosts, the application uses `PORT` when `SERVER_PORT` is not present. The default is `8080`.

### 3. Set environment variables

| Variable | Value |
|---|---|
| `XRAY_UUID` | A new private UUID |
| `SERVER_PORT` | Injected by Falix with the assigned port |
| `PORT` | Fallback port on other hosts, defaults to `8080` |
| `WS_PATH` | `/relay` |

Generate a UUID on Linux:

```sh
cat /proc/sys/kernel/random/uuid
```

Keep your UUID private.

### 4. Start the service

Start the server from the Falix panel and inspect its Console. The startup message shows the listening port and WebSocket path.

## 🔗 Client connection

Falix provides two common connection paths. Get the public address and assigned port from the Network page.

### Direct public port

This profile uses plain WebSocket without TLS. Replace the placeholders with your server details.

```text
vless://<XRAY_UUID>@<FALIX_ADDRESS>:<FALIX_PORT>?encryption=none&security=none&type=ws&host=<FALIX_ADDRESS>&path=%2Frelay#Falix-Relay
```

### Falix Reverse Proxy

For a secure connection, create a Falix Reverse Proxy with active TLS and point its backend to the service port. Use the proxy domain after TLS becomes active.

```text
vless://<XRAY_UUID>@<FALIX_DOMAIN>:443?encryption=none&security=tls&sni=<FALIX_DOMAIN>&type=ws&host=<FALIX_DOMAIN>&path=%2Frelay#Falix-Relay
```

A DNS subdomain alone does not provide TLS. Use `security=tls` only with a TLS-enabled Reverse Proxy. The proxy must forward WebSocket traffic and preserve the `/relay` path.

Read Falix's [Domains and HTTPS guide](https://client.falixnodes.net/guides/web-apps/domains-and-https) and [WebSocket guide](https://client.falixnodes.net/guides/web-apps/websockets).

## ⚙️ Environment variables

| Variable | Default | Description |
|---|---|---|
| `XRAY_UUID` | None | Required private UUID for the only VLESS client |
| `SERVER_PORT` | Injected by Falix | Takes priority when present |
| `PORT` | `8080` | Fallback TCP port. Valid range: 1024 to 65535 |
| `WS_PATH` | `/relay` | WebSocket request path |

## 🐳 Run locally with Docker Compose

Clone the repository and copy the sample environment file:

```sh
git clone https://github.com/MHDLabs/Falix-Relay.git
cd Falix-Relay
cp .env.example .env
```

Replace the sample `XRAY_UUID` in `.env` with your private UUID. Build the image and validate the Xray configuration:

```sh
docker compose build
docker compose run --rm falix-relay check
```

Start the service and view its logs:

```sh
docker compose up -d
docker compose logs -f falix-relay
```

The Compose file publishes the port on `127.0.0.1` only. For public access, configure a TLS-enabled reverse proxy on the same host and forward WebSocket traffic to the local service port.

## 📦 Published image

GitHub Actions builds a multi-platform image for Linux AMD64 and ARM64 on pushes to `main` and on `v*` tags.

```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```

Anonymous pulls require Public visibility for the package in GitHub Packages.

## 🛠️ Troubleshooting

| Problem | Check |
|---|---|
| Service does not start | Check the UUID format and the PORT range |
| Connection refused | Confirm SERVER_PORT is present, or PORT matches the Falix allocation |
| Direct connection fails | Check the address, port, UUID, and `/relay` path. Keep TLS disabled for a direct connection |
| Secure connection fails | Check the Reverse Proxy TLS status and backend port |
| Configuration error | Run the `check` command and inspect the Xray logs |

The `check` command validates the Xray configuration only. It does not test public DNS, port allocation, TLS, firewall rules, or client connectivity.

## 🔐 Security

- Keep your UUID private.
- Direct WebSocket connections do not use TLS.
- Use a TLS-enabled Reverse Proxy for WSS.
- Do not expose the raw service port without an appropriate network layer.
- Keep a private copy of your UUID before replacing or removing the container.

## 📄 License

Falix-Relay project files are released under the MIT License. Xray-core is a separate project and keeps its own license.

---

❤️ Made with love in MHDLabs

Keep it simple :)
