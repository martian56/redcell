"""On-demand ngrok TCP tunnels for reverse-shell listeners. Each armed listener
gets its own ngrok agent process tunnelling to the local listener port; the
assigned public address is parsed from the agent's json logs, so ephemeral
free-tier addresses work without assuming a reserved endpoint."""

from __future__ import annotations

import asyncio
import json

from ..logs import get_logger

log = get_logger("ngrok")

_URL_TIMEOUT = 30.0


class NgrokError(RuntimeError):
    pass


class NgrokManager:
    def __init__(self) -> None:
        self._procs: dict[str, asyncio.subprocess.Process] = {}

    async def open(self, listener_id: str, port: int, token: str) -> str:
        await self.close(listener_id)
        try:
            proc = await asyncio.create_subprocess_exec(
                "ngrok", "tcp", str(port), "--authtoken", token,
                "--log", "stdout", "--log-format", "json", "--log-level", "info",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        except FileNotFoundError as exc:
            raise NgrokError("ngrok is not installed on the worker") from exc
        self._procs[listener_id] = proc
        try:
            public = await asyncio.wait_for(self._read_public_url(proc), timeout=_URL_TIMEOUT)
        except (TimeoutError, NgrokError):
            await self.close(listener_id)
            raise
        if not public:
            await self.close(listener_id)
            raise NgrokError("ngrok exited before publishing a tunnel address")
        return public

    async def close(self, listener_id: str) -> None:
        proc = self._procs.pop(listener_id, None)
        if proc is None:
            return
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except TimeoutError:
                proc.kill()

    async def close_all(self) -> None:
        for lid in list(self._procs):
            await self.close(lid)

    async def _read_public_url(self, proc: asyncio.subprocess.Process) -> str | None:
        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                return None
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            err = rec.get("err")
            if err and err != "<nil>":
                raise NgrokError(str(err))
            url = rec.get("url", "")
            if isinstance(url, str) and url.startswith("tcp://"):
                return url[len("tcp://"):]
