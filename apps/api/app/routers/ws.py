"""WebSocket fan-out. Each socket subscribes to one Redis channel."""

from __future__ import annotations

import asyncio

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redcell_core.bus import bus, chat_channel, events_channel, shell_channel
from redcell_core.config import settings
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
