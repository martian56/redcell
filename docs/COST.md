# Cost and token accounting

How REDCELL measures what a run spends, and why the number is what it is.

## Providers report tokens, not dollars

Native LLM APIs (OpenAI, Anthropic, Google, DeepSeek, and so on) return token usage - `prompt_tokens`, `completion_tokens`, `total_tokens` - not a dollar amount. The cost is computed from those tokens and a per-model price.

The exception is OpenRouter, which can return the actual charge in `usage.cost` when the request asks for it. REDCELL uses that real number when available.
