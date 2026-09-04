#!/usr/bin/env bash
set -euo pipefail

# REDCELL deployment helper.
# Fronts the stack with a Caddy reverse proxy so the web app and API share one
# origin (no CORS), and optionally provisions HTTPS for a domain.

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

has_domain=$(ask "Do you have a domain pointing at this server? [y/N]: " "n")
case "$has_domain" in
  y|Y|yes|YES)
    domain=""
    while [ -z "$domain" ]; do
      domain=$(ask "  Domain (e.g. redcell.example.com): " "")
    done
    set_env "SITE_ADDRESS" "$domain"
    set_env "REDCELL_COOKIE_SECURE" "true"
    set_env "REDCELL_CORS_ORIGINS" "https://${domain}"
    set_env "REDCELL_ENV" "production"
    url="https://${domain}"
    say ""
    say "Point an A/AAAA DNS record for ${domain} at this server before continuing."
    say "Caddy will request a TLS certificate automatically on first request."
    ;;
  *)
    ip=$(curl -fsS https://api.ipify.org 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "your-server-ip")
    set_env "SITE_ADDRESS" ":80"
    set_env "REDCELL_COOKIE_SECURE" "false"
    set_env "REDCELL_CORS_ORIGINS" "http://${ip}"
    set_env "REDCELL_ENV" "production"
    url="http://${ip}"
    say ""
    say "No domain: serving over plain HTTP. Set up a domain later for HTTPS."
    ;;
esac

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
