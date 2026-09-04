# Deploying REDCELL

REDCELL self-hosts with Docker Compose behind a Caddy reverse proxy. One command brings the whole stack up, with or without a domain.

The short version lives in the [README](../README.md#deploy-self-host); this guide covers every mode and the things that go wrong.

## Architecture

Caddy is the only service that publishes ports (80 and 443). It serves the web app and proxies `/api/*` to the API on the same origin, so there is no CORS to configure.
