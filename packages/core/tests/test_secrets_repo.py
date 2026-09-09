import pytest
from redcell_core.db import session_scope
from redcell_core.repositories import secrets as secrets_repo


@pytest.mark.asyncio
async def test_secret_roundtrip_and_encryption():
    name = "test_token"
    async with session_scope() as s:
        assert await secrets_repo.has_secret(s, name) is False
        await secrets_repo.set_secret(s, name, "s3cr3t-value-1234567890")
        assert await secrets_repo.has_secret(s, name) is True
        assert await secrets_repo.get_secret(s, name) == "s3cr3t-value-1234567890"

    async with session_scope() as s:
        from redcell_core.models import Secret

        row = await s.get(Secret, name)
        assert row is not None
        assert "s3cr3t-value-1234567890" not in row.value_enc

    async with session_scope() as s:
        assert await secrets_repo.delete_secret(s, name) is True
        assert await secrets_repo.has_secret(s, name) is False
        assert await secrets_repo.get_secret(s, name) == ""
