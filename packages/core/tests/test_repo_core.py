import pytest

from redcell_core.db import session_scope
from redcell_core.repositories import sessions as sessions_repo


@pytest.mark.asyncio
async def test_create_and_count():
    async with session_scope() as s:
        row = await sessions_repo.create(s, {"name": "T", "client": "C", "scope": [], "targets": []})
        assert row.id.startswith("ses-")
        counts = await sessions_repo.severity_counts(s, row.id)
        assert counts["critical"] == 0
        assert await sessions_repo.findings_count(s, row.id) == 0
