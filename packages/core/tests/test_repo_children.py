import pytest

from redcell_core.db import session_scope
from redcell_core.repositories import proxy_entries, servers


@pytest.mark.asyncio
async def test_proxy_history_capped():
    async with session_scope() as s:
        for i in range(5):
            await proxy_entries.add_capped(
                s, "ses-cap", {"method": "GET", "url": f"/{i}", "status": 200, "length": "1"}, cap=3)
        rows = await proxy_entries.list_for_session(s, "ses-cap")
        assert len(rows) == 3


@pytest.mark.asyncio
async def test_server_secret_encrypted():
    async with session_scope() as s:
        row = await servers.create(s, {"name": "x", "host": "h", "username": "root"}, secret_plain="pw")
        assert row.secret_ref and row.secret_ref != "pw"
        assert await servers.get_secret(s, row.id) == "pw"
