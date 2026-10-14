# 🚀 FreeNET

> A small VLESS server with WebSocket and XHTTP transports.

[🇮🇷 فارسی](README-fa.md)

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-deploy-0B0D0E?logo=railway&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## What it does

FreeNET is a single-UUID VLESS server intended to run behind a public HTTP/HTTPS service such as Railway. It supports:

- VLESS over WebSocket
- VLESS over XHTTP `packet-up`
- VLESS over XHTTP `stream-up`

The server accepts TCP destinations only; UDP is not implemented. TLS is terminated by the public hosting platform. This project has no user panel, per-user accounts, database, or Trojan support.

## Deploy on Railway

1. Fork this repository and deploy the fork as a Railway service. Give your fork/repository a name of your choosing.
2. Sign in to Railway using a GitHub account you own and authorize Railway to access the fork. Use an account that satisfies Railway's current account and service policies; deployment approval cannot be guaranteed by this project.
3. Generate a Railway public domain and wait for the deployment health check at `/health` to pass.

No persistent volume or `/data` directory is required. Railway provides `PORT`; the app listens on `0.0.0.0` and Railway provides public HTTPS/TLS.

### Keep your identifiers stable

The optional environment variables are:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SEC` | Random value at process start | Secret embedded in the subscription URL. Set it in Railway Variables to keep the URL stable across redeploys. |
| `VLESS_UUID` | Random UUID at process start | UUID used by the VLESS server and generated client links. Set it in Railway Variables to keep client configurations stable across redeploys. |
| `PORT` | `8000` | HTTP listen port; normally supplied by Railway. |

At startup, the complete subscription URL is printed in the deployment logs. If `SEC` is not configured, the generated subscription URL changes whenever the process restarts or redeploys. If `VLESS_UUID` is not configured, clients must also be updated to use the newly generated UUID after a restart. The server stores neither value persistently.

Keep `SEC` and `VLESS_UUID` private. Anyone who obtains the subscription URL can download the client configuration, and anyone who obtains the UUID can attempt to connect to the proxy.

## Subscription and transports

Open the logged URL:

```text
https://<railway-domain>/sub/<SEC>
```

It returns a Base64-encoded subscription containing three connectable VLESS entries and one display-only status entry:

| Entry | Transport | Server path | Notes |
| --- | --- | --- | --- |
| FreeNET-VLESS-WS | WebSocket | `/vless/<uuid>` | TLS at the public domain; ALPN `http/1.1`. |
| FreeNET-XHTTP-Packet-Up | XHTTP `packet-up` | `/xhttp/<uuid>` | HTTP `GET`/`POST`; TLS at the public domain. |
| FreeNET-XHTTP-Stream-Up | XHTTP `stream-up` | `/xhttp/<uuid>` | HTTP `GET`/`POST`; TLS at the public domain. |
| FreeNET status | Display-only | Not a server endpoint | Shows process uptime and aggregate traffic; it is not a connection configuration. |

The subscription response also includes aggregate upload/download metadata. Counters and uptime are in memory: they reset on process restart and are not saved to disk.

## Run locally with Python

Python 3.12 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
SEC=change-this-secret VLESS_UUID=12345678-1234-5678-1234-567812345678 PORT=8000 python main.py
```

Open `http://localhost:8000/sub/change-this-secret` to retrieve the subscription. For use from client devices, configure a reachable public domain with TLS termination and set the corresponding `RAILWAY_PUBLIC_DOMAIN` environment variable for the startup URL.

## Docker

The container is stateless and does not need a volume:

```bash
docker build -t freenet .
docker run --rm -p 8000:8000 -e PORT=8000 -e SEC=change-this-secret freenet
```

## Project structure

```text
FreeNET/
├── main.py          # FastAPI app, subscription, UUID validation, and routes
├── core.py          # TCP relay, in-memory traffic counters, and uptime
├── protocols.py     # VLESS WebSocket and XHTTP transports
├── Dockerfile
├── railway.json
├── requirements.txt
├── README.md
└── README-fa.md
```
