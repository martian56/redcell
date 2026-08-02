import asyncio
import json

import pytest

from redcell_core.bus import bus, events_channel
from redcell_core.config import settings
from redcell_core.db import session_scope
from redcell_core.repositories import runs as runs_repo
from redcell_core.repositories import sessions as sessions_repo
from worker.tasks import run_engagement


@pytest.mark.asyncio
async def test_run_engagement_sim_publishes(monkeypatch):
    # This test exercises the simulator path; pin the mode so a live root .env
    # (REDCELL_RUN_MODE=live) doesn't route it into the LLM-backed runner.
    monkeypatch.setattr(settings, "run_mode", "sim")
    await bus.connect()
    async with session_scope() as s:
        ses = await sessions_repo.create(s, {"name": "W", "client": "C", "scope": [], "targets": []})
        run = await runs_repo.create(s, {"session_id": ses.id, "name": "r", "status": "queued",
                                         "phase": "Recon", "model": "kimi-k3"})
        rid = ses_id_run = run.id

    got = []

    async def collect():
        async for m in bus.subscribe(events_channel(rid)):
            got.append(json.loads(m))
            return

    collector = asyncio.create_task(collect())
    await asyncio.sleep(0.1)
    task = asyncio.create_task(run_engagement({}, rid))
    await asyncio.wait_for(collector, timeout=10)
    async with session_scope() as s:
        await runs_repo.set_status(s, rid, "stopped")
    await asyncio.wait_for(task, timeout=10)
    assert got and got[0]["runId"] == rid
