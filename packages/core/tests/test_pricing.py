"""Cost resolution: OpenRouter real cost first, then LiteLLM, then the table."""

import litellm
from redcell_core.engine.llm import LlmClient, _usage, _usage_cost
from redcell_core.engine.pricing import estimate_cost, price_for
from redcell_core.schemas import LlmSettings


def test_price_exact():
    assert price_for("claude-opus-5") == (15.0, 75.0)


def test_price_strips_vendor_prefix():
    assert price_for("z-ai/glm-5.2") == (0.5, 1.8)


def test_price_family_fallback_for_unknown_variant():
    assert price_for("glm-5.9") is not None


def test_estimate_cost_math():
    assert estimate_cost("claude-opus-5", 1_000_000, 1_000_000) == 90.0


def test_estimate_cost_is_zero_for_local_provider():
    assert estimate_cost("glm-4", 1_000_000, 1_000_000, provider="ollama") == 0.0


def test_estimate_cost_zero_for_unknown_model():
    assert estimate_cost("totally-unknown-9000", 1000, 1000) == 0.0


def test_usage_parses_dict():
    assert _usage({"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}) == (15, 10, 5)


def test_usage_total_is_derived_when_missing():
    total, _p, _c = _usage({"usage": {"prompt_tokens": 10, "completion_tokens": 5}})
    assert total == 15


def test_usage_cost_extracted():
    assert _usage_cost({"usage": {"cost": 0.0123}}) == 0.0123


def test_cost_prefers_openrouter_real_cost():
    client = LlmClient(LlmSettings(provider="openrouter", model="z-ai/glm-5.2"))
    resp = {"usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150, "cost": 0.0042}}
    assert client._cost(resp, 100, 50) == 0.0042


def test_cost_falls_back_to_table(monkeypatch):
    monkeypatch.setattr(litellm, "completion_cost", lambda **_: 0.0)
    client = LlmClient(LlmSettings(provider="anthropic", model="claude-opus-5"))
    resp = {"usage": {"prompt_tokens": 1_000_000, "completion_tokens": 0, "total_tokens": 1_000_000}}
    assert client._cost(resp, 1_000_000, 0) == 15.0
