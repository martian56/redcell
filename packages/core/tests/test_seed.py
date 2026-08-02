import pytest

from redcell_core import seed
from redcell_core.config import settings
from redcell_core.db import session_scope
from redcell_core.repositories import providers as providers_repo
from redcell_core.repositories import sessions as sessions_repo
from redcell_core.repositories import users as users_repo


@pytest.mark.asyncio
async def test_bootstrap_then_demo_then_unseed():
    # This test wipes the database. Refuse to run unless the suite's isolated
    # test database is in effect, so it can never destroy real dev data.
    assert settings.database_url.rsplit("/", 1)[-1].endswith("_test"), \
        "destructive seed test requires the isolated *_test database"
    await seed.unseed(force=True)
    await seed.bootstrap()
    async with session_scope() as s:
        assert len(await providers_repo.list_all(s)) >= 5
        assert await users_repo.get_by_username(s, "admin") is not None
    await seed.demo()
    async with session_scope() as s:
        assert len(await sessions_repo.list_all(s)) >= 3
    await seed.unseed(force=True)
    async with session_scope() as s:
        assert await sessions_repo.list_all(s) == []
