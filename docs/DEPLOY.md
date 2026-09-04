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
- Ports 80 and 443 free on the host (nothing else bound to them).

## Quick start

```bash
git clone https://github.com/martian56/redcell.git
cd redcell
./deploy.sh
```

`deploy.sh` installs Docker if needed, asks how REDCELL will be reached, writes `.env`, pulls the images, and starts the stack.

## Deployment modes

`deploy.sh` offers three ways to reach REDCELL. Each writes a matching set of values to `.env`; nothing else needs editing.

| Mode | SITE_ADDRESS | CADDYFILE | Cookie secure |
| --- | --- | --- | --- |
| 1. Direct, no domain | `:80` | `Caddyfile` | false |
| 2. Domain, direct | `your-domain` | `Caddyfile` | true |
| 3. Domain, behind a proxy | `your-domain` | `Caddyfile.proxy` | true |

### 1. This server directly, no domain

Serves plain HTTP on the server IP. Good for a quick trial or a trusted private network.

Credentials travel unencrypted, so `deploy.sh` asks you to confirm. Do not use this over the public internet for anything real.

You reach it at `http://SERVER_IP`.

### 2. A domain pointed straight at this server

Caddy obtains a Let's Encrypt certificate automatically and serves `https://your-domain`. This is the simplest way to get real HTTPS.

Point an `A` record (and `AAAA` if you use IPv6) for the domain at the server before you run it. Caddy needs the domain to resolve to this host to pass the ACME challenge.

Ports 80 and 443 must be reachable from the internet; Let's Encrypt validates over them.

### 3. A domain behind Cloudflare, Coolify, or another proxy

A proxy or CDN in front holds the public certificate and forwards traffic to this server. Caddy here serves both plain HTTP on :80 and its own self-signed HTTPS on :443, so it answers whichever way the proxy connects.

Use this when the domain does not resolve directly to the server, for example when it is proxied through Cloudflare or fronted by Coolify. In that case Caddy cannot complete a Let's Encrypt challenge itself, so it uses an internal certificate instead.

This mode mounts `docker/caddy/Caddyfile.proxy` by setting `CADDYFILE=Caddyfile.proxy` in `.env`.

## Behind Cloudflare

When a domain's DNS record is proxied (the orange cloud), it resolves to Cloudflare, not your server. Choose mode 3.

Set the Cloudflare SSL/TLS mode to **Full**. Cloudflare then connects to the origin over HTTPS and accepts the self-signed certificate Caddy serves.

**Flexible** also works: Cloudflare connects to the origin over plain HTTP on :80, which the proxy config serves too.

**Full (strict)** rejects the self-signed origin certificate. To use it, install a Cloudflare Origin Certificate on the server, or switch the record to DNS-only and use mode 2.

A Cloudflare **521** means the origin refused the connection on the port Cloudflare tried. Usually the deploy is still in IP mode (:80 only) while Cloudflare is set to Full and reaching for :443. Re-run `deploy.sh` and choose mode 3.

To skip Cloudflare's proxy entirely, set the DNS record to DNS-only (grey cloud) pointing at the server and use mode 2 for a direct Let's Encrypt certificate.

## Behind Coolify or another reverse proxy

If Coolify, Traefik, nginx, or a cloud load balancer terminates TLS and forwards to this host, use mode 3. Point the proxy's upstream at the server on port 80 (HTTP) or 443 (HTTPS, self-signed accepted).

The app marks its login cookie `Secure` based on `REDCELL_COOKIE_SECURE`, not the request scheme, so cookies work even though the proxy reaches the origin over HTTP. Mode 3 sets this to `true` for you.

## DNS

For a direct domain (mode 2), create an `A` record for the domain pointing at the server's IPv4 address.

Add an `AAAA` record too if the server has a public IPv6 address; otherwise an IPv6-only client cannot reach it.

Let DNS propagate before the first request so the certificate can be issued. `getent hosts your-domain` on the server should return the server's own IP.

## Ports and firewall

Only Caddy publishes ports: 80 and 443 (plus 443/udp for HTTP/3). Open both in any cloud firewall or security group.

Everything else (5432, 6379, 9000) stays on the internal network and should not be opened.

## Cookies and HTTPS

`REDCELL_COOKIE_SECURE=true` marks the session cookie `Secure`, so the browser only sends it over HTTPS. Modes 2 and 3 set it to `true`; mode 1 (plain HTTP) uses `false`.

Browsers treat `http://localhost` as a secure context, so a local `docker compose up` still logs in even with a secure cookie. A plain-HTTP deploy on a public IP does not, which is why mode 1 uses `false`.

## First login

The first run generates an admin password. Read it with:

```bash
docker compose logs init-secrets
```

Sign in as `admin` with that password, then change it in Settings. The password persists in the `redcell_secrets` volume across redeploys.

## Updating

```bash
cd redcell
git pull
docker compose pull
docker compose up -d
```

Because the deploy mode lives entirely in `.env`, a `git pull` never conflicts with local changes. Your mode is preserved across updates.

## Changing how it is reached

Re-run `./deploy.sh` and pick a different option, or edit `SITE_ADDRESS`, `CADDYFILE`, `REDCELL_COOKIE_SECURE`, and `REDCELL_CORS_ORIGINS` in `.env` and run `docker compose up -d`.

## Backups

State lives in named volumes: `redcell_pg` (database), `redcell_minio` (files), and `redcell_secrets` (keys and admin password). Back these up.

Database dump:

```bash
docker compose exec -T postgres pg_dump -U redcell redcell > redcell.sql
```

## Verifying the deployment

Check every container is up and the infra ones are healthy:

```bash
docker compose ps
```

The web app should return 200 and the API should return 401 (auth required) on the same origin:

```bash
curl -sI https://your-domain/
curl -so /dev/null -w '%{http_code}\n' https://your-domain/api/v1/sessions
```

## Troubleshooting

**Port 80 or 443 already in use.** Another service is bound to it. Stop it, or free the port before deploying. Caddy needs both.

**Certificate never issues (mode 2).** The domain must resolve to this server and ports 80/443 must be reachable from the internet. If the domain is proxied by a CDN, use mode 3 instead.

**Cloudflare 521.** The origin is not listening on the port Cloudflare uses. Use mode 3 so Caddy serves :443, and set Cloudflare SSL to Full.

**Cloudflare 526.** Full (strict) rejected the self-signed origin certificate. Switch Cloudflare to Full, install a Cloudflare Origin Certificate, or use DNS-only plus mode 2.

**Login does not stick.** Over plain HTTP on an IP the secure cookie is dropped. Use a domain, or accept mode 1 which sets the cookie insecure.

**CORS errors.** All traffic should go through Caddy on one origin. Reach REDCELL at its `SITE_ADDRESS`, not the API port directly.

**Something is failing.** Read the logs of a service, for example `docker compose logs api` or `docker compose logs caddy`.

## Security notes

Secrets are generated per deployment and stored in the `redcell_secrets` volume. There are no usable default credentials outside dev.

REDCELL runs offensive tooling. Only point it at systems you are authorized to test. See [HARDENING.md](HARDENING.md).

## Removing it

`docker compose down` stops the stack and keeps your data. Add `-v` to delete the volumes and wipe everything.

## FAQ

**Can I run it locally to try it?** Yes: `docker compose up` serves it at `http://localhost`. Secure cookies work because browsers trust localhost.

**Can I use a subdomain?** Yes, `redcell.example.com` works exactly like a bare domain in modes 2 and 3.
