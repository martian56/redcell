import pytest
from redcell_core.db import session_scope
from sqlalchemy import text


@pytest.mark.asyncio
async def test_can_connect():
    async with session_scope() as s:
        result = await s.execute(text("select 1"))
        assert result.scalar() == 1
