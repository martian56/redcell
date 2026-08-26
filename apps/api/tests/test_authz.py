"""Protected endpoints reject unauthenticated requests."""

import asyncio

from fastapi.testclient import TestClient
from redcell_core import seed
from redcell_core.db import engine


async def _boot():
    await seed.bootstrap()
    await engine.dispose()


from app.main import app  # noqa: E402


def test_protected_endpoints_require_auth():
    asyncio.run(_boot())
    with TestClient(app) as c:
        assert c.get("/api/v1/auth/me").status_code == 401
        assert c.get("/api/v1/sessions").status_code == 401
        assert c.post("/api/v1/sessions", json={"name": "x", "client": "y"}).status_code == 401
        assert c.get("/api/v1/settings").status_code == 401
        assert c.get("/api/v1/servers").status_code == 401
        assert c.get("/api/v1/runs/run-x/chat").status_code == 401
