"""Cross-process coordination between the API and the worker (requires shared Redis).

- steer queue: operator directives the orchestrator drains at each plan step.
- awaiting flag: set while blocked on an ask_operator question, so the next
  operator message is routed as the answer, not a new directive."""

from __future__ import annotations

import redis.asyncio as redis

from .config import settings

_r = redis.from_url(settings.redis_url, decode_responses=True)


def _steer_key(run_id: str) -> str:
    return f"steer:{run_id}"


def _awaiting_key(run_id: str) -> str:
    return f"awaiting:{run_id}"


async def push_steer(run_id: str, text: str) -> None:
    try:
        await _r.rpush(_steer_key(run_id), text)
    except Exception:
        pass


async def drain_steer(run_id: str) -> list[str]:
    out: list[str] = []
    try:
        while True:
            v = await _r.lpop(_steer_key(run_id))
            if v is None:
                break
            out.append(v)
    except Exception:
        pass
    return out


async def set_awaiting(run_id: str, on: bool) -> None:
    try:
        if on:
            await _r.set(_awaiting_key(run_id), "1", ex=900)
        else:
            await _r.delete(_awaiting_key(run_id))
    except Exception:
        pass


async def is_awaiting(run_id: str) -> bool:
    try:
        return bool(await _r.get(_awaiting_key(run_id)))
    except Exception:
        return False
