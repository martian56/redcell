"""Provider-agnostic LLM client built on LiteLLM. `complete` returns the assistant
message with any tool calls."""

from __future__ import annotations

from typing import Any

from ..schemas import LlmSettings

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
        resp = await litellm.acompletion(model=self._model(), messages=messages, **kwargs)
        choice = resp["choices"][0]["message"]
        out: dict[str, Any] = {"role": "assistant", "content": choice.get("content") or ""}
        tcs = choice.get("tool_calls") or []
        if tcs:
            out["tool_calls"] = [
                {"id": tc["id"], "name": tc["function"]["name"], "arguments": tc["function"]["arguments"]}
                for tc in tcs
            ]
        out["usage_tokens"] = _usage_total(resp)
        try:
            out["cost"] = float(litellm.completion_cost(completion_response=resp) or 0.0)
        except Exception:
            out["cost"] = 0.0
        return out


def _usage_total(resp: Any) -> int:
    usage = resp.get("usage") if hasattr(resp, "get") else None
    if usage is None:
        return 0
    if hasattr(usage, "total_tokens"):
        return int(getattr(usage, "total_tokens") or 0)
    try:
        return int(usage.get("total_tokens") or 0)
    except Exception:
        return 0
