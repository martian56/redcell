"""Fallback token pricing for models LiteLLM does not price.

Prices are USD per 1M tokens as (input, output). LiteLLM is tried first in the
client; this table fills the gap for the catalog models (and future variants
via a family match). Local providers cost nothing.
"""

from __future__ import annotations

PRICES: dict[str, tuple[float, float]] = {
    "gpt-5.6": (5.0, 15.0),
    "gpt-5.5": (3.0, 10.0),
    "gpt-5.4": (2.5, 8.0),
    "gpt-5.4-mini": (0.4, 1.6),
    "o4-mini": (1.1, 4.4),
    "claude-opus-5": (15.0, 75.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-haiku-4-5": (0.8, 4.0),
    "gemini-3.1-pro": (2.5, 10.0),
    "gemini-3.6-flash": (0.3, 2.5),
    "gemini-3.1-flash-lite": (0.1, 0.4),
    "deepseek-v4-pro": (0.6, 1.7),
    "deepseek-v4-flash": (0.3, 0.9),
    "deepseek-r2": (0.7, 2.4),
    "kimi-k3": (0.6, 2.5),
    "kimi-k2.7-code": (0.5, 2.0),
    "glm-5.3": (0.6, 2.2),
    "glm-5.2": (0.5, 1.8),
    "glm-4.6": (0.4, 1.6),
    "glm-4.5-air": (0.2, 1.1),
    "llama-4-70b": (0.6, 0.9),
    "qwen3-72b": (0.6, 0.9),
    "deepseek-v4": (0.6, 1.7),
}

_FREE_PROVIDERS = {"ollama"}


def _norm(model: str) -> str:
    return model.split("/")[-1].strip().lower()


def price_for(model: str) -> tuple[float, float] | None:
    n = _norm(model)
    if n in PRICES:
        return PRICES[n]
    for key, val in PRICES.items():
        if n.startswith(key) or key.startswith(n):
            return val
    fam = n.split("-")[0]
    for key, val in PRICES.items():
        if key.split("-")[0] == fam:
            return val
    return None


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int, provider: str | None = None) -> float:
    if provider in _FREE_PROVIDERS:
        return 0.0
    p = price_for(model)
    if p is None:
        return 0.0
    inp, outp = p
    return round(prompt_tokens / 1_000_000 * inp + completion_tokens / 1_000_000 * outp, 6)
