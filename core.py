from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

__all__ = [
    "Target",
    "Stats",
    "Relay",
    "get_stats",
    "get_global_stats",
    "open_target",
    "relay_to_target",
    "tcp_receive",
    "tcp_send",
    "tcp_close",
    "format_bytes",
    "format_uptime",
]

DEFAULT_CHUNK_SIZE = 16 * 1024
DEFAULT_CONNECT_TIMEOUT = 10.0

_PROCESS_START_MONOTONIC = time.monotonic()


def format_bytes(value: int) -> str:
    try:
        value = int(value)
    except Exception:
        value = 0

    if value < 0:
        value = 0

    if value < 1024:
        return f"{value}B"

    scaled = float(value)
    units = ("KB", "MB", "GB", "TB", "PB", "EB")

    for unit in units:
        scaled /= 1024.0
        if scaled < 1024.0 or unit == units[-1]:
            return f"{scaled:.1f}{unit}"

    return f"{scaled:.1f}EB"


def format_uptime(seconds: float) -> str:
    try:
        seconds = int(seconds)
    except Exception:
        seconds = 0

    if seconds < 0:
        seconds = 0

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    if days:
        return f"{days}d {hours:02d}h" if hours else f"{days}d"
    if hours:
        return f"{hours}h {minutes:02d}m" if minutes else f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return "0m"


class Stats:
    """Track aggregate traffic counters for the lifetime of this process."""

    def __init__(self) -> None:
        self._start_time = _PROCESS_START_MONOTONIC
        self.total_upload = 0
        self.total_download = 0

    def add_upload(self, size: int) -> None:
        try:
            size = int(size)
        except Exception:
            return

        if size <= 0:
            return

        self.total_upload += size

    def add_download(self, size: int) -> None:
        try:
            size = int(size)
        except Exception:
            return

        if size <= 0:
            return

        self.total_download += size

    def uptime_seconds(self) -> float:
        return max(0.0, time.monotonic() - self._start_time)


_global_stats: Optional[Stats] = None


def get_global_stats() -> Stats:
    global _global_stats
    if _global_stats is None:
        _global_stats = Stats()
    return _global_stats


def get_stats() -> Dict[str, str]:
    stats = get_global_stats()
    return {
        "uptime": format_uptime(stats.uptime_seconds()),
        "upload": format_bytes(stats.total_upload),
        "download": format_bytes(stats.total_download),
    }


@dataclass(frozen=True)
class Target:
    host: str
    port: int
    network: str = "tcp"

    def __post_init__(self) -> None:
        host = str(self.host).strip()
        if not host:
            raise ValueError("Target host is required")

        try:
            port = int(self.port)
        except Exception as exc:
            raise ValueError("Target port is invalid") from exc

        if not (0 < port <= 65535):
            raise ValueError("Target port is invalid")

        network = str(self.network).strip().lower()
        if network != "tcp":
            raise ValueError("Only TCP targets are supported")

        object.__setattr__(self, "host", host)
        object.__setattr__(self, "port", port)
        object.__setattr__(self, "network", network)


async def open_target(
    target: Target,
    timeout: Optional[float] = DEFAULT_CONNECT_TIMEOUT,
) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    if target.network != "tcp":
        raise ValueError("Only TCP targets are supported")

    connection = asyncio.open_connection(target.host, target.port)
    if timeout is None:
        return await connection

    return await asyncio.wait_for(connection, timeout)


async def _safe_close(close: Any) -> None:
    if close is None:
        return

    try:
        if inspect.isawaitable(close):
            await close
            return

        if callable(close):
            result = close()
            if inspect.isawaitable(result):
                await result
    except asyncio.CancelledError:
        raise
    except Exception:
        pass


def tcp_receive(
    reader: asyncio.StreamReader,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Callable[[], Awaitable[bytes]]:
    try:
        chunk_size = int(chunk_size)
    except Exception:
        chunk_size = DEFAULT_CHUNK_SIZE

    chunk_size = max(1, chunk_size)

    async def receive() -> bytes:
        return await reader.read(chunk_size)

    return receive


def tcp_send(
    writer: asyncio.StreamWriter,
) -> Callable[[bytes], Awaitable[None]]:
    async def send(data: bytes) -> None:
        if not data:
            return
        writer.write(data)
        await writer.drain()

    return send


def tcp_close(
    writer: asyncio.StreamWriter,
) -> Callable[[], Awaitable[None]]:
    async def close() -> None:
        try:
            if writer is None:
                return
            if not writer.is_closing():
                writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    return close


class Relay:
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        stats: Optional[Stats] = None,
    ) -> None:
        try:
            chunk_size = int(chunk_size)
        except Exception:
            chunk_size = DEFAULT_CHUNK_SIZE

        self.chunk_size = max(512, chunk_size)
        self._stats = stats or get_global_stats()

    async def _pipe(
        self,
        receive: Callable[[], Awaitable[Any]],
        send: Callable[[bytes], Awaitable[Any]],
        add: Callable[[int], None],
    ) -> None:
        while True:
            try:
                data = await receive()
            except asyncio.CancelledError:
                raise
            except Exception:
                break

            try:
                if data is None:
                    break

                if isinstance(data, bytes):
                    pass
                elif isinstance(data, str):
                    data = data.encode("utf-8", "ignore")
                elif isinstance(data, (bytearray, memoryview)):
                    data = bytes(data)
                else:
                    try:
                        data = bytes(data)
                    except Exception:
                        break

                if not data:
                    break

                await send(data)
            except asyncio.CancelledError:
                raise
            except Exception:
                break

            try:
                add(len(data))
            except Exception:
                pass

    async def run(
        self,
        *,
        client_receive: Callable[[], Awaitable[Any]],
        client_send: Callable[[bytes], Awaitable[Any]],
        target_receive: Callable[[], Awaitable[Any]],
        target_send: Callable[[bytes], Awaitable[Any]],
        client_close: Optional[Callable[[], Any]] = None,
        target_close: Optional[Callable[[], Any]] = None,
    ) -> None:
        upload_task = asyncio.create_task(
            self._pipe(client_receive, target_send, self._stats.add_upload),
            name="relay-upload",
        )
        download_task = asyncio.create_task(
            self._pipe(target_receive, client_send, self._stats.add_download),
            name="relay-download",
        )

        tasks = (upload_task, download_task)
        cancelled = False

        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        except asyncio.CancelledError:
            cancelled = True
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                cancelled = True
            except Exception:
                pass

            try:
                try:
                    await _safe_close(client_close)
                except asyncio.CancelledError:
                    cancelled = True
            finally:
                try:
                    await _safe_close(target_close)
                except asyncio.CancelledError:
                    cancelled = True

            if cancelled:
                raise asyncio.CancelledError()


async def relay_to_target(
    target: Target,
    *,
    client_receive: Callable[[], Awaitable[Any]],
    client_send: Callable[[bytes], Awaitable[Any]],
    client_close: Optional[Callable[[], Any]] = None,
    timeout: Optional[float] = DEFAULT_CONNECT_TIMEOUT,
    relay: Optional[Relay] = None,
) -> None:
    relay = relay or Relay()

    target_reader, target_writer = await open_target(target, timeout)

    await relay.run(
        client_receive=client_receive,
        client_send=client_send,
        client_close=client_close,
        target_receive=tcp_receive(target_reader, relay.chunk_size),
        target_send=tcp_send(target_writer),
        target_close=tcp_close(target_writer),
    )
