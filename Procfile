api: cd apps/api && uv run uvicorn app.main:app --host 127.0.0.1 --port 8080
worker: cd apps/worker && uv run arq worker.settings.WorkerSettings
web: cd apps/web && bun run dev
