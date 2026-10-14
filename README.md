# 🚀 FreeNET

> Minimal VLESS proxy server with WebSocket and XHTTP transports.

[🇮🇷 فارسی](README-fa.md)

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-deploy-0B0D0E?logo=railway&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## Overview

FreeNET is a small VLESS server intended for deployment behind an HTTP/HTTPS reverse proxy such as Railway. It provides these transports:

- VLESS over WebSocket
- VLESS over XHTTP `packet-up`
- VLESS over XHTTP `stream-up`

There is no web panel, subscription service, user database, or Trojan implementation. Configure your client manually with the instance domain and the UUID stored in `/data/identity.json`.

All proxy destinations use TCP. TLS termination and public HTTPS access must be provided by the hosting platform or reverse proxy.

## Deploy on Railway

1. Deploy this repository as a Railway service.
2. Attach a persistent volume mounted at `/data`.
3. Assign a public domain and enable HTTPS.

Railway supplies the listening port through `PORT`; the app binds to `0.0.0.0`. The health endpoint is `/health`.

The persistent directory contains:

- `/data/identity.json` — the service VLESS UUID.
- `/data/stats.json` — aggregate upload/download counters.

Keep the volume to retain the same UUID and statistics across restarts. If migrating from an older installation, the app reads the UUID from the existing identity file and removes obsolete Trojan/subscription fields.

## Client endpoints

### VLESS WebSocket

- WebSocket path: `/vless/<uuid>`
- Transport: WebSocket
- TLS: enabled at the public proxy; use the public hostname as SNI/Host where required.
- Encryption: `none`

### VLESS XHTTP

- HTTP path: `/xhttp/<uuid>` (additional path components are accepted)
- Methods: `GET` and `POST`
- Modes: `packet-up` and `stream-up`
- Encryption: `none`

Choose the transport and XHTTP mode in the client configuration. The server does not provide or publish generated client links.

## Configuration and storage

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` | `8000` | HTTP listen port (normally set by Railway) |
| `FREENET_DATA_DIR` | `/data` | Directory for identity and statistics |

Create the data directory before running locally:

```bash
mkdir -p data
FREENET_DATA_DIR=./data PORT=8000 python main.py
```

The UUID is generated at first launch and saved to `data/identity.json`. Set that UUID in your client. For real client connections, use a public TLS-enabled domain.

Statistics are aggregate for the whole instance; upload and download values persist with the data volume. Uptime is for the current process and resets on restart.

## Docker

```bash
docker build -t freenet .
docker volume create freenet-data
docker run --rm -p 8000:8000 -e PORT=8000 -v freenet-data:/data freenet
```

## Project structure

```text
FreeNET/
├── main.py          # FastAPI app, UUID persistence, and HTTP routes
├── core.py          # TCP relay and aggregate statistics
├── protocols.py     # VLESS WebSocket and XHTTP transports
├── Dockerfile
├── railway.json
├── requirements.txt
├── README.md
└── README-fa.md
```
