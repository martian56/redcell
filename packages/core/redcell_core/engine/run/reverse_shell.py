from __future__ import annotations

import asyncio
import base64
from typing import Any

from ...bus import shell_channel, shell_input_channel
from ...config import settings
from ...db import session_scope
from ...repositories import listeners as listeners_repo
from ...repositories import secrets as secrets_repo
from ...repositories import shells as shells_repo
from .support import _REMOTE_LISTENER_PY, in_callback_range


class ReverseShellMixin:
    async def _start_listener(self, port: int, method: str = "auto") -> dict[str, Any]:
        remote = self.server is not None and getattr(self.backend, "kind", "") == "remote-docker"
        if not remote and not in_callback_range(port):
            return {"error": f"port {port} is outside the reachable callback range "
                    f"{settings.callback_port_min}-{settings.callback_port_max}; "
                    f"retry start_listener with a port in that range."}
        async with session_scope() as s:
            token = await secrets_repo.get_secret(s, secrets_repo.NGROK_AUTHTOKEN)
        if method == "ngrok" and not token:
            return {"error": "ngrok requested but no ngrok auth token is configured "
                    "(Settings > Integrations); use method 'direct' or add a token."}
        use_ngrok = not remote and method != "direct" and (method == "ngrok" or bool(token))
        bind = f"0.0.0.0:{port}"
        async with session_scope() as s:
            listener = await listeners_repo.create(s, {"session_id": self.session_id, "kind": "tcp",
                                                       "bind": bind, "status": "starting", "sessions_count": 0})
            lid = listener.id
        if remote:
            await self._open_remote_listener(port, lid)
            callback = f"{self.server.host}:{port}"
            status = "listening"
        else:
            from ..live import get_listener_manager, get_ngrok_manager
            status = await get_listener_manager().start(lid)
            callback = f"{settings.callback_host}:{port}"
            if use_ngrok and status == "listening":
                try:
                    callback = await get_ngrok_manager().open(lid, port, token)
                except Exception as exc:
                    await self._event("listener", "steer",
                                      f"ngrok tunnel failed, using direct callback: {exc}")
        await self._event("listener", "net", f"listener {bind} ({status}); reverse-shell callback -> {callback}")
        await self._advance_phase("Post-Exploitation")
        return {"listenerId": lid, "bind": bind, "status": status, "callback": callback,
                "note": "Use this callback address (host:port) in the reverse-shell payload."}

    async def _open_remote_listener(self, port: int, listener_id: str) -> None:
        async with session_scope() as s:
            await listeners_repo.set_status(s, listener_id, "listening")
            shell = await shells_repo.create(s, {"session_id": self.session_id, "kind": "reverse",
                                                 "label": f"revsh :{port} @ {self.server.host}",
                                                 "status": "running", "host": self.server.host, "pty": True})
            shell_id = shell.id
        self._listener_tasks.append(
            asyncio.create_task(self._remote_listener_bridge(port, listener_id, shell_id)))

    async def _remote_listener_bridge(self, port: int, listener_id: str, shell_id: str) -> None:
        try:
            conn = await self.backend.connection()
            b64 = base64.b64encode(_REMOTE_LISTENER_PY.encode()).decode()
            inner = f"import base64;exec(base64.b64decode('{b64}'))"
            from ..execution import _shq
            cmd = f"docker exec -i {self.backend.name} python3 -c {_shq(inner)} {int(port)}"
            proc = await conn.create_process(cmd, encoding=None)
        except Exception as exc:
            await self._event("listener", "steer", f"remote listener failed: {exc}")
            async with session_scope() as s:
                await shells_repo.set_status(s, shell_id, "closed")
            return

        async def pump_out() -> None:
            while True:
                data = await proc.stdout.read(4096)
                if not data:
                    break
                await self.bus.publish(shell_channel(shell_id), data.decode(errors="replace"))

        async def pump_in() -> None:
            async for keys in self.bus.subscribe(shell_input_channel(shell_id)):
                try:
                    proc.stdin.write(keys.encode())
                    await proc.stdin.drain()
                except Exception:
                    break

        async def watch() -> None:
            buf = b""
            while True:
                data = await proc.stderr.read(1024)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    text = line.decode(errors="replace").strip()
                    if text.startswith("CONNECT"):
                        remote = text[7:].strip()
                        async with session_scope() as s:
                            sh = await shells_repo.get(s, shell_id)
                            if sh:
                                sh.label = f"revsh {remote}"
                                sh.remote_addr = remote
                            lst = await listeners_repo.get(s, listener_id)
                            if lst:
                                lst.sessions_count += 1
                        await self._event("listener", "net",
                                          f"caught reverse shell from {remote} on {self.server.host}:{port}")
                        await self._advance_phase("Post-Exploitation")

        out_t = asyncio.create_task(pump_out())
        in_t = asyncio.create_task(pump_in())
        try:
            await watch()
            await proc.wait()
        except asyncio.CancelledError:
            raise
        finally:
            out_t.cancel()
            in_t.cancel()
            try:
                proc.close()
            except Exception:
                pass
            async with session_scope() as s:
                await shells_repo.set_status(s, shell_id, "closed")
