"""VLESS transports: WebSocket and XHTTP packet-up/stream-up."""

import asyncio
import ipaddress
import os
import struct
import time
from typing import Dict, Optional
from uuid import UUID

from fastapi import Request, WebSocket
from fastapi.responses import Response, StreamingResponse

from core import Relay, Target, get_global_stats, open_target, relay_to_target

_vless_uuid_str = os.environ.get("VLESS_UUID", "")
try:
    _VLESS_UUID_BYTES = UUID(_vless_uuid_str).bytes if _vless_uuid_str else b""
except ValueError:
    _VLESS_UUID_BYTES = b""


class WSReader:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.buffer = bytearray()

    async def read(self, n: int) -> bytes:
        while len(self.buffer) < n:
            if len(self.buffer) > 4096:
                raise ConnectionError("Header too large")
            try:
                msg = await asyncio.wait_for(self.ws.receive(), timeout=30.0)
            except asyncio.TimeoutError as exc:
                raise ConnectionError("Timeout") from exc
            if msg["type"] == "websocket.disconnect":
                raise ConnectionError("Disconnected")
            if msg["type"] == "websocket.receive":
                if "bytes" in msg and msg["bytes"]:
                    self.buffer.extend(msg["bytes"])
                elif "text" in msg and msg["text"]:
                    raise ConnectionError("Text message not supported")
                else:
                    raise ConnectionError("Empty message")
            else:
                raise ConnectionError("Unexpected message type")
        result = bytes(self.buffer[:n])
        del self.buffer[:n]
        return result

    def get_remaining(self) -> bytes:
        return bytes(self.buffer)


async def handle_vless(ws: WebSocket) -> None:
    await ws.accept()
    reader = WSReader(ws)

    try:
        version = (await reader.read(1))[0]
        if version != 0:
            return

        req_uuid = await reader.read(16)
        if req_uuid != _VLESS_UUID_BYTES:
            return

        opt_len = (await reader.read(1))[0]
        if opt_len > 0:
            await reader.read(opt_len)

        command = (await reader.read(1))[0]
        if command != 0x01:
            return

        port = struct.unpack("!H", await reader.read(2))[0]
        if not 1 <= port <= 65535:
            return

        atyp = (await reader.read(1))[0]
        if atyp == 0x01:
            host = str(ipaddress.IPv4Address(await reader.read(4)))
        elif atyp == 0x02:
            domain_len = (await reader.read(1))[0]
            if domain_len == 0:
                return
            try:
                host = (await reader.read(domain_len)).decode("utf-8")
            except UnicodeDecodeError:
                return
        elif atyp == 0x03:
            host = str(ipaddress.IPv6Address(await reader.read(16)))
        else:
            return

        initial_payload = reader.get_remaining()
    except Exception:
        return

    try:
        target = Target(host=host, port=port, network="tcp")
    except ValueError:
        return

    try:
        await ws.send_bytes(b"\x00\x00")
    except Exception:
        return

    initial_sent = False

    async def client_receive():
        nonlocal initial_sent
        if not initial_sent:
            initial_sent = True
            if initial_payload:
                return initial_payload

        while True:
            try:
                msg = await ws.receive()
            except Exception:
                return None
            if msg["type"] == "websocket.disconnect":
                return None
            if msg["type"] == "websocket.receive":
                if "bytes" in msg:
                    return msg["bytes"] or None
                if "text" in msg:
                    continue
            return None

    async def client_send(data: bytes):
        try:
            await ws.send_bytes(data)
        except Exception:
            pass

    async def client_close():
        try:
            await ws.close()
        except Exception:
            pass

    try:
        await relay_to_target(
            target,
            client_receive=client_receive,
            client_send=client_send,
            client_close=client_close,
            timeout=10.0,
            relay=Relay(),
        )
    except Exception:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


MAX_SESSIONS = 10000
MAX_SEQ_GAP = 1000
MAX_PACKET_SIZE = 2 * 1024 * 1024
MAX_HEADER_SIZE = 4096
MAX_BUFFERED_BYTES = 8 * 1024 * 1024
SESSION_TIMEOUT = 300

_sessions: Dict[str, "XHTTPSession"] = {}
_cleanup_task_started = False


