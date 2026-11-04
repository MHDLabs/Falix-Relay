# 🛰️ Falix-Relay

**Keep it simple :) — MHDLabs**

[🇮🇷 فارسی](README-fa.md) · [Setup guide](docs/README.md)

Falix-Relay is a minimal, headless **VLESS + WebSocket** relay powered by the official [Xray-core](https://github.com/XTLS/Xray-core). It is designed for small deployments on Falix or another compatible container host.

No web panel. No user database. No quotas. No traffic accounting. Just one inbound and one UUID.

## ✨ What it includes

- 🔐 One VLESS client, configured through `XRAY_UUID`
- 🌐 WebSocket transport with a configurable `WS_PATH`
- 🔌 Configurable TCP listen port through `PORT`
- 📦 A small Docker image based on the official Xray binary
- 🔒 Non-root runtime and checksum-verified Xray release assets
- 🧰 `check` and `version` commands for basic inspection

The container currently pins Xray-core **v26.10.21**. It does not include a panel, database, account system, quota manager, usage dashboard, or a second proxy engine.

## 🚀 Falix deployment notes

Falix assigns a public port to each server. Set the project's `PORT` environment variable to the exact port assigned in **Network → Ports**. The current entrypoint reads `PORT`; it does not automatically read Falix's `SERVER_PORT` variable.

The Xray inbound listens on `0.0.0.0`, and the default WebSocket path is `/relay`.

You can connect through the raw Falix address and port using plain WebSocket, or place the service behind Falix's Reverse Proxy and use secure WebSocket (WSS). A Falix DNS subdomain alone does not add TLS.

> [!WARNING]
> **Falix Free servers must not be used to run VPN/proxy software or relay other people's traffic.** Falix's current Acceptable Use Policy explicitly restricts this. Do not deploy this project on a Free server. For any other plan, check the plan-specific terms before deploying.

## ⚙️ Configuration

| Variable | Required | Default | Description |
|---|---:|---|---|
| `XRAY_UUID` | Yes | — | Private UUID for the single VLESS client |
| `PORT` | No | `8080` | TCP listen port; must be between `1024` and `65535` |
| `WS_PATH` | No | `/relay` | WebSocket path |

Generate a private UUID and never publish it:

```sh
cat /proc/sys/kernel/random/uuid
```

## 📚 Documentation

- [🇬🇧 Setup and deployment guide](docs/README.md)
- [🇮🇷 راهنمای راه‌اندازی](docs/README-fa.md)

The guides cover Falix port and domain configuration, client URI formats, Docker usage, and troubleshooting.

## 📦 Published image

The GitHub Actions workflow builds a multi-platform image for Linux **amd64** and **arm64** and publishes it to GHCR:

```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```

Anonymous pulls require the package visibility to be Public in GitHub Packages.

## 🔐 Network and security

Xray listens for plain WebSocket inside the container; TLS is not terminated by this Xray configuration. Use a TLS-enabled reverse proxy when you need WSS. Do not assume that a DNS name by itself provides encryption.

The project does not persist application data inside the container. Keep your UUID somewhere private before replacing or removing a deployment.

## 📄 License

The Falix-Relay project files are released under the MIT License. Xray-core is a separate project and retains its own license.

---

❤️ Made with love in MHDLabs

> Keep it simple :)
