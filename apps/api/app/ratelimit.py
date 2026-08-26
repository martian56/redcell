"""A small in-process sliding-window rate limiter, applied as a route dependency.
Single-process/single-user by design; disabled when settings.rate_limit_enabled
is false (tests)."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from redcell_core.config import settings

_HITS: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def _reset() -> None:
    _HITS.clear()


def rate_limit(name: str, max_calls: int, window_seconds: float):
    async def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        ip = request.client.host if request.client else "unknown"
        key = (name, ip)
        now = time.monotonic()
        hits = _HITS[key]
        while hits and now - hits[0] > window_seconds:
            hits.popleft()
        if len(hits) >= max_calls:
            raise HTTPException(status_code=429, detail="too many requests, slow down")
        hits.append(now)

    return dependency
