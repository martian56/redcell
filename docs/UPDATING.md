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

**No Update button.** Either you are already up to date, the build is `dev`, or `REDCELL_COMPOSE_DIR` is unset. Set it and redeploy to enable the button.

**"In-app update is not available on this deployment."** `REDCELL_COMPOSE_DIR` is not set. `deploy.sh` sets it; add it to `.env` and `docker compose up -d`.

**Updater cannot run compose.** The updater image lacks the compose plugin. Set `REDCELL_UPDATER_IMAGE` to an image that includes it.

**Update did not apply.** Confirm compose tracks `:latest` and that the new images were published. Check `docker compose logs` for the pull.

**Version still old after update.** The images may not carry a baked `REDCELL_VERSION` yet. Only releases built after this feature include it.

**Permission denied on the socket.** The api container must have access to `/var/run/docker.sock`. The compose file mounts it by default.

**Stuck updating.** The pull may be slow on a large image. Give it time, then check `docker compose ps` and logs.

## API

- `GET /api/v1/system/version` returns `{ current, latest, updateAvailable }`.

- `POST /api/v1/system/update` (admin) starts the update and returns `{ started, detail }`.

Both require a valid session; update additionally requires the admin role.

## Configuration

- `REDCELL_COMPOSE_DIR` - host path of the checkout; enables the button.

- `REDCELL_UPDATER_IMAGE` - image for the one-shot updater (default `docker:cli`).

- `REDCELL_VERSION` - baked into the image at build; the running version.

## End to end

1. The banner polls the version endpoint and compares against the latest release.
2. An admin clicks Update.
3. The api launches a detached updater container with the socket and the checkout mounted.
4. The updater pulls new images and runs `up -d`, which re-applies migrations.
5. The app restarts; the banner shows the new version.

## What updates

The api, worker, and web images update to the new release. Postgres, Redis, and MinIO stay on their pinned versions.

Your data in the named volumes is preserved across the update.

## FAQ

**Is the update safe to run during work?** It restarts the stack, so avoid it mid-engagement. Data is preserved, but active connections drop briefly.

**Should I back up first?** Backing up the database and volumes before an update is good practice. See DEPLOY.md.

**Does it need internet?** Yes, to check the latest release and to pull new images.

**How do I disable it?** Leave `REDCELL_COMPOSE_DIR` unset. The endpoint then refuses and the button does nothing useful.

**Why not Watchtower?** Watchtower recreates containers but does not re-run the compose one-shots, so migrations would be skipped. Running compose keeps migrations in the loop.

**Can it auto-update on a schedule?** Not yet; updates are on demand from the button.

## Best practices

- Update in a quiet window, not during a live run.

- Take a database dump first for anything important.

- Verify the new version in Settings after the restart.

- Pin a version if you need change control rather than always tracking latest.

## Notes

Running the update when already current is harmless: the pull finds nothing new and `up -d` is a no-op.

This feature ships in a release; a deployment must be updated once (by shell) to pick it up before the button exists.

## References

- `apps/api/app/routers/system.py` - the version and update endpoints.
- `apps/web/src/app/UpdateBanner.tsx` - the Settings banner.
- Issue #66 - the request this implements.
