"""Global settings and provider catalog."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from redcell_core.repositories import provider_credentials as creds_repo
from redcell_core.repositories import providers as providers_repo
from redcell_core.repositories import secrets as secrets_repo
from redcell_core.repositories import settings as settings_repo
from redcell_core.schemas import (
    AvailableModel,
    DismissActionInput,
    NgrokStatus,
    NgrokTokenInput,
    ProviderCatalogEntry,
    ProviderKeyInput,
    ProviderKeyStatus,
    Settings,
    SetupStatus,
)
from redcell_core.security import current_user
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import db

router = APIRouter(tags=["settings"], dependencies=[Depends(current_user)])


@router.get("/settings", response_model=Settings)
async def get_settings(s: AsyncSession = Depends(db)) -> Settings:
    row = await settings_repo.get(s)
    return Settings(llm=row.llm, execution=row.execution, scope=row.scope, proxy=row.proxy,
                    report=row.report or {}, notifications=row.notifications or {})


@router.post("/settings", response_model=Settings)
async def save_settings(body: Settings, s: AsyncSession = Depends(db)) -> Settings:
    row = await settings_repo.save(s, body.model_dump())
    return Settings(llm=row.llm, execution=row.execution, scope=row.scope, proxy=row.proxy,
                    report=row.report or {}, notifications=row.notifications or {})


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


# ---- ngrok auth token (Fernet-encrypted at rest) ----
@router.get("/integrations/ngrok", response_model=NgrokStatus)
async def ngrok_status(s: AsyncSession = Depends(db)) -> NgrokStatus:
    return NgrokStatus(configured=await secrets_repo.has_secret(s, secrets_repo.NGROK_AUTHTOKEN))


@router.post("/integrations/ngrok", response_model=NgrokStatus)
async def set_ngrok_token(body: NgrokTokenInput, s: AsyncSession = Depends(db)) -> NgrokStatus:
    token = body.token.strip()
    if len(token) < 20 or " " in token:
        raise HTTPException(status_code=422, detail="that does not look like an ngrok auth token")
    await secrets_repo.set_secret(s, secrets_repo.NGROK_AUTHTOKEN, token)
    return NgrokStatus(configured=True)


@router.delete("/integrations/ngrok", status_code=204)
async def clear_ngrok_token(s: AsyncSession = Depends(db)) -> None:
    await secrets_repo.delete_secret(s, secrets_repo.NGROK_AUTHTOKEN)


# ---- onboarding / recommended actions ----
@router.get("/setup-status", response_model=SetupStatus)
async def setup_status(s: AsyncSession = Depends(db)) -> SetupStatus:
    keyed = await creds_repo.keyed_ids(s)
    cfg = await settings_repo.get(s)
    has_ai = bool(keyed) or bool((cfg.llm or {}).get("api_key"))
    has_ngrok = await secrets_repo.has_secret(s, secrets_repo.NGROK_AUTHTOKEN)
    dismissed = await settings_repo.dismissed_actions(s)
    return SetupStatus(has_ai_key=has_ai, has_ngrok=has_ngrok, dismissed=dismissed)


@router.post("/setup-status/dismiss", response_model=SetupStatus)
async def dismiss_setup_action(body: DismissActionInput, s: AsyncSession = Depends(db)) -> SetupStatus:
    await settings_repo.dismiss_action(s, body.action)
    return await setup_status(s)


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
