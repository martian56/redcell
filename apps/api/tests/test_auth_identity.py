"""current_user resolves the real seeded user, not a hardcoded id."""

import asyncio

from fastapi.testclient import TestClient
from redcell_core import seed
from redcell_core.db import engine, session_scope
from redcell_core.repositories import users as users_repo

_admin_id = None


async def _boot():
    global _admin_id
    await seed.bootstrap()
    async with session_scope() as s:
        u = await users_repo.get_by_username(s, "admin")
        _admin_id = u.id
    await engine.dispose()


from app.main import app  # noqa: E402


def test_me_returns_the_real_seeded_user():
    asyncio.run(_boot())
    with TestClient(app) as c:
        assert c.post("/api/v1/auth/login",
                      json={"username": "admin", "password": "admin"}).status_code == 200
        me = c.get("/api/v1/auth/me").json()
        assert me["username"] == "admin"
        assert me["id"] != "u-1"
        assert me["id"] == _admin_id
