"""Provider-agnostic LLM client built on LiteLLM. `complete` returns the assistant
message with any tool calls."""

from __future__ import annotations

from typing import Any

from ..config import settings
from ..schemas import LlmSettings
from .pricing import estimate_cost

# provider id -> LiteLLM model prefix. Providers LiteLLM does not route natively
# fall back to an OpenAI-compatible base URL from settings.
_PREFIX = {
    "openai": "",
    "anthropic": "anthropic/",
    "google": "gemini/",
    "xai": "xai/",
    "deepseek": "deepseek/",
    "moonshot": "moonshot/",
    "zhipu": "zhipu/",
    "qwen": "dashscope/",
    "mistral": "mistral/",
    "groq": "groq/",
    "together": "together_ai/",
    "fireworks": "fireworks_ai/",
    "cohere": "cohere/",
    "perplexity": "perplexity/",
    "deepinfra": "deepinfra/",
    "openrouter": "openrouter/",
    "ollama": "ollama/",
    "custom": "openai/",
}


class LlmClient:
    def __init__(self, cfg: LlmSettings) -> None:
        self.cfg = cfg

    def _model(self) -> str:
        prefix = _PREFIX.get(self.cfg.provider, "")
        model = self.cfg.model
        return model if model.startswith(prefix) or not prefix else prefix + model

    def _kwargs(self) -> dict[str, Any]:
        kw: dict[str, Any] = {}
        if self.cfg.api_key:
            kw["api_key"] = self.cfg.api_key
        if self.cfg.api_base:
            kw["api_base"] = self.cfg.api_base
        elif self.cfg.provider == "ollama":
            kw["api_base"] = "http://localhost:11434"
        if self.cfg.reasoning_effort and self.cfg.provider in ("openai", "anthropic"):
            kw["reasoning_effort"] = self.cfg.reasoning_effort
        kw["num_retries"] = settings.llm_num_retries
        kw["timeout"] = settings.llm_timeout_seconds
        return kw

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        import litellm  # lazy: live mode only

        kwargs = self._kwargs()
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        # Ask OpenRouter to report the actual charge in usage.cost.
        if self.cfg.provider == "openrouter":
            kwargs.setdefault("extra_body", {})["usage"] = {"include": True}
        resp = await litellm.acompletion(model=self._model(), messages=messages, **kwargs)
        choice = resp["choices"][0]["message"]
        out: dict[str, Any] = {"role": "assistant", "content": choice.get("content") or ""}
        tcs = choice.get("tool_calls") or []
        if tcs:
            out["tool_calls"] = [
                {"id": tc["id"], "name": tc["function"]["name"], "arguments": tc["function"]["arguments"]}
                for tc in tcs
            ]
        total, prompt, completion = _usage(resp)
        out["usage_tokens"] = total
        out["cost"] = self._cost(resp, prompt, completion)
        return out

    def _cost(self, resp: Any, prompt_tokens: int, completion_tokens: int) -> float:
        # 1. OpenRouter reports the real charge in usage.cost when include is set.
        if self.cfg.provider == "openrouter":
            direct = _usage_cost(resp)
            if direct:
                return direct
        # 2. LiteLLM's price map, accurate for models it knows.
        try:
            import litellm

            metered = float(litellm.completion_cost(completion_response=resp) or 0.0)
            if metered:
                return metered
        except Exception:
            pass
        # 3. Our fallback table for the catalog models.
        return estimate_cost(self.cfg.model, prompt_tokens, completion_tokens, self.cfg.provider)


def _usage_obj(resp: Any) -> Any:
    if resp is None:
        return None
    if hasattr(resp, "get"):
        return resp.get("usage")
    return getattr(resp, "usage", None)


def _field(obj: Any, name: str) -> Any:
    if obj is None:
        return None
    if hasattr(obj, name):
        return getattr(obj, name)
    if hasattr(obj, "get"):
        return obj.get(name)
    return None


def _int(v: Any) -> int:
    try:
        return int(v or 0)
    except Exception:
        return 0


def _usage(resp: Any) -> tuple[int, int, int]:
    u = _usage_obj(resp)
    total = _int(_field(u, "total_tokens"))
    prompt = _int(_field(u, "prompt_tokens"))
    completion = _int(_field(u, "completion_tokens"))
    if not total:
        total = prompt + completion
    return total, prompt, completion


def _usage_cost(resp: Any) -> float:
    u = _usage_obj(resp)
    try:
        return float(_field(u, "cost") or 0.0)
    except Exception:
        return 0.0
