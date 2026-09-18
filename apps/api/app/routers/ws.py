"""WebSocket fan-out. Each socket subscribes to one Redis channel."""

from __future__ import annotations

import asyncio
import json

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redcell_core.bus import bus, chat_channel, events_channel, notifications_channel, shell_channel
from redcell_core.config import settings
from redcell_core.db import session_scope
from redcell_core.logs import get_logger
from redcell_core.repositories import servers as servers_repo
from redcell_core.repositories import session_servers as session_servers_repo
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


@router.websocket("/ws/notifications")
async def ws_notifications(ws: WebSocket) -> None:
    if not _authed(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    await _pump(ws, notifications_channel())


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
        except WebSocketDisconnect:
            return
        except Exception:
            get_logger("api.ws").exception("noVNC bridge write error")
            return

    tasks = {asyncio.create_task(to_ws()), asyncio.create_task(to_proc())}
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        # Runs even if the bridge itself is cancelled, so the docker exec never leaks.
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        try:
            proc.kill()
        except Exception:
            pass
        try:
            await proc.wait()
        except Exception:
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


_DEVICE_SERIAL = "127.0.0.1:5555"


async def _ssh_connect(host: str, user: str, secret: str | None):
    from redcell_core.engine import ssh
    return await ssh.connect(host, username=user or "root", secret=secret)


def _adb_input(action: dict) -> str | None:
    kind = str(action.get("type") or "")
    base = f"adb -s {_DEVICE_SERIAL} shell input"
    if kind == "tap":
        return f"{base} tap {int(action['x'])} {int(action['y'])}"
    if kind == "swipe":
        return f"{base} swipe {int(action['x1'])} {int(action['y1'])} {int(action['x2'])} {int(action['y2'])}"
    if kind == "text":
        text = str(action.get("text") or "").replace("'", "")
        return f"{base} text '{text}'"
    if kind == "key":
        key = str(action.get("key") or "").replace("'", "")
        return f"{base} keyevent '{key}'"
    return None


async def _local_run(argv: list[str]) -> bytes:
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    assert proc.stdout is not None
    out = await proc.stdout.read()
    await proc.wait()
    return out


@router.websocket("/ws/device/{session_id}")
async def ws_device(ws: WebSocket, session_id: str) -> None:
    """Stream the Android device's screen (periodic screencap PNGs) and forward
    operator tap/text/key input. Works over SSH to an attached mobile device host,
    or against the local deployment host (local-first) when none is attached."""
    from redcell_core.capabilities import host_capabilities

    if not _authed(ws):
        await ws.close(code=4401)
        return
    async with session_scope() as s:
        session = await sessions_repo.get(s, session_id)
        if session is None:
            await ws.close(code=4404)
            return
        row = await session_servers_repo.get_by_role(s, session_id, "mobile")
        server = secret = None
        if row is not None:
            server = await servers_repo.get(s, row.server_id)
            secret = await servers_repo.get_secret(s, row.server_id)

    container = f"redcell-exec-{session_id[:12]}"
    cap = (f"adb connect {_DEVICE_SERIAL} >/dev/null 2>&1; "
           f"adb -s {_DEVICE_SERIAL} exec-out screencap -p")

    conn = None
    if server is not None:
        try:
            conn = await _ssh_connect(server.host, getattr(server, "username", None) or "root", secret)
        except Exception:
            await ws.close(code=1011)
            return
    else:
        caps = await host_capabilities()
        if not caps["features"]["dynamic_mobile"]["available"]:
            await ws.close(code=4403)  # no device host, and this host can't run one
            return

    async def capture() -> bytes:
        if conn is not None:
            r = await conn.run(f"docker exec {container} sh -c {json.dumps(cap)}", encoding=None, check=False)
            return r.stdout or b""
        return await _local_run(["docker", "exec", container, "sh", "-c", cap])

    async def send(cmd: str) -> None:
        if conn is not None:
            await conn.run(f"docker exec {container} sh -c {json.dumps(cmd)}", check=False)
        else:
            await _local_run(["docker", "exec", container, "sh", "-c", cmd])

    await ws.accept()

    async def stream() -> None:
        while True:
            frame = await capture()
            if frame[:8] == b"\x89PNG\r\n\x1a\n":
                await ws.send_bytes(frame)
            await asyncio.sleep(0.35)

    async def control() -> None:
        try:
            while True:
                msg = await ws.receive_text()
                try:
                    action = json.loads(msg)
                except json.JSONDecodeError:
                    continue
                cmd = _adb_input(action)
                if cmd:
                    await send(cmd)
        except WebSocketDisconnect:
            return
        except Exception:
            return

    tasks = {asyncio.create_task(stream()), asyncio.create_task(control())}
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if conn is not None:
            conn.close()
