"""Simulator: the default (sim) live producer. Publishes events, chat questions,
and shell output onto the bus every tick while a run is 'running', using the same
channels as the live engine (runner.py)."""

from __future__ import annotations

import asyncio
import random

from ..bus import Bus, chat_channel, shell_channel
from ..db import session_scope
from ..repositories import chat as chat_repo
from ..repositories import runs as runs_repo
from ..repositories import shells as shells_repo

EVENT_TEMPLATES = [
    ("web-exploit", "tool", 'sqlmap -u ".../search?q=1" --batch --dump'),
    ("recon", "net", "httpx: 12 new endpoints discovered"),
    ("auth-tester", "tool", "jwt_tool: testing alg=none bypass"),
    ("idor-hunter", "net", "enumerating /api/v2/orders/{id}"),
    ("web-exploit", "finding", "candidate: reflected XSS in /search echo"),
    ("orchestrator", "steer", "reprioritizing: focus on auth surface"),
    ("listener", "net", "heartbeat from session #3 (10.0.3.9)"),
]

SHELL_LINES = {
    "reverse": [
        "root@web-01:/var/www/app# ls -la",
        "total 48  drwxr-xr-x 6 www-data www-data 4096 config/",
        "root@web-01:/var/www/app# id",
        "uid=0(root) gid=0(root) groups=0(root)",
    ],
    "tool": [
        "[INFO] testing connection to the target URL",
        "[INFO] parameter 'q' is 'MySQL error-based' injectable",
        "available databases [4]: acme_prod, information_schema, mysql, sys",
    ],
    "interactive": [
        "operator@kali:~/sessions/acme$ ls loot/",
        "creds.txt  users_dump.csv  jwt_forged.txt",
    ],
}

AGENT_QUESTIONS = [
    ("web-01 is SSH-reachable with creds recovered from loot. Pivot to the internal 10.0.0.0/16 network?",
     ["Yes, pivot", "Stay external", "Ask me later"]),
    ("The SQLi on /api/v2/search can dump the full users table (1284 rows). Proceed with the dump?",
     ["Dump users", "Prove it with 1 row", "Skip"]),
    ("Found an admin panel at /admin behind basic auth. Try the recovered credentials there?",
     ["Yes", "No"]),
]


class Simulator:
    def __init__(self, bus: Bus, tick_sec: float = 2.5) -> None:
        self.bus = bus
        self.tick_sec = tick_sec

    async def run_one(self, run_id: str) -> None:
        async with session_scope() as s:
            run = await runs_repo.get(s, run_id)
            if run is None:
                return
            session_id = run.session_id
        tick = 0
        shell_cursor: dict[str, int] = {}
        await asyncio.sleep(0.5)
        while True:
            async with session_scope() as s:
                run = await runs_repo.get(s, run_id)
                status = run.status if run else "stopped"
            if status in ("stopped", "completed") or run is None:
                return
            if status == "paused":
                await asyncio.sleep(self.tick_sec)
                continue

            tick += 1
            try:
                await self._emit_event(run_id)
                async with session_scope() as s:
                    await runs_repo.set_meters(s, run_id, random.randint(3_000, 22_000),
                                               random.uniform(0.004, 0.03), int(self.tick_sec))
                if tick % 9 == 0:
                    await self._ask_question(run_id)
                await self._emit_shells(session_id, shell_cursor)
            except Exception:
                pass
            await asyncio.sleep(self.tick_sec)

    async def _emit_event(self, run_id: str) -> None:
        source, typ, text = random.choice(EVENT_TEMPLATES)
        from .. import events as events_bus
        await events_bus.emit(self.bus, run_id, source, typ, text)

    async def _ask_question(self, run_id: str) -> None:
        text, options = random.choice(AGENT_QUESTIONS)
        async with session_scope() as s:
            msg = await chat_repo.create(s, run_id, "assistant", text, options)
            payload = {"id": msg.id, "runId": run_id, "role": "assistant",
                       "text": text, "options": options, "ts": msg.ts}
        await self.bus.publish_json(chat_channel(run_id), payload)

    async def _emit_shells(self, session_id: str, cursor: dict[str, int]) -> None:
        async with session_scope() as s:
            running = [sh for sh in await shells_repo.list_for_session(s, session_id)
                       if sh.status == "running"]
        for sh in running:
            lines = SHELL_LINES.get(sh.kind) or SHELL_LINES["tool"]
            i = cursor.get(sh.id, 0)
            cursor[sh.id] = i + 1
            await self.bus.publish(shell_channel(sh.id), lines[i % len(lines)] + "\r\n")
