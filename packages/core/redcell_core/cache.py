"""Best-effort Redis cache for rarely-changing reads (provider catalog, settings).
If Redis is down, get returns None and set is a no-op."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from .config import settings

_r = redis.from_url(settings.redis_url, decode_responses=True)


async def get_json(key: str) -> Any | None:
    try:
        raw = await _r.get(key)
    except Exception:
        return None
    return json.loads(raw) if raw else None


async def set_json(key: str, value: Any, ttl: int = 300) -> None:
    try:
        await _r.set(key, json.dumps(value), ex=ttl)
    except Exception:
        pass
