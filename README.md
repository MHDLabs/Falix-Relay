# 🛰️ Falix-Relay

**Keep it simple:) — MHDLabs**

Falix-Relay is a tiny, headless relay built around the **official Xray-core**. It has no web panel, database, account system, quotas, traffic accounting, or secondary proxy engine.

## What v1 does

- Runs the official Xray binary, pinned to **v26.10.21** and verified against a SHA-256 digest during image build.
- Serves one VLESS + WebSocket inbound using the UUID from `XRAY_UUID`.
- Takes the listen port from `PORT` (default: `8080`) and the WebSocket path from `WS_PATH` (default: `/relay`).
- Runs as a non-root user with a read-only root filesystem in the supplied Compose setup.
- Provides `check` and `version` commands without adding a management API.

## Important network requirement

This v1 configuration is for a platform or reverse proxy that **terminates public TLS and forwards HTTP/WebSocket traffic** to Falix-Relay. Xray listens for plain WebSocket inside the container; it does not terminate TLS in this configuration.

Do **not** expose the container's plain WebSocket port directly to an untrusted public network. Put it behind a TLS-enabled ingress/reverse proxy that supports WebSocket upgrades. This minimal configuration does not implement raw-TCP protocol sniffing, REALITY, or a generic multi-protocol router. Those require a different Xray configuration and a compatible network path.

## Quick start with Docker Compose

1. Copy the environment example:

   ```sh
   cp .env.example .env
   ```

2. Generate your own UUID and set it as `XRAY_UUID` in `.env`. Do not use the example UUID in a real deployment. Keep `.env` private; it is ignored by Git.

3. Build the image and validate the generated configuration:

   ```sh
   docker compose build
   docker compose run --rm falix-relay check
   ```

4. Start the relay:

   ```sh
   docker compose up -d
   docker compose logs -f falix-relay
   ```

Compose binds the container port to **127.0.0.1** by default. Configure your TLS ingress/reverse proxy to forward WebSocket requests to that local address and port. The platform's public ingress must support WebSocket upgrades.

For a host that injects `PORT`, set it to the internal listening port expected by that platform. This container runs as non-root and supports ports **1024–65535**.

## Environment variables

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `XRAY_UUID` | Yes for run/check | — | The sole VLESS client UUID. It is rendered into a temporary config at startup and is never printed by Falix-Relay. |
| `PORT` | No | `8080` | Container TCP listen port; must be between 1024 and 65535. |
| `WS_PATH` | No | `/relay` | WebSocket request path. Restricted to a conservative character set. |

No account management, database, quota, bandwidth tracking, web server, QR service, or sing-box dependency is included.

## Validate and inspect

```sh
docker compose run --rm falix-relay check
docker compose run --rm falix-relay version
```

The `check` command runs Xray's own configuration test. It does not test public DNS, TLS ingress, firewall rules, or end-to-end client connectivity.

## Client URI shape

For a TLS-enabled public hostname whose ingress forwards WebSocket traffic to Falix-Relay, a compatible VLESS client URI has this shape:

```text
vless://<XRAY_UUID>@<PUBLIC_HOST>:443?encryption=none&security=tls&sni=<PUBLIC_HOST>&type=ws&host=<PUBLIC_HOST>&path=%2Frelay#Falix-Relay
```

Replace the placeholders with your private UUID and public hostname. The public port, TLS SNI, host header, and path must match your ingress configuration.

## Updating Xray

The Dockerfile pins an exact Xray release and hard-coded SHA-256 digests for the supported Linux amd64 and arm64 archives. When upgrading, update the version and the corresponding official release-asset digests together, then run the CI checks before deploying.

## License

Falix-Relay project files are released under the MHDLabs MIT License. Xray-core is a separate project and retains its own license.
