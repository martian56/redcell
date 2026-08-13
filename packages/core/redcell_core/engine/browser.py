"""Session-scoped browser control. Boots the in-container browser stack lazily
(rc-browserd) and drives it through the rc-browser helper via backend.run, the
same path every other tool uses. While the operator holds control through the VNC
bridge, agent actions no-op so the two never fight for the cursor."""

from __future__ import annotations

import json
import shlex
from typing import Any


class BrowserManager:
    def __init__(self, backend: Any, session_id: str, bus: Any = None) -> None:
        self.backend = backend
        self.session_id = session_id
        self.bus = bus
        self.owner = "agent"
        self._started = False

    def set_owner(self, owner: str) -> None:
        self.owner = "operator" if owner == "operator" else "agent"

    async def ensure_started(self) -> None:
        if self._started:
            return
        await self.backend.run("rc-browserd start")
        self._started = True

    async def stop(self) -> None:
        if not self._started:
            return
        try:
            await self.backend.run("rc-browserd stop")
        finally:
            self._started = False

    async def _action(self, *parts: str) -> dict[str, Any]:
        if self.owner == "operator":
            return {"status": "operator_has_control"}
        await self.ensure_started()
        cmd = "rc-browser " + " ".join(shlex.quote(p) for p in parts)
        res = await self.backend.run(cmd)
        return _parse_json(getattr(res, "output", res))

    async def open(self, url: str) -> dict[str, Any]:
        return await self._action("open", url)

    async def click(self, selector: str) -> dict[str, Any]:
        return await self._action("click", selector)

    async def type(self, selector: str, text: str, submit: bool = False) -> dict[str, Any]:
        parts = ["type", selector, text]
        if submit:
            parts.append("--submit")
        return await self._action(*parts)

    async def read(self) -> dict[str, Any]:
        return await self._action("read")

    async def screenshot(self) -> dict[str, Any]:
        return await self._action("screenshot")


def _parse_json(output: Any) -> dict[str, Any]:
    """rc-browser prints one JSON line. Scan from the last non-empty line so any
    startup log noise ahead of it is ignored."""
    text = output if isinstance(output, str) else str(output)
    for line in reversed([ln for ln in text.splitlines() if ln.strip()]):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return {"ok": False, "error": "no JSON from rc-browser", "raw": text[:300]}
