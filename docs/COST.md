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

## The price table

`engine/pricing.py` maps a model to `(input, output)` in USD per 1M tokens. Cost is `prompt/1e6 * input + completion/1e6 * output`.

Lookup is by the last path segment, lowercased, so `z-ai/glm-5.2` and `glm-5.2` resolve the same.

An unknown variant falls back to its family (for example an unlisted `glm-5.x` uses a listed GLM price), so a new model still gets a sensible estimate.

Local providers (Ollama) cost nothing, so their estimate is 0 regardless of model.

## Updating prices

Edit `PRICES` in `engine/pricing.py`. Keep entries as USD per 1M tokens `(input, output)`. Prefer real published prices where a model exists.

For OpenRouter you usually do not need a table entry, since the real cost comes back on the response.

## OpenRouter details

The client adds `extra_body={"usage": {"include": true}}` for the `openrouter` provider so the response includes accounting.

It then reads `usage.cost` (USD). This reflects OpenRouter's actual charge, including any per-model routing and discounts.

## Accuracy and caveats

For non-OpenRouter providers the number is an estimate. It is only as accurate as the price table and the usage the provider reports.

Prompt caching, batch discounts, and provider promotions are not modeled in the table, so estimated cost can run high or low.

If a provider omits usage, tokens and cost for that call are 0.

## Budgets

A run can carry a `budget_tokens` ceiling. Track spend against it to stop a run before it runs away.

## Verifying

Start a live run and watch the header: tokens and dollars should climb as calls complete.

On OpenRouter, compare the shown cost against your OpenRouter dashboard for the same period; they should track closely.