def _parse_vless_header(data: bytes):
    if len(data) < 18 or data[0] != 0 or data[1:17] != _VLESS_UUID_BYTES:
        return None, None, None
    opt_len = data[17]
    offset = 18 + opt_len
    if len(data) < offset + 4 or data[offset] != 0x01:
        return None, None, None
    port = struct.unpack("!H", data[offset + 1 : offset + 3])[0]
    atyp = data[offset + 3]
    offset += 4

    if atyp == 0x01:
        if len(data) < offset + 4:
            return None, None, None
        host = str(ipaddress.IPv4Address(data[offset : offset + 4]))
        offset += 4
    elif atyp == 0x02:
        if len(data) < offset + 1:
            return None, None, None
        domain_len = data[offset]
        offset += 1
        if len(data) < offset + domain_len:
            return None, None, None
        try:
            host = data[offset : offset + domain_len].decode("utf-8")
        except UnicodeDecodeError:
            return None, None, None
        offset += domain_len
    elif atyp == 0x03:
        if len(data) < offset + 16:
            return None, None, None
        host = str(ipaddress.IPv6Address(data[offset : offset + 16]))
        offset += 16
    else:
        return None, None, None

    return host, port, data[offset:]


async def _target_pump(reader: asyncio.StreamReader, queue: asyncio.Queue, stats):
    try:
        while True:
            data = await reader.read(16384)
            if not data:
                break
            stats.add_download(len(data))
            await queue.put(data)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
    finally:
        try:
            queue.put_nowait(None)
        except asyncio.QueueFull:
            pass


class XHTTPSession:
    def __init__(self, session_id: str, mode: str):
        self.session_id = session_id
        self.mode = mode
        self.created_at = time.time()
        self.last_seen = time.time()
        self.target_reader: Optional[asyncio.StreamReader] = None
        self.target_writer: Optional[asyncio.StreamWriter] = None
        self.target_connected = False
        self.downlink_queue: asyncio.Queue = asyncio.Queue(maxsize=1024)
        self.downlink_connected = False
        self.downlink_task: Optional[asyncio.Task] = None
        self.next_seq = 0
        self.seq_buf: Dict[int, bytes] = {}
        self.buffered_bytes = 0
        self.closed = False
        self._lock = asyncio.Lock()

    async def close(self):
        if self.closed:
            return
        self.closed = True
        if self.downlink_task and not self.downlink_task.done():
            self.downlink_task.cancel()
        if self.target_writer:
            try:
                self.target_writer.close()
                await self.target_writer.wait_closed()
            except Exception:
                pass
        try:
            self.downlink_queue.put_nowait(None)
        except asyncio.QueueFull:
            pass


async def _cleanup_sessions():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        dead = [sid for sid, session in _sessions.items() if now - session.last_seen > SESSION_TIMEOUT]
        for sid in dead:
            session = _sessions.pop(sid, None)
            if session:
                await session.close()


def _ensure_cleanup():
    global _cleanup_task_started
    if not _cleanup_task_started:
        asyncio.create_task(_cleanup_sessions())
        _cleanup_task_started = True


