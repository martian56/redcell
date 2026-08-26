"""Login is throttled when rate limiting is enabled."""

import asyncio

from app.ratelimit import _reset
from fastapi.testclient import TestClient
from redcell_core import seed
from redcell_core.config import settings
from redcell_core.db import engine


async def _boot():
    await seed.bootstrap()
    await engine.dispose()


from app.main import app  # noqa: E402


def test_login_is_rate_limited():
    asyncio.run(_boot())
    settings.rate_limit_enabled = True
    _reset()
    try:
        with TestClient(app) as c:
            codes = [
                c.post("/api/v1/auth/login", json={"username": "admin", "password": "nope"}).status_code
                for _ in range(12)
            ]
        assert 429 in codes
        assert 429 not in codes[:10]
    finally:
        settings.rate_limit_enabled = False
        _reset()
