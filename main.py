import os
import sys
import json
import uuid
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import PlainTextResponse, Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FreeNET")

DATA_DIR = Path(os.environ.get("FREENET_DATA_DIR") or "/data")
os.environ["FREENET_DATA_DIR"] = str(DATA_DIR)
IDENTITY_PATH = DATA_DIR / "identity.json"

def load_or_create_identity() -> dict:
    if not DATA_DIR.exists() or not DATA_DIR.is_dir():
        logger.error(
            "Data directory %s is not available. A persistent volume is required.",
            DATA_DIR,
        )
        sys.exit(1)

    if IDENTITY_PATH.exists():
        try:
            with open(IDENTITY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Identity is not a JSON object")
            if not isinstance(data.get("uuid"), str):
                raise ValueError("Missing or invalid UUID")
            parsed_uuid = uuid.UUID(data["uuid"])
            identity = {"uuid": str(parsed_uuid)}
            if data != identity:
                tmp_path = IDENTITY_PATH.with_name(IDENTITY_PATH.name + ".tmp")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(identity, f, indent=2)
                os.chmod(tmp_path, 0o600)
                os.replace(tmp_path, IDENTITY_PATH)
            return identity
        except Exception as e:
            logger.error(
                "Identity file is corrupted or invalid. Refusing to regenerate to protect existing links. Error: %s",
                e,
            )
            sys.exit(1)

    logger.info("Generating new identity...")
    identity = {"uuid": str(uuid.uuid4())}
    tmp_path = IDENTITY_PATH.with_name(IDENTITY_PATH.name + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(identity, f, indent=2)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, IDENTITY_PATH)
    except Exception as e:
        logger.error(
            "Failed to persist identity file. Refusing to start with ephemeral identity. Error: %s",
            e,
        )
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
        sys.exit(1)
    return identity

IDENTITY = load_or_create_identity()
os.environ["VLESS_UUID"] = IDENTITY["uuid"]

try:
    _IDENTITY_UUID = uuid.UUID(IDENTITY["uuid"])
except Exception as e:
    logger.error("Invalid identity UUID. Error: %s", e)
    sys.exit(1)

import protocols
import core

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

def _uuid_matches(value: str) -> bool:
    try:
        return uuid.UUID(value) == _IDENTITY_UUID
    except Exception:
        return False

@app.on_event("startup")
async def startup() -> None:
    logger.info("FreeNET started")

@app.get("/")
async def root():
    return PlainTextResponse("FreeNET")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/vless/{client_uuid}")
async def ws_vless(ws: WebSocket, client_uuid: str):
    if not _uuid_matches(client_uuid):
        await ws.close(code=1008, reason="Invalid UUID")
        return
    await protocols.handle_vless(ws)

async def _handle_xhttp_request(client_uuid: str, request: Request):
    if not _uuid_matches(client_uuid):
        return Response(content="Not Found", status_code=404)
    return await protocols.handle_xhttp(request)

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
