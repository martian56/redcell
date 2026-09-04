# Cost and token accounting

How REDCELL measures what a run spends, and why the number is what it is.

## Providers report tokens, not dollars

Native LLM APIs (OpenAI, Anthropic, Google, DeepSeek, and so on) return token usage - `prompt_tokens`, `completion_tokens`, `total_tokens` - not a dollar amount. The cost is computed from those tokens and a per-model price.

The exception is OpenRouter, which can return the actual charge in `usage.cost` when the request asks for it. REDCELL uses that real number when available.

## How cost is resolved

For each LLM call, cost is resolved in order:

1. **OpenRouter real cost** - for the `openrouter` provider, the request sets `usage.include`, and the response's `usage.cost` is the charge.
2. **LiteLLM price map** - `litellm.completion_cost` multiplies the returned tokens by LiteLLM's own prices for models it knows.
3. **REDCELL price table** - a fallback in `engine/pricing.py` for models LiteLLM does not price (the catalog uses forward-looking model names LiteLLM has no entry for).

If none apply (an unknown model on a direct provider), cost is 0 rather than a wrong guess.

## Why spend used to read \$0.00

The model catalog uses names like `glm-5.3`, `claude-opus-5`, and `deepseek-v4-pro`. LiteLLM has no prices for them, so `completion_cost` returned 0 and the run never accumulated any cost. The price-table fallback fixes this.

## Per-run accumulation

Each metered call adds its tokens and cost onto the run via `runs.set_meters`. The run's `tokens` and `cost_usd` grow as the engagement proceeds.

The console header shows the running totals next to Elapsed and Model.
