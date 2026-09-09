from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt, encrypt
from ..models import Secret
from . import ids

NGROK_AUTHTOKEN = "ngrok_authtoken"


async def set_secret(s: AsyncSession, name: str, value: str) -> None:
    row = await s.get(Secret, name)
    if row is None:
        row = Secret(name=name, created_at=ids.now_iso())
        s.add(row)
    row.value_enc = encrypt(value)
    await s.flush()


async def get_secret(s: AsyncSession, name: str) -> str:
    row = await s.get(Secret, name)
    if row is None:
        return ""
    return decrypt(row.value_enc)


async def has_secret(s: AsyncSession, name: str) -> bool:
    row = await s.get(Secret, name)
    return bool(row and row.value_enc)


async def delete_secret(s: AsyncSession, name: str) -> bool:
    row = await s.get(Secret, name)
    if not row:
        return False
    await s.delete(row)
    await s.flush()
    return True
