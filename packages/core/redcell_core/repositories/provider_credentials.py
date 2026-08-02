from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt, encrypt
from ..models import ProviderCredential
from . import ids


async def set_key(s: AsyncSession, provider_id: str, api_key: str, api_base: str | None = None) -> ProviderCredential:
    row = await s.get(ProviderCredential, provider_id)
    if row is None:
        row = ProviderCredential(provider_id=provider_id, created_at=ids.now_iso())
        s.add(row)
    if api_key:  # empty key means "leave existing key untouched"
        row.api_key_enc = encrypt(api_key)
    row.api_base = api_base or None
    await s.flush()
    return row


async def delete(s: AsyncSession, provider_id: str) -> bool:
    row = await s.get(ProviderCredential, provider_id)
    if not row:
        return False
    await s.delete(row)
    await s.flush()
    return True


async def get_secret(s: AsyncSession, provider_id: str) -> tuple[str, str | None]:
    """Return (api_key, api_base) decrypted, or ('', None) if none stored."""
    row = await s.get(ProviderCredential, provider_id)
    if not row:
        return "", None
    return decrypt(row.api_key_enc), row.api_base


async def keyed_ids(s: AsyncSession) -> set[str]:
    rows = await s.scalars(select(ProviderCredential.provider_id).where(ProviderCredential.api_key_enc != ""))
    return set(rows.all())


async def list_status(s: AsyncSession) -> list[dict]:
    rows = list((await s.scalars(select(ProviderCredential))).all())
    return [{"provider_id": r.provider_id, "has_key": bool(r.api_key_enc), "api_base": r.api_base} for r in rows]
