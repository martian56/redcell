"""Reverse-shell catcher. Opens TCP listeners; a caught callback is registered as
a reverse shell whose output streams onto `shell:{id}` and whose input arrives on
`shellin:{id}`. A caught session also raises an event on the owning run."""

from __future__ import annotations

import asyncio

from ..bus import Bus, events_channel, shell_channel, shell_input_channel
from ..db import session_scope
from ..repositories import ids
from ..repositories import listeners as listeners_repo
from ..repositories import sessions as sessions_repo
from ..repositories import shells as shells_repo


class ListenerManager:
    def __init__(self, bus: Bus) -> None:
        self.bus = bus
        self._servers: dict[str, asyncio.AbstractServer] = {}

    async def start(self, listener_id: str) -> str:
        async with session_scope() as s:
            listener = await listeners_repo.get(s, listener_id)
            if listener is None:
                return "error"
            session_id, bind = listener.session_id, listener.bind
        host, _, port_s = bind.rpartition(":")
        host = host or "0.0.0.0"
        try:
            port = int(port_s)
        except ValueError:
            await self._set_status(listener_id, "error")
            return "error"
        try:
            server = await asyncio.start_server(
                lambda r, w: self._on_connect(listener_id, session_id, r, w), host, port)
        except OSError:
            await self._set_status(listener_id, "error")
            return "error"
        self._servers[listener_id] = server
        await self._set_status(listener_id, "listening")
        return "listening"

    async def stop(self, listener_id: str) -> None:
        server = self._servers.pop(listener_id, None)
        if server is not None:
            server.close()
            await server.wait_closed()

    async def stop_all(self) -> None:
        for lid in list(self._servers):
            await self.stop(lid)

    async def _on_connect(self, listener_id: str, session_id: str,
                          reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        remote = f"{peer[0]}:{peer[1]}" if peer else "unknown"
        async with session_scope() as s:
            shell = await shells_repo.create(s, {"session_id": session_id, "kind": "reverse",
                                                 "label": f"revsh {remote}", "status": "running",
                                                 "host": remote, "remote_addr": remote, "pty": True})
            listener = await listeners_repo.get(s, listener_id)
            if listener:
                listener.sessions_count += 1
            shell_id = shell.id
        await self._announce(session_id, f"caught reverse shell from {remote}")

        outbound = asyncio.create_task(self._pump_out(shell_id, reader))
        inbound = asyncio.create_task(self._pump_in(shell_id, writer))
        try:
            await asyncio.wait({outbound, inbound}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            outbound.cancel()
            inbound.cancel()
            async with session_scope() as s:
                await shells_repo.set_status(s, shell_id, "closed")
            writer.close()

    async def _pump_out(self, shell_id: str, reader: asyncio.StreamReader) -> None:
        while True:
            data = await reader.read(4096)
            if not data:
                return
            await self.bus.publish(shell_channel(shell_id), data.decode(errors="replace"))

    async def _pump_in(self, shell_id: str, writer: asyncio.StreamWriter) -> None:
        async for keystrokes in self.bus.subscribe(shell_input_channel(shell_id)):
            writer.write(keystrokes.encode())
            await writer.drain()

    async def _set_status(self, listener_id: str, status: str) -> None:
        async with session_scope() as s:
            await listeners_repo.set_status(s, listener_id, status)

    async def _announce(self, session_id: str, text: str) -> None:
        async with session_scope() as s:
            session = await sessions_repo.get(s, session_id)
            run_id = session.active_run_id if session else None
        if not run_id:
            return
        from .. import events as events_bus
        await events_bus.emit(self.bus, run_id, "listener", "net", text)
