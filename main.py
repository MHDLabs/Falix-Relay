import os
import uuid
import logging
import base64
import secrets
from contextlib import asynccontextmanager
from typing import AsyncIterator
from urllib.parse import quote

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import PlainTextResponse, Response

import core
import health

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FreeNET")

SUBSCRIPTION_SECRET = os.environ.get("SEC") or secrets.token_urlsafe(24)
IDENTITY_UUID = uuid.UUID(os.environ.get("VLESS_UUID", str(uuid.uuid4())))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    health.start_background_tasks()
    public_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "localhost:8000")
    subscription_url = f"https://{public_domain}/sub/{quote(SUBSCRIPTION_SECRET, safe='')}"
    logger.info(
        "\nSubscription URL: %s\n"
        "If SEC is not set, this link changes after redeploy. "
        "Set SEC in Railway Variables to keep it stable.",
        subscription_url,
    )
    try:
        yield
    finally:
        await health.stop_background_tasks()


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

def _uuid_matches(value: str) -> bool:
    try:
        return uuid.UUID(value) == IDENTITY_UUID
    except Exception:
        return False

@app.get("/")
async def root():
    return PlainTextResponse("FreeNET")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/vless/{client_uuid}")
async def websocket_vless(ws: WebSocket, client_uuid: str):
    if not _uuid_matches(client_uuid):
        await ws.close(code=1008, reason="Invalid UUID")
        return
    await health.handle_vless(ws, IDENTITY_UUID.bytes)

async def _handle_xhttp_request(client_uuid: str, request: Request):
    if not _uuid_matches(client_uuid):
        return Response(content="Not Found", status_code=404)
    return await health.handle_xhttp(request, IDENTITY_UUID.bytes)


def _public_host(request: Request) -> str:
    forwarded_host = request.headers.get("x-forwarded-host")
    host = (forwarded_host or request.headers.get("host") or "localhost").split(",", 1)[0].strip()
    if host.startswith("["):
        closing_bracket = host.find("]")
        if closing_bracket != -1:
            return host[1:closing_bracket]
    if host.count(":") == 1:
        return host.rsplit(":", 1)[0]
    return host


def _format_host(host: str) -> str:
    return f"[{host}]" if ":" in host else host


def _query_string(parameters: dict[str, str]) -> str:
    return "&".join(
        f"{key}={quote(value, safe='')}" for key, value in parameters.items()
    )


@app.get("/sub/{secret}")
async def subscription(secret: str, request: Request):
    if not secrets.compare_digest(secret, SUBSCRIPTION_SECRET):
        return Response(content="Not Found", status_code=404)

    host = _public_host(request)
    formatted_host = _format_host(host)
    configs = []
    transports = (
        ("ws", None, "FreeNET-VLESS-WS"),
        ("xhttp", "packet-up", "FreeNET-XHTTP-Packet-Up"),
        ("xhttp", "stream-up", "FreeNET-XHTTP-Stream-Up"),
    )
    for transport, mode, name in transports:
        parameters = {
            "encryption": "none",
            "security": "tls",
            "type": transport,
            "host": formatted_host,
            "path": f"/vless/{IDENTITY_UUID}" if transport == "ws" else f"/xhttp/{IDENTITY_UUID}",
            "sni": host,
            "fp": "chrome",
            "alpn": "http/1.1" if transport == "ws" else "h2,http/1.1",
        }
        if mode:
            parameters["mode"] = mode
        configs.append(
            f"vless://{IDENTITY_UUID}@{formatted_host}:443?{_query_string(parameters)}"
        )

    stats = core.get_global_stats()
    status = (
        f"📊 FreeNET • {core.format_uptime(stats.uptime_seconds())} • "
        f"↑{core.format_bytes(stats.total_upload)} "
        f"↓{core.format_bytes(stats.total_download)}"
    )
    configs.append(
        "vless://00000000-0000-0000-0000-000000000000@127.0.0.1:1"
        f"?type=tcp&security=none&encryption=none"
    )
    encoded = base64.b64encode("\n".join(configs).encode("utf-8")).decode("ascii")
    return Response(
        content=encoded,
        media_type="text/plain",
        headers={
            "Cache-Control": "no-store",
            "Profile-Title": base64.b64encode(status.encode("utf-8")).decode("ascii"),
            "Subscription-Userinfo": (
                f"upload={stats.total_upload}; download={stats.total_download}; total=0; expire=0"
            ),
        },
    )

@app.api_route("/xhttp/{client_uuid}", methods=["GET", "POST"])
async def xhttp_base(client_uuid: str, request: Request):
    return await _handle_xhttp_request(client_uuid, request)

@app.api_route("/xhttp/{client_uuid}/{path:path}", methods=["GET", "POST"])
async def xhttp_path(client_uuid: str, request: Request):
    return await _handle_xhttp_request(client_uuid, request)

if __name__ == "__main__":
    import uvicorn
    try:
        port = int(os.environ.get("PORT", "8000"))
    except (TypeError, ValueError):
        port = 8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        workers=1,
    )
