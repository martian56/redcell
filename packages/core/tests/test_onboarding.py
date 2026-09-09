import pytest
from redcell_core.db import session_scope
from redcell_core.repositories import settings as settings_repo


@pytest.mark.asyncio
async def test_dismiss_action_is_idempotent_and_persisted():
    async with session_scope() as s:
        assert await settings_repo.dismissed_actions(s) == []
        await settings_repo.dismiss_action(s, "ngrok")
        await settings_repo.dismiss_action(s, "ngrok")
        await settings_repo.dismiss_action(s, "ai-key")

    async with session_scope() as s:
        dismissed = await settings_repo.dismissed_actions(s)
        assert dismissed.count("ngrok") == 1
        assert set(dismissed) == {"ngrok", "ai-key"}
