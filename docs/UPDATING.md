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

The docker socket is root-equivalent on the host. The update endpoint is a real privilege boundary.

Only an admin can trigger an update, and only when `REDCELL_COMPOSE_DIR` is set. If you do not want in-app updates, leave it unset.

Updates pull `:latest` from the project's registry. Trust that registry, or pin to a specific version tag you have reviewed.

## Updating from the shell

```bash
cd redcell
git pull
docker compose pull
docker compose up -d
```

This is the same set of steps the button runs, plus a `git pull` to refresh the compose file and scripts.

## Rolling back

Pin the image tags to a previous version (for example `:0.3.2`) in an override, or check out the matching commit and `docker compose up -d`.

## Verifying an update

After the restart, the Settings banner shows the new version and reads Up to date.

The version endpoint returns the running and latest versions:

```bash
curl -s https://your-domain/api/v1/system/version
```

`docker compose ps` should show the app containers recently recreated.

## Troubleshooting
