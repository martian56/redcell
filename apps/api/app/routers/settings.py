"""Global settings and provider catalog."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from redcell_core.repositories import provider_credentials as creds_repo
from redcell_core.repositories import providers as providers_repo
from redcell_core.repositories import settings as settings_repo
from redcell_core.schemas import (
    AvailableModel,
    ProviderCatalogEntry,
    ProviderKeyInput,
    ProviderKeyStatus,
    Settings,
)
from redcell_core.security import current_user

from ..deps import db

router = APIRouter(tags=["settings"], dependencies=[Depends(current_user)])


@router.get("/settings", response_model=Settings)
async def get_settings(s: AsyncSession = Depends(db)) -> Settings:
    row = await settings_repo.get(s)
    return Settings(llm=row.llm, execution=row.execution, scope=row.scope, proxy=row.proxy,
                    report=row.report or {})


@router.post("/settings", response_model=Settings)
async def save_settings(body: Settings, s: AsyncSession = Depends(db)) -> Settings:
    row = await settings_repo.save(s, body.model_dump())
    return Settings(llm=row.llm, execution=row.execution, scope=row.scope, proxy=row.proxy,
                    report=row.report or {})


@router.get("/providers", response_model=list[ProviderCatalogEntry])
async def providers(s: AsyncSession = Depends(db)) -> list[ProviderCatalogEntry]:
    return [ProviderCatalogEntry(id=p.id, label=p.label, models=p.models, needs_key=p.needs_key)
            for p in await providers_repo.list_all(s)]


# ---- per-provider API keys (Fernet-encrypted at rest) ----
@router.get("/provider-keys", response_model=list[ProviderKeyStatus])
async def list_provider_keys(s: AsyncSession = Depends(db)) -> list[ProviderKeyStatus]:
    return [ProviderKeyStatus(provider_id=x["provider_id"], has_key=x["has_key"], api_base=x["api_base"])
            for x in await creds_repo.list_status(s)]


@router.post("/provider-keys", response_model=ProviderKeyStatus)
async def set_provider_key(body: ProviderKeyInput, s: AsyncSession = Depends(db)) -> ProviderKeyStatus:
    row = await creds_repo.set_key(s, body.provider_id, body.api_key, body.api_base)
    return ProviderKeyStatus(provider_id=row.provider_id, has_key=bool(row.api_key_enc), api_base=row.api_base)


@router.delete("/provider-keys/{provider_id}", status_code=204)
async def remove_provider_key(provider_id: str, s: AsyncSession = Depends(db)) -> None:
    await creds_repo.delete(s, provider_id)


# ---- models available to the operator (keyed + keyless providers) ----
@router.get("/models/available", response_model=list[AvailableModel])
async def available_models(s: AsyncSession = Depends(db)) -> list[AvailableModel]:
    keyed = set(await creds_repo.keyed_ids(s))
    # legacy single key stored on the default provider in app_settings
    cfg = await settings_repo.get(s)
    base = cfg.llm or {}
    if base.get("api_key") and base.get("provider"):
        keyed.add(base["provider"])
    out: list[AvailableModel] = []
    for p in await providers_repo.list_all(s):
        if p.needs_key and p.id not in keyed:
            continue
        for m in p.models:
            out.append(AvailableModel(provider=p.id, provider_label=p.label, model=m))
    return out
