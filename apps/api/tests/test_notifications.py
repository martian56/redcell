import asyncio

from app.main import app  # noqa: E402
from fastapi.testclient import TestClient
from redcell_core import seed
from redcell_core.db import engine, session_scope
from redcell_core.repositories import notifications as nrepo
from redcell_core.repositories import settings as settings_repo


async def _boot():
    await seed.bootstrap()
    await engine.dispose()


async def _boot_seeded():
    await seed.bootstrap()
    async with session_scope() as s:
        await nrepo.create(s, kind="run_completed", title="Test run", body="done", link="sessions/x")
    await engine.dispose()


async def _finding_gated_off():
    async with session_scope() as s:
        cfg = await settings_repo.get(s)
        cfg.notifications = {"critical_findings": False}
        await s.flush()
    async with session_scope() as s:
        result = await nrepo.notify(s, kind="finding", title="SQLi")
    await engine.dispose()
    return result


def _login(c: TestClient):
    r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200


def test_notifications_require_auth():
    asyncio.run(_boot())
    with TestClient(app) as c:
        assert c.get("/api/v1/notifications").status_code == 401


def test_settings_carry_notification_prefs():
    asyncio.run(_boot())
    with TestClient(app) as c:
        _login(c)
        st = c.get("/api/v1/settings").json()
        assert "notifications" in st
        assert "criticalFindings" in st["notifications"]
        assert c.post("/api/v1/settings", json=st).status_code == 200


def test_feed_mark_read_and_mark_all():
    asyncio.run(_boot_seeded())
    with TestClient(app) as c:
        _login(c)
        feed = c.get("/api/v1/notifications").json()
        assert feed["unread"] >= 1
        mine = [n for n in feed["items"] if n["title"] == "Test run"]
        assert mine and mine[0]["read"] is False
        nid = mine[0]["id"]
        after = c.post(f"/api/v1/notifications/{nid}/read").json()
        marked = [n for n in after["items"] if n["id"] == nid]
        assert marked and marked[0]["read"] is True
        assert c.post("/api/v1/notifications/read-all").json()["unread"] == 0


def test_notify_respects_disabled_category():
    asyncio.run(_boot())
    assert asyncio.run(_finding_gated_off()) is None
