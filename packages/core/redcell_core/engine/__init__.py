"""Agent orchestration engine: LangGraph runner, sim producer, execution
backends, reverse-shell catcher, and the provider-agnostic LLM client. Runs in
the worker process; publishes live output onto the bus."""
