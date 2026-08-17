"""Session brief, run instruction, and assessment files persist and read back."""

import asyncio

from fastapi.testclient import TestClient
from redcell_core import seed
from redcell_core.db import engine


async def _boot():
    await seed.bootstrap()
    await engine.dispose()


from app.main import app  # noqa: E402


def test_brief_instruction_and_assessment_file_roundtrip():
    asyncio.run(_boot())
    with TestClient(app) as c:
        assert c.post("/api/v1/auth/login",
                      json={"username": "admin", "password": "admin"}).status_code == 200

        r = c.post("/api/v1/sessions", json={
            "name": "Ctx", "client": "QA", "scope": ["*.t"], "targets": ["https://t"],
            "roe": "no dos", "brief": "CTF: prompt injection, find the flag, skip recon",
        })
        assert r.status_code == 200
        sid = r.json()["id"]
        assert r.json()["brief"] == "CTF: prompt injection, find the flag, skip recon"
        assert c.get(f"/api/v1/sessions/{sid}").json()["brief"].startswith("CTF:")

        r = c.post(f"/api/v1/sessions/{sid}/runs",
                   json={"name": "assess", "model": "kimi-k3", "instruction": "this run: try IDOR"})
        assert r.status_code == 200
        rid = r.json()["id"]
        assert r.json()["instruction"] == "this run: try IDOR"
        assert c.get(f"/api/v1/runs/{rid}").json()["instruction"] == "this run: try IDOR"

        r = c.post(f"/api/v1/sessions/{sid}/files",
                   files={"file": ("challenge.bin", b"\x7fELFbinary", "application/octet-stream")},
                   data={"kind": "assessment"})
        assert r.status_code == 200 and r.json()["kind"] == "assessment"
        files = c.get(f"/api/v1/sessions/{sid}/files").json()
        assert any(f["filename"] == "challenge.bin" and f["kind"] == "assessment" for f in files)

        bad = c.post(f"/api/v1/sessions/{sid}/files",
                     files={"file": ("../../evil.sh", b"x", "text/plain")},
                     data={"kind": "assessment"})
        assert bad.status_code == 400
