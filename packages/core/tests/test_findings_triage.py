"""Findings triage: status transitions and duplicate merge (issue #6)."""

import pytest
from redcell_core.db import session_scope
from redcell_core.repositories import findings as findings_repo
from redcell_core.repositories import sessions as sessions_repo


async def _session(s, name="T"):
    return await sessions_repo.create(s, {"name": name, "client": "C", "scope": [], "targets": []})


async def _finding(s, sid, **kw):
    data = {"session_id": sid, "title": "T", "severity": "high", "location": "/a"}
    data.update(kw)
    return await findings_repo.create(s, data)


@pytest.mark.asyncio
async def test_set_status_transitions():
    async with session_scope() as s:
        sess = await _session(s)
        f = await _finding(s, sess.id)
        assert f.status == "candidate"
        assert (await findings_repo.set_status(s, f.id, "verified")).status == "verified"
        assert (await findings_repo.set_status(s, f.id, "dismissed")).status == "dismissed"
        # verify() is a shortcut for set_status(..., "verified")
        assert (await findings_repo.verify(s, f.id)).status == "verified"


@pytest.mark.asyncio
async def test_set_status_rejects_unknown_status():
    async with session_scope() as s:
        sess = await _session(s)
        f = await _finding(s, sess.id)
        with pytest.raises(ValueError):
            await findings_repo.set_status(s, f.id, "bogus")


@pytest.mark.asyncio
async def test_set_status_missing_finding_returns_none():
    async with session_scope() as s:
        assert await findings_repo.set_status(s, "RC-nope", "verified") is None


@pytest.mark.asyncio
async def test_merge_dismisses_duplicates_but_keeps_primary_and_other_sessions():
    async with session_scope() as s:
        a = await _session(s, "A")
        b = await _session(s, "B")
        primary = await _finding(s, a.id, title="XSS", location="/x")
        dup = await _finding(s, a.id, title="XSS reflected", location="/x")
        foreign = await _finding(s, b.id, title="XSS", location="/x")
        result = await findings_repo.merge(s, primary.id, [dup.id, foreign.id, primary.id])
        assert result.id == primary.id
        assert (await findings_repo.get(s, dup.id)).status == "dismissed"
        # a finding in another session is never touched
        assert (await findings_repo.get(s, foreign.id)).status == "candidate"
        # the primary stays the canonical record
        assert (await findings_repo.get(s, primary.id)).status == "candidate"


@pytest.mark.asyncio
async def test_merge_missing_primary_returns_none():
    async with session_scope() as s:
        assert await findings_repo.merge(s, "RC-nope", []) is None
