"""FastAPI application factory."""

from __future__ import annotations

import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redcell_core.bus import bus
from redcell_core.config import settings
from redcell_core.db import session_scope
from redcell_core.logs import configure as configure_logging
from redcell_core.storage import storage
from sqlalchemy import text

from .routers import ai, auth, files, infra, notifications, reports, resources, system, ws
from .routers import settings as settings_router


async def _health_report() -> dict[str, object]:
    checks: dict[str, str] = {}
    try:
        async with session_scope() as s:
            await s.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "down"
    try:
        checks["redis"] = "ok" if await bus.ping() else "down"
    except Exception:
        checks["redis"] = "down"
    try:
        checks["storage"] = "ok" if await storage.ping() else "down"
    except Exception:
        checks["storage"] = "down"
    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await bus.connect()
    try:
        yield
    finally:
        await bus.close()


def create_app() -> FastAPI:
    app = FastAPI(title="REDCELL API", version="0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    for r in (auth.router, resources.router, settings_router.router, infra.router,
              files.router, reports.router, ai.router, system.router,
              notifications.router, ws.router):
        app.include_router(r, prefix=prefix)

    @app.get("/health")
    async def health() -> dict[str, object]:
        return await _health_report()

    @app.get(prefix + "/health")
    async def api_health() -> dict[str, object]:
        return await _health_report()

    return app


app = create_app()
