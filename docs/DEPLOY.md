# Deploying REDCELL

REDCELL self-hosts with Docker Compose behind a Caddy reverse proxy. One command brings the whole stack up, with or without a domain.

The short version lives in the [README](../README.md#deploy-self-host); this guide covers every mode and the things that go wrong.

## Architecture

Caddy is the only service that publishes ports (80 and 443). It serves the web app and proxies `/api/*` to the API on the same origin, so there is no CORS to configure.

Postgres, Redis, MinIO, the API, and the web app stay on the internal Docker network and are never exposed to the internet.

Stored files (reports, loot, uploads) are streamed through the API, so MinIO never needs a public route.

## What gets deployed

- **postgres** — application database (named volume `redcell_pg`).
- **redis** — job queue and pub/sub for live updates.
- **minio** — S3-compatible object storage (named volume `redcell_minio`).
- **init-secrets** — generates the secret key, JWT secret, and first admin password on first run.
- **migrate** — applies database migrations and seeds the provider catalog, then exits.
- **api** — the FastAPI backend.
- **worker** — the arq worker that runs engagements and generates reports.
- **web** — the built React console served by nginx.
- **caddy** — the reverse proxy and TLS terminator (named volumes `caddy_data`, `caddy_config`).

## Prerequisites

- A Linux server you can SSH into as root (or a sudo user). 2 GB RAM is enough to start; more helps when engagements run.
- Docker Engine with the Compose plugin. `deploy.sh` installs both if they are missing.
