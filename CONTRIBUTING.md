# Contributing to REDCELL

Thanks for your interest in REDCELL. This guide covers how to set the project up,
the conventions we follow, and how to get a change merged.

First, the important part: REDCELL is offensive security tooling. Only run it
against systems you own or are explicitly authorized to test, and only propose
features that respect that boundary. See [SECURITY.md](SECURITY.md) and the
responsible-use note in the README.

By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting set up

You will need Docker, [uv](https://docs.astral.sh/uv/), and [bun](https://bun.sh/).

```bash
# infrastructure (Postgres, Redis, MinIO)
docker compose -f docker-compose.dev.yml up -d

# python deps, database, seed data
uv sync --group live
uv run rc db upgrade
uv run rc seed
cp .env.example .env

# run the three processes in separate terminals
cd apps/api    && uv run uvicorn app.main:app --host 127.0.0.1 --port 8080
cd apps/worker && uv run arq worker.settings.WorkerSettings
cd apps/web    && bun install && bun run dev
```

The app runs at http://localhost:5183 (sign in with `admin` / `admin`). Runs
default to a safe simulation. Set `REDCELL_RUN_MODE=live` in `.env` to execute
real tools.

## Tests and checks

The backend suite runs against real infrastructure, isolated to throwaway
test-only resources (a `*_test` database, Redis db 15, `test-*` buckets), so it
never touches your dev data. Bring the infra up first, then:

```bash
uv run pytest
```

Frontend:

```bash
cd apps/web
bun run typecheck
bun run build
```

CI runs all of these on every pull request. Make sure they pass locally before
opening one.

## Code style

- Python: type hints, small focused modules, follow the patterns already in the
  codebase.
- TypeScript and React: strict TS, functional components, the existing store and
  hook patterns.
- Comments explain the why, not the what. Keep them terse.
- Writing style, and this one matters here: no em-dashes, no smart quotes, and no
  marketing or AI-sounding phrasing anywhere. That applies to code comments, UI
  copy, docs, and commit messages. Use plain, direct language and match the
  surrounding code.

## Commits and pull requests

- Branch off `main`. Do not commit directly to `main`.
- Keep each pull request focused on one change.
- We loosely follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`,
  `test:`, `ci:`, `style:`).
- In the pull request, say what changed and why, and link any related issue.
- Confirm `pytest`, `typecheck`, and `build` pass.
- If your change touches the UI, include a screenshot.

## Reporting bugs and requesting features

Use the issue templates. For anything security-sensitive, do not open a public
issue. Follow [SECURITY.md](SECURITY.md) instead.
