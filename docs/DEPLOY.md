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
