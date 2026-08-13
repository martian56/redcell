"""End-to-end API smoke test against Postgres + Redis + MinIO. Boots the app in
a TestClient (lifespan connects the bus), then hits the REST endpoints, file
upload/download, reports, and a WebSocket chat round-trip."""

import asyncio
import time

from fastapi.testclient import TestClient

# Ensure admin + providers exist, then release the bootstrap loop's connections.
from redcell_core import seed  # noqa: E402
from redcell_core.db import engine  # noqa: E402


async def _boot():
    await seed.bootstrap()
    await engine.dispose()


from app.main import app  # noqa: E402

failures = []


def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        failures.append(name)


def test_api_smoke():
    # other tests may have unseeded the DB; boot here, and free the bootstrap
    # loop's connections before TestClient opens its own.
    asyncio.run(_boot())
    with TestClient(app) as c:
        r = c.get("/health")
        check("health", r.status_code == 200 and r.json()["status"] == "ok")

        check("me-401-before-login", c.get("/api/v1/auth/me").status_code == 401)
        check("first-run", c.get("/api/v1/auth/first-run").status_code == 200)
        check("login-bad", c.post("/api/v1/auth/login", json={"username": "admin", "password": "nope"}).status_code == 401)
        r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
        check("login", r.status_code == 200 and r.json()["username"] == "admin")
        check("me-after-login", c.get("/api/v1/auth/me").status_code == 200)

        # session + run (independent of demo data)
        r = c.post("/api/v1/sessions", json={"name": "Smoke", "client": "QA", "scope": ["*.t"], "targets": ["https://t"]})
        check("create-session", r.status_code == 200 and "createdAt" in r.json() and "severityCounts" in r.json())
        sid = r.json()["id"]
        check("sessions-list", any(x["id"] == sid for x in c.get("/api/v1/sessions").json()))
        check("session-get", c.get(f"/api/v1/sessions/{sid}").status_code == 200)
        check("session-404", c.get("/api/v1/sessions/nope").status_code == 404)

        r = c.post(f"/api/v1/sessions/{sid}/runs", json={"name": "assess", "model": "kimi-k3"})
        check("create-run", r.status_code == 200 and r.json()["status"] == "queued")
        rid = r.json()["id"]
        check("runs-list", len(c.get(f"/api/v1/sessions/{sid}/runs").json()) >= 1)
        check("run-get", c.get(f"/api/v1/runs/{rid}").status_code == 200)

        g = c.get(f"/api/v1/runs/{rid}/agents").json()
        check("agent-graph-orchestrator", any(n["name"] == "orchestrator" for n in g["nodes"]))

        check("findings-empty", c.get(f"/api/v1/sessions/{sid}/findings").json() == [])

        r = c.post(f"/api/v1/sessions/{sid}/shells", json={"kind": "tool", "label": "nmap"})
        check("shell-open", r.status_code == 200)
        shid = r.json()["id"]
        check("shell-write", c.post(f"/api/v1/shells/{shid}/write", json={"data": "id\n"}).status_code == 200)
        check("shell-list", len(c.get(f"/api/v1/sessions/{sid}/shells").json()) >= 1)
        check("shell-close", c.delete(f"/api/v1/shells/{shid}").status_code == 204)

        r = c.post(f"/api/v1/sessions/{sid}/listeners", json={"kind": "tcp", "bind": "0.0.0.0:9001"})
        check("listener-start", r.status_code == 200 and r.json()["status"] == "listening")

        check("proxy-history", c.get(f"/api/v1/sessions/{sid}/proxy").status_code == 200)
        check("hosts", c.get(f"/api/v1/sessions/{sid}/hosts").status_code == 200)
        check("loot", c.get(f"/api/v1/sessions/{sid}/loot").status_code == 200)

        check("chat-history", c.get(f"/api/v1/runs/{rid}/chat").json() == [])
        r = c.post(f"/api/v1/runs/{rid}/chat", json={"text": "focus on auth"})
        check("chat-send", r.status_code == 200 and r.json()["role"] == "operator")

        st = c.get("/api/v1/settings").json()
        check("settings-get", "llm" in st and "execution" in st)
        check("settings-save", c.post("/api/v1/settings", json=st).status_code == 200)
        check("providers", len(c.get("/api/v1/providers").json()) >= 5)

        r = c.post("/api/v1/servers", json={"name": "t1", "host": "1.2.3.4", "username": "root", "authMethod": "password", "password": "x"})
        check("server-create", r.status_code == 200)
        check("server-delete", c.delete(f"/api/v1/servers/{r.json()['id']}").status_code == 204)
        r = c.post("/api/v1/proxies", json={"label": "p1", "url": "http://p:8080", "kind": "http", "auth": "open"})
        check("proxy-create", r.status_code == 200)
        check("proxy-delete", c.delete(f"/api/v1/proxies/{r.json()['id']}").status_code == 204)

        # files: proxied upload -> download redirect -> delete
        r = c.post(f"/api/v1/sessions/{sid}/files", files={"file": ("t.txt", b"hello", "text/plain")})
        check("file-upload", r.status_code == 200 and r.json()["filename"] == "t.txt")
        fid = r.json()["id"]
        check("file-list", any(f["id"] == fid for f in c.get(f"/api/v1/sessions/{sid}/files").json()))
        dl = c.get(f"/api/v1/files/{fid}", follow_redirects=False)
        check("file-download-redirect", dl.status_code in (302, 307) and "location" in {k.lower() for k in dl.headers})
        check("file-delete", c.delete(f"/api/v1/files/{fid}").status_code == 204)

        # reports: create enqueues async generation (worker not running in test -> stays generating)
        r = c.post(f"/api/v1/sessions/{sid}/reports", json={"title": "Q3 report", "formats": ["json"]})
        check("report-create", r.status_code == 200 and r.json()["status"] == "generating")
        repid = r.json()["id"]
        check("report-get", c.get(f"/api/v1/reports/{repid}").status_code == 200)
        check("report-list", len(c.get(f"/api/v1/sessions/{sid}/reports").json()) >= 1)
        check("report-delete", c.delete(f"/api/v1/reports/{repid}").status_code == 204)

        # run lifecycle
        check("run-pause", c.post(f"/api/v1/runs/{rid}/pause").status_code == 200)
        check("run-resume", c.post(f"/api/v1/runs/{rid}/resume").status_code == 200)
        check("run-stop", c.post(f"/api/v1/runs/{rid}/stop").status_code == 200)

        # browser control handoff (publishes the owner to the browser channel)
        rbc = c.post(f"/api/v1/sessions/{sid}/browser/control", json={"owner": "operator"})
        check("browser-control", rbc.status_code == 200 and rbc.json()["owner"] == "operator")

        # WebSocket chat round-trip (REST publish -> WS receive)
        with c.websocket_connect(f"/api/v1/ws/chat/{rid}") as ws:
            time.sleep(0.3)
            c.post(f"/api/v1/runs/{rid}/chat", json={"text": "ping over ws"})
            msg = ws.receive_json()
            check("ws-chat-roundtrip", msg.get("role") == "operator" and msg.get("text") == "ping over ws")

        # WS auth guard: no cookie -> connection refused
        fresh = TestClient(app)
        with fresh:
            try:
                with fresh.websocket_connect(f"/api/v1/ws/events/{rid}"):
                    check("ws-auth-guard", False)
            except Exception:
                check("ws-auth-guard", True)
            try:
                with fresh.websocket_connect(f"/api/v1/ws/browser/{sid}"):
                    check("ws-browser-auth-guard", False)
            except Exception:
                check("ws-browser-auth-guard", True)

    assert not failures, f"failed checks: {failures}"
