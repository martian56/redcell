from redcell_core.engine.llm import LlmClient
from redcell_core.schemas import LlmSettings


def test_kwargs_include_retries_and_timeout():
    kw = LlmClient(LlmSettings(provider="openai", model="gpt-5.6", api_key="x"))._kwargs()
    assert kw["num_retries"] >= 1
    assert kw["timeout"] > 0
