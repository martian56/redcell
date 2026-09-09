from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt, encrypt
from ..models import Secret
from . import ids

NGROK_AUTHTOKEN = "ngrok_authtoken"


async def set_secret(s: AsyncSession, name: str, value: str) -> None:
    stmt = pg_insert(Secret).values(name=name, value_enc=encrypt(value), created_at=ids.now_iso())
    stmt = stmt.on_conflict_do_update(index_elements=[Secret.name],
                                      set_={"value_enc": stmt.excluded.value_enc})
    await s.execute(stmt)
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
