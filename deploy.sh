#!/usr/bin/env bash
set -euo pipefail

# REDCELL deployment helper.
# Fronts the stack with a Caddy reverse proxy so the web app and API share one
# origin (no CORS). Works with no domain, with a domain (automatic HTTPS), or
# behind a proxy or CDN that terminates TLS.

cd "$(dirname "$0")"
ENV_FILE=".env"

say() { printf '%s\n' "$*"; }
ask() { local p="$1" d="${2:-}" a; read -r -p "$p" a || true; printf '%s' "${a:-$d}"; }

set_env() {
  local key="$1" val="$2"
  touch "$ENV_FILE"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i.bak "s|^${key}=.*|${key}=${val}|" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  else
    printf '%s=%s\n' "$key" "$val" >> "$ENV_FILE"
  fi
}

ask_domain() {
  local d=""
  while ! printf '%s' "$d" | grep -qE '^[A-Za-z0-9][A-Za-z0-9.-]*$'; do
    d=$(ask "  Domain (e.g. redcell.example.com): " "")
  done
  printf '%s' "$d"
}

server_ip() {
  curl -fsS --connect-timeout 5 --max-time 8 https://api.ipify.org 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "your-server-ip"
}

if ! command -v docker >/dev/null 2>&1; then
  say "Docker is not installed."
  yn=$(ask "Install it now with the official get.docker.com script? [Y/n]: " "y")
  case "$yn" in
    n|N|no|NO) say "Install Docker, then re-run this script: https://docs.docker.com/engine/install/"; exit 1 ;;
    *) curl -fsSL https://get.docker.com | sh ;;
  esac
fi
if ! docker compose version >/dev/null 2>&1; then
  say "The Docker Compose plugin is missing; attempting to install it..."
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -y && apt-get install -y docker-compose-plugin
  fi
fi
if ! docker compose version >/dev/null 2>&1; then
  say "Could not set up the Docker Compose plugin. Install it, then re-run this script."
  exit 1
fi

say "=================================================="
say " REDCELL deploy"
say "=================================================="
say ""
say "How will REDCELL be reached?"
say "  1) This server directly, no domain (plain HTTP on the server IP)"
say "  2) A domain pointed straight at this server (automatic HTTPS)"
say "  3) A domain behind Cloudflare, Coolify, or another proxy or CDN (the proxy provides HTTPS)"
mode=$(ask "Choose [1/2/3] (default 1): " "1")

case "$mode" in
  2)
    say ""
    domain=$(ask_domain)
    set_env SITE_ADDRESS "$domain"
    set_env CADDYFILE "Caddyfile"
    set_env REDCELL_COOKIE_SECURE "true"
    set_env REDCELL_CORS_ORIGINS "https://${domain}"
    set_env REDCELL_ENV "production"
    url="https://${domain}"
    say ""
    say "Point an A or AAAA record for ${domain} at this server before continuing."
    say "Caddy requests a TLS certificate automatically on first request."
    ;;
  3)
    say ""
    domain=$(ask_domain)
    set_env SITE_ADDRESS "$domain"
    set_env CADDYFILE "Caddyfile.proxy"
    set_env REDCELL_COOKIE_SECURE "true"
    set_env REDCELL_CORS_ORIGINS "https://${domain}"
    set_env REDCELL_ENV "production"
    url="https://${domain}"
    say ""
    say "Point your proxy or CDN at this server. On Cloudflare, set the SSL mode to Full."
    say "The proxy provides the public certificate; the origin serves its own."
    ;;
  *)
    say ""
    say "WARNING: without a domain, REDCELL is served over plain HTTP."
    say "Login credentials and session cookies are not encrypted in transit."
    ok=$(ask "Continue with an insecure HTTP deployment? [y/N]: " "n")
    case "$ok" in
      y|Y|yes|YES) ;;
      *) say "Aborted. Re-run and choose a domain for HTTPS."; exit 1 ;;
    esac
    ip=$(server_ip)
    host="$ip"
    case "$ip" in *:*) host="[$ip]" ;; esac
    set_env SITE_ADDRESS ":80"
    set_env CADDYFILE "Caddyfile"
    set_env REDCELL_COOKIE_SECURE "false"
    set_env REDCELL_CORS_ORIGINS "http://${host}"
    set_env REDCELL_ENV "production"
    url="http://${host}"
    ;;
esac

set_env REDCELL_COMPOSE_DIR "$(pwd)"

say ""
say "Pulling images..."
docker compose pull

say "Starting the stack..."
docker compose up -d

say ""
say "=================================================="
say " REDCELL is starting at: ${url}"
say ""
say " First run generates an admin password. Read it with:"
say "   docker compose logs init-secrets"
say " Then log in as 'admin' and change it in Settings."
say "=================================================="
