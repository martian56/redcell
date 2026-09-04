"""Runtime version and in-app self-update."""

from __future__ import annotations

import asyncio
import os
import time

from fastapi import APIRouter, Depends, HTTPException
from redcell_core.schemas import Camel
from redcell_core.security import User, current_user

router = APIRouter(tags=["system"], dependencies=[Depends(current_user)])

_GITHUB_LATEST = "https://api.github.com/repos/martian56/redcell/releases/latest"
_cache: dict[str, object] = {"at": 0.0, "latest": None}
_CACHE_TTL = 600.0


class VersionInfo(Camel):
    current: str
    latest: str | None = None
    update_available: bool = False


class UpdateStarted(Camel):
    started: bool
    detail: str


def current_version() -> str:
    return os.environ.get("REDCELL_VERSION") or "dev"


def _norm(v: str | None) -> tuple[int, ...]:
    if not v:
        return ()
    parts: list[int] = []
    for p in v.strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def update_available(current: str, latest: str | None) -> bool:
    if not latest or current == "dev":
        return False
    return _norm(latest) > _norm(current)


async def _latest_version() -> str | None:
    now = time.time()
    if _cache["latest"] is not None and now - float(_cache["at"]) < _CACHE_TTL:
        return _cache["latest"]  # type: ignore[return-value]
    tag: str | None = None
    try:
        import httpx

        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(_GITHUB_LATEST, headers={"accept": "application/vnd.github+json"})
            r.raise_for_status()
            tag = r.json().get("tag_name")
    except Exception:
        tag = None
    if tag:
        _cache["latest"] = tag
        _cache["at"] = now
    return _cache["latest"]  # type: ignore[return-value]


@router.get("/system/version", response_model=VersionInfo)
async def version() -> VersionInfo:
    current = current_version()
    latest = await _latest_version()
    return VersionInfo(current=current, latest=latest, update_available=update_available(current, latest))


@router.post("/system/update", response_model=UpdateStarted)
async def start_update(user: User = Depends(current_user)) -> UpdateStarted:
    if user.role != "admin":
        raise HTTPException(403, "admin only")
    repo_dir = os.environ.get("REDCELL_COMPOSE_DIR")
    if not repo_dir:
        raise HTTPException(400, "in-app update is not available on this deployment (REDCELL_COMPOSE_DIR is not set)")
    image = os.environ.get("REDCELL_UPDATER_IMAGE") or "docker:cli"
    cmd = [
        "docker", "run", "-d", "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", f"{repo_dir}:/repo",
        "-w", "/repo",
        image,
        "sh", "-c", "docker compose pull && docker compose up -d",
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError((out or b"").decode(errors="replace")[-300:])
    except Exception as exc:
        raise HTTPException(500, f"could not start the updater: {exc}") from None
    return UpdateStarted(started=True, detail="Update started. The stack will pull new images and restart shortly.")
