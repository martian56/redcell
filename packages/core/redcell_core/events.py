"""Emit a run event: persist it (durable activity log) and publish it live on the bus."""

from __future__ import annotations

from .bus import events_channel
from .db import session_scope
from .repositories import events as events_repo


async def emit(bus, run_id: str, source: str, type: str, text: str) -> dict:
    async with session_scope() as s:
        row = await events_repo.record(s, run_id, source, type, text)
        payload = {"id": row.id, "ts": row.ts, "runId": run_id,
                   "source": source, "type": type, "text": text}
    await bus.publish_json(events_channel(run_id), payload)
    return payload