async def handle_xhttp(request: Request):
    _ensure_cleanup()
    stats = get_global_stats()
    path = request.scope.get("path", "")
    parts = [part for part in path.split("/") if part]
    session_id = parts[2] if len(parts) >= 3 else request.query_params.get("session_id")
    seq_str = parts[3] if len(parts) >= 4 else request.query_params.get("seq")
    mode = request.query_params.get("mode", "packet-up")

    if not session_id:
        return Response(content="Missing session_id", status_code=400)
    if len(session_id) < 8 or len(session_id) > 128:
        return Response(content="Invalid session_id", status_code=400)

    session = _sessions.get(session_id)
    if not session:
        if len(_sessions) >= MAX_SESSIONS:
            return Response(content="Too many sessions", status_code=503)
        session = XHTTPSession(session_id, mode)
        _sessions[session_id] = session

    session.last_seen = time.time()
    method = request.method

    if method == "GET":
        if session.downlink_connected:
            return Response(content="Downlink already connected", status_code=409)
        session.downlink_connected = True

        async def downlink_stream():
            try:
                while True:
                    chunk = await session.downlink_queue.get()
                    if chunk is None:
                        break
                    yield chunk
            except asyncio.CancelledError:
                pass
            finally:
                session.downlink_connected = False
                asyncio.create_task(session.close())

        return StreamingResponse(
            downlink_stream(),
            media_type="application/octet-stream",
            headers={
                "Cache-Control": "no-cache, no-store",
                "X-Accel-Buffering": "no",
                "Transfer-Encoding": "chunked",
            },
        )

    if method != "POST":
        return Response(content="Method not allowed", status_code=405)

    if mode == "packet-up":
        body = bytearray()
        try:
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > MAX_PACKET_SIZE:
                    await session.close()
                    return Response(content="Packet too large", status_code=413)
        except asyncio.CancelledError:
            await session.close()
            raise
        except Exception:
            await session.close()
            return Response(content="Upload error", status_code=400)

        if seq_str is None and session.target_connected:
            return Response(content="Missing seq", status_code=400)
        try:
            seq = int(seq_str) if seq_str is not None else 0
            if seq < 0:
                return Response(content="Invalid seq", status_code=400)
        except ValueError:
            return Response(content="Invalid seq", status_code=400)

        async with session._lock:
            if session.closed:
                return Response(content="Session closed", status_code=410)
            if not session.target_connected:
                if seq == 0:
                    host, port, payload = _parse_vless_header(bytes(body))
                    if not host:
                        await session.close()
                        return Response(content="Invalid VLESS header", status_code=400)
                    try:
                        target = Target(host=host, port=port, network="tcp")
                        reader, writer = await open_target(target, timeout=10.0)
                        session.target_reader = reader
                        session.target_writer = writer
                        session.target_connected = True
                        session.downlink_task = asyncio.create_task(
                            _target_pump(reader, session.downlink_queue, stats)
                        )
                        if payload:
                            stats.add_upload(len(payload))
                            writer.write(payload)
                            await writer.drain()
                        session.next_seq = 1
                        while session.next_seq in session.seq_buf:
                            data = session.seq_buf.pop(session.next_seq)
                            session.buffered_bytes -= len(data)
                            stats.add_upload(len(data))
                            writer.write(data)
                            await writer.drain()
                            session.next_seq += 1
                    except Exception:
                        await session.close()
                        return Response(content="Target connect failed", status_code=502)
                else:
                    if seq - 1 > MAX_SEQ_GAP:
                        await session.close()
                        return Response(content="Sequence gap too large", status_code=400)
                    if session.buffered_bytes + len(body) > MAX_BUFFERED_BYTES:
                        await session.close()
                        return Response(content="Buffer limit exceeded", status_code=400)
                    session.seq_buf[seq] = bytes(body)
                    session.buffered_bytes += len(body)
            elif seq < session.next_seq:
                pass
            elif seq == session.next_seq:
                stats.add_upload(len(body))
                session.target_writer.write(bytes(body))
                await session.target_writer.drain()
                session.next_seq += 1
                while session.next_seq in session.seq_buf:
                    data = session.seq_buf.pop(session.next_seq)
                    session.buffered_bytes -= len(data)
                    stats.add_upload(len(data))
                    session.target_writer.write(data)
                    await session.target_writer.drain()
                    session.next_seq += 1
            else:
                if seq - session.next_seq > MAX_SEQ_GAP:
                    await session.close()
                    return Response(content="Sequence gap too large", status_code=400)
                if session.buffered_bytes + len(body) > MAX_BUFFERED_BYTES:
                    await session.close()
                    return Response(content="Buffer limit exceeded", status_code=400)
                session.seq_buf[seq] = bytes(body)
                session.buffered_bytes += len(body)
        return Response(content='{"ok":true}', media_type="application/json")

    if mode == "stream-up":
        if not session.target_connected:
            header_buf = bytearray()
            header_parsed = False
            try:
                async for chunk in request.stream():
                    if not chunk:
                        break
                    if not header_parsed:
                        header_buf.extend(chunk)
                        host, port, payload = _parse_vless_header(bytes(header_buf))
                        if host is not None:
                            header_parsed = True
                            try:
                                target = Target(host=host, port=port, network="tcp")
                                reader, writer = await open_target(target, timeout=10.0)
                                session.target_reader = reader
                                session.target_writer = writer
                                session.target_connected = True
                                session.downlink_task = asyncio.create_task(
                                    _target_pump(reader, session.downlink_queue, stats)
                                )
                                if payload:
                                    stats.add_upload(len(payload))
                                    writer.write(payload)
                                    await writer.drain()
                            except Exception:
                                await session.close()
                                return Response(content="Target connect failed", status_code=502)
                        elif len(header_buf) > MAX_HEADER_SIZE:
                            await session.close()
                            return Response(content="Header too large or invalid", status_code=400)
                    else:
                        stats.add_upload(len(chunk))
                        session.target_writer.write(chunk)
                        await session.target_writer.drain()
            except asyncio.CancelledError:
                await session.close()
                raise
            except Exception:
                await session.close()
                return Response(content="Stream error", status_code=400)

            if not header_parsed:
                await session.close()
                return Response(content="Invalid VLESS header", status_code=400)
        else:
            try:
                async for chunk in request.stream():
                    if not chunk:
                        break
                    stats.add_upload(len(chunk))
                    session.target_writer.write(chunk)
                    await session.target_writer.drain()
            except asyncio.CancelledError:
                await session.close()
                raise
            except Exception:
                await session.close()
                return Response(content="Stream error", status_code=502)

        if session.target_connected and session.target_writer:
            try:
                session.target_writer.close()
                await session.target_writer.wait_closed()
            except Exception:
                pass
        return Response(content='{"ok":true}', media_type="application/json")

    return Response(content="Unsupported mode", status_code=400)
