# Hardening & threat model

REDCELL runs real offensive tooling, catches reverse shells, and stores provider
API keys and SSH credentials. Treat it as sensitive infrastructure.

> **Never expose REDCELL to the public internet.** Bind it to localhost or a
> private network, put it behind a VPN or an authenticated reverse proxy with
> TLS, and restrict who can reach it. The console has a single operator account;
> it is not a multi-tenant, internet-facing service.

## Threat model in one paragraph

The console is the control plane for tools that can compromise machines. The main
risks are: someone other than the operator reaching the console (or its API/WebSocket
endpoints), a deployment running on the shipped/default secrets, the agent acting
outside the authorized scope, and stored loot/credentials leaking. The items below
address each.

## Deploying safely

- **Set `REDCELL_ENV` to something other than `dev`.** Outside dev the app refuses
  to start on the built-in placeholder secrets and fails fast until real ones are
  provided.
- **Provide real secrets.** `REDCELL_JWT_SECRET`, `REDCELL_SECRET_KEY` (a Fernet
  key), and `REDCELL_ADMIN_PASSWORD` — via env vars or `*_FILE` paths. The shipped
  `docker compose up` generates unique ones into a volume on first run and prints
  the admin password once; change it after logging in. Never reuse the dev values.
- **Serve over HTTPS and keep secure cookies on.** The default compose sets
  `REDCELL_COOKIE_SECURE=true`; the `docker-compose.local.yml` override turns it off
  only for local http. Behind a TLS reverse proxy, keep it on.
- **Lock down the network.** The API binds `127.0.0.1` by default. Do not publish
  it, the worker, Postgres, Redis, or MinIO to untrusted networks. The Kali
  container runs with host networking so it can reach targets and catch shells —
  run REDCELL on a host you control and segment it from anything you care about.
- **Scope every engagement.** Set the session scope; the engine enforces it in code
  at the tool boundary (out-of-scope targets are refused, and an obviously
  destructive `run_command` is blocked). An empty scope is unrestricted by design —
  only leave it empty on a lab you own.
- **Rotate provider keys** you add in Settings if the host is ever compromised;
  they are encrypted at rest with `REDCELL_SECRET_KEY`, so that key is as sensitive
  as the keys themselves.

## Data retention

- **Loot and credentials** the agent captures are stored in Postgres (the `loot`
  table) and MinIO (the `loot` bucket), encrypted where marked sensitive. There is
  no automatic expiry today — treat the database and buckets as holding live secrets
  for the duration you keep them, and purge a session's data when the engagement
  ends if you do not need the record.
- **Reports** (PDF/JSON/SARIF) live in the `reports` bucket; delete them when no
  longer needed.
- **Checkpoints** (`redcell-checkpoints.sqlite`) contain run conversation state;
  they are local to the worker host.

## Authorized use only

Point REDCELL only at systems you own or are contracted to test, and stay within
the rules of engagement. See [SECURITY.md](../SECURITY.md) to report a vulnerability
in REDCELL itself.
