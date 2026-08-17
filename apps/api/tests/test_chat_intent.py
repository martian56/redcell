"""Regression: a question sent while a run is live must not get the canned
"Got it. Steering the run now." steer acknowledgement."""

import asyncio

from fastapi.testclient import TestClient
from redcell_core import seed
from redcell_core.db import engine

CANNED = "Got it. Steering the run now."


async def _boot():
    await seed.bootstrap()
    await engine.dispose()


from app.main import app  # noqa: E402


def test_live_run_chat_question_is_not_canned_steer():
    asyncio.run(_boot())
    with TestClient(app) as c:
        assert c.post("/api/v1/auth/login",
                      json={"username": "admin", "password": "admin"}).status_code == 200

        sid = c.post("/api/v1/sessions", json={"name": "ChatIntent", "client": "QA",
                                               "scope": ["*.t"], "targets": ["https://t"]}).json()["id"]
        rid = c.post(f"/api/v1/sessions/{sid}/runs",
                     json={"name": "assess", "model": "kimi-k3"}).json()["id"]

        assert c.post(f"/api/v1/runs/{rid}/resume").json()["status"] == "running"

        r = c.post(f"/api/v1/runs/{rid}/chat", json={"text": "what is the orchestrator doing?"})
        assert r.status_code == 200 and r.json()["role"] == "operator"

        texts = [m["text"] for m in c.get(f"/api/v1/runs/{rid}/chat").json()]
        assert CANNED not in texts, f"chat returned the canned steer ack for a question: {texts}"
