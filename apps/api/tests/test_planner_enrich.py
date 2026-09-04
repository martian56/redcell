"""The planner fallback fills draft fields from the operator's text."""

from app.routers.ai import enrich_proposal
from redcell_core.schemas import SessionProposal


def test_fills_from_bare_domain_when_model_returns_nothing():
    p = enrich_proposal(None, "do a full pentest on Ufazien, its domain is ufazien.com")
    assert p is not None
    assert p.kind == "network"
    assert p.scope == ["ufazien.com"]
    assert p.targets == ["https://ufazien.com"]
    assert p.name == "Ufazien assessment"


def test_fills_gaps_but_keeps_model_values():
    model = SessionProposal(name="Custom name", scope=["keep.example.com"], brief="focus on auth")
    p = enrich_proposal(model, "target is app.acme.com")
    assert p.name == "Custom name"          # not overwritten
    assert p.scope == ["keep.example.com"]  # not overwritten
    assert p.brief == "focus on auth"       # preserved
    assert p.targets == ["https://app.acme.com"]  # gap filled


def test_git_url_is_a_code_review():
    p = enrich_proposal(None, "review the code at https://github.com/org/repo")
    assert p is not None
    assert p.kind == "code"
    assert p.source == "https://github.com/org/repo"
    assert p.scope == [] and p.targets == []


def test_cidr_goes_to_scope():
    p = enrich_proposal(None, "assess the 10.0.0.0/24 range")
    assert p is not None
    assert "10.0.0.0/24" in p.scope


def test_no_target_no_proposal():
    assert enrich_proposal(None, "hi, can you help me plan something later?") is None
