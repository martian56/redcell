# Updating REDCELL

Two ways to update a self-hosted REDCELL: the in-app Update button, or pulling and restarting from the shell.

## In-app update

Settings shows a version banner. When a newer release exists, an admin sees an Update button.

The banner shows the running version and, when available, the latest release to update to.

## How the version is known

The running version is baked into the api and worker images at build time as `REDCELL_VERSION`, set from the release tag.

The latest version comes from the GitHub Releases API for the repository, cached briefly to avoid rate limits.

An update is offered when the latest release compares greater than the running version. A `dev` build never shows an update.

## What the button does

It calls an admin-only endpoint that launches a one-shot updater container on the host.

The updater runs `docker compose pull` then `docker compose up -d` against this deployment's compose file.

`up -d` re-runs the one-shot `migrate` service, so database migrations in the new version are applied automatically.

## Why a one-shot container

The api container cannot cleanly recreate itself: `up -d` would kill the process mid-update. A separate one-shot container is not part of the recreate, so it survives and finishes the job.

## Downtime

There is a few-second gap while the api, worker, and web containers restart. The UI reconnects on its own; the version banner then shows the new version.

## Requirements for the button

- `REDCELL_COMPOSE_DIR` must point at the host checkout so the updater can find the compose file. `deploy.sh` sets it; leave it blank to disable the button.

- The api container needs the docker socket (it already mounts it to run tools).

- The updater image (`REDCELL_UPDATER_IMAGE`, default `docker:cli`) needs the docker compose plugin.

- Compose tracks `:latest`, so a pull fetches the new build.

## Security
