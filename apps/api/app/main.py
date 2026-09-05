"""FastAPI application factory."""

from __future__ import annotations

import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redcell_core.bus import bus
from redcell_core.config import settings
from redcell_core.logs import configure as configure_logging

from .routers import ai, auth, files, infra, notifications, reports, resources, system, ws
from .routers import settings as settings_router


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await bus.connect()
    try:
        yield
    finally:
        await bus.close()


def create_app() -> FastAPI:
    app = FastAPI(title="REDCELL API", version="0.2.0", lifespan=lifespan)

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
    async def health() -> dict[str, str]:
        return {"status": "ok", "mode": settings.run_mode, "bus": bus.transport}

    @app.get(prefix + "/health")
    async def api_health() -> dict[str, str]:
        return {"status": "ok", "mode": settings.run_mode, "bus": bus.transport}

    return app


app = create_app()
