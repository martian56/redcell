"""WebSocket fan-out. Each socket subscribes to one Redis channel."""

from __future__ import annotations

import asyncio

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redcell_core.bus import bus, chat_channel, events_channel, shell_channel
from redcell_core.config import settings
from redcell_core.db import session_scope
from redcell_core.repositories import sessions as sessions_repo
from redcell_core.security import COOKIE_NAME

router = APIRouter()


def _authed(ws: WebSocket) -> bool:
    token = ws.cookies.get(COOKIE_NAME)
    if not token:
        return False
    try:
        jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return True
    except jwt.PyJWTError:
        return False


async def _forward(ws: WebSocket, channel: str) -> None:
    async for payload in bus.subscribe(channel):
        await ws.send_text(payload)


async def _drain(ws: WebSocket) -> None:
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        return


async def _pump(ws: WebSocket, channel: str) -> None:
    forward = asyncio.create_task(_forward(ws, channel))
    drain = asyncio.create_task(_drain(ws))
    _, pending = await asyncio.wait({forward, drain}, return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()
    for t in pending:
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass


@router.websocket("/ws/events/{run_id}")
async def ws_events(ws: WebSocket, run_id: str) -> None:
    if not _authed(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    await _pump(ws, events_channel(run_id))


@router.websocket("/ws/chat/{run_id}")
async def ws_chat(ws: WebSocket, run_id: str) -> None:
    if not _authed(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    await _pump(ws, chat_channel(run_id))


@router.websocket("/ws/shell/{shell_id}")
async def ws_shell(ws: WebSocket, shell_id: str) -> None:
    if not _authed(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    await _pump(ws, shell_channel(shell_id))


async def _bridge(ws: WebSocket, proc: asyncio.subprocess.Process) -> None:
    """Pump raw bytes both ways between the noVNC client and the container's VNC
    server (RFB over the WebSocket)."""
    async def to_ws() -> None:
        assert proc.stdout is not None
        while True:
            chunk = await proc.stdout.read(65536)
            if not chunk:
                break
            await ws.send_bytes(chunk)

    async def to_proc() -> None:
        assert proc.stdin is not None
        try:
            while True:
                data = await ws.receive_bytes()
                proc.stdin.write(data)
                await proc.stdin.drain()
        except (WebSocketDisconnect, Exception):
            return

    t1 = asyncio.create_task(to_ws())
    t2 = asyncio.create_task(to_proc())
    _, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()
    try:
        proc.kill()
    except Exception:
        pass
    for t in pending:
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass


@router.websocket("/ws/browser/{session_id}")
async def ws_browser(ws: WebSocket, session_id: str) -> None:
    """Bridge a noVNC client to the session container's x11vnc via `docker exec`.
    Local sessions only for now; remote-server sessions are a follow-up."""
    if not _authed(ws):
        await ws.close(code=4401)
        return
    async with session_scope() as s:
        session = await sessions_repo.get(s, session_id)
    if session is None:
        await ws.close(code=4404)
        return
    if session.server_id:
        await ws.close(code=4403)  # live view for remote servers not supported yet
        return
    container = f"redcell-exec-{session_id[:12]}"
    await ws.accept()
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", "-i", container, "socat", "-", "TCP:127.0.0.1:5900",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except Exception:
        await ws.close(code=1011)
        return
    await _bridge(ws, proc)
