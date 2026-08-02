# REDCELL platform

Red-team platform backend. Postgres holds state, Redis carries pub/sub plus the
job queue and cache, MinIO stores files, and a separate arq worker runs the
agents. The API stays thin: it serves REST and WebSockets and enqueues runs.

- `packages/core` (`redcell_core`): shared library. Config, db (async
  SQLAlchemy 2.0), models, schemas, repositories, storage (MinIO), bus (Redis),
  crypto (Fernet), the engine (LangGraph runner, sim, execution, listeners,
  reporting), the `rc` CLI, and Alembic migrations.
- `apps/api`: FastAPI. Routers go through repositories and enqueue worker jobs.
- `apps/worker`: arq worker. Runs the engine (sim or live) and publishes live
  output onto Redis.

## Run modes

- **sim** (default): the simulator publishes real events, chat questions, and
  shell output. No provider keys, Docker, or target needed.
- **live** (`REDCELL_RUN_MODE=live`): the LangGraph engine runs real agents
  through LiteLLM, executes commands (Kali container or SSH VPS), and catches
  reverse shells. Needs `uv sync --group live` and provider keys in Settings.

Both publish onto the same channels (`events:{runId}`, `chat:{runId}`,
`shell:{shellId}`), so the UI is identical either way.

## Dev quick start

```bash
# 1. infrastructure (from repo root)
docker compose -f docker-compose.dev.yml up -d      # redis + postgres + minio

# 2. Python deps (uv workspace, shared .venv at repo root)
uv sync --group live                                 # omit --group live for sim-only

# 3. database + seed
uv run rc db upgrade                                 # apply migrations
uv run rc seed --demo                                # admin + providers + demo data
#   rc seed            bootstrap only (buckets, providers, admin, settings)
#   rc seed --unseed   wipe Postgres app data + empty MinIO buckets

# 4. run the three processes (separate terminals)
cd apps/api    && uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
cd apps/worker && uv run arq worker.settings.WorkerSettings
bun dev                                              # frontend on :5183
```

Open http://localhost:5183 and sign in with `admin` / `admin`. Health check:
`curl http://localhost:8080/health`.

## Configuration (env, `REDCELL_` prefix)

| Var | Default | Notes |
| --- | --- | --- |
| `REDCELL_ENV` | `dev` | `unseed` is guarded outside dev |
| `REDCELL_DATABASE_URL` | `postgresql+asyncpg://redcell:redcell@localhost:5432/redcell` | |
| `REDCELL_REDIS_URL` | `redis://localhost:6379/0` | pub/sub + arq + cache |
| `REDCELL_RUN_MODE` | `sim` | `sim` or `live` |
| `REDCELL_S3_ENDPOINT` / `_ACCESS_KEY` / `_SECRET_KEY` | localhost:9000 / minioadmin | MinIO / S3 |
| `REDCELL_SECRET_KEY` | dev Fernet key | encrypts stored SSH/proxy creds; set a real one in prod |
| `REDCELL_JWT_SECRET` | dev value | set 32+ bytes in prod |
| `REDCELL_ADMIN_USERNAME` / `_PASSWORD` | admin / admin | seeded admin |
| `REDCELL_CORS_ORIGINS` | `http://localhost:5183` | comma-separated |

## Tests

```bash
uv run pytest        # repos, storage vs MinIO, engine, worker, API smoke, seed
```

## Files and reports

- Upload (API-proxied): `POST /sessions/{id}/files`. Download: `GET /files/{id}`
  redirects to a short-TTL presigned URL (private) or the public URL.
- Buckets: `uploads`, `loot`, `reports`, `public` (env-overridable).
- Reports: `POST /sessions/{id}/reports` enqueues generation. The worker writes a
  PDF plus JSON and SARIF to the `reports` bucket and the API serves them back.
