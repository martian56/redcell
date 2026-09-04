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

The updater pulls and recreates only the app services (`api`, `worker`, `web`) and re-runs `migrate`, leaving the reverse proxy and datastores running. That keeps the proxy up (no full-stack restart) and avoids a port-bind race on the proxy container.

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

## See also

- [DEPLOY.md](DEPLOY.md) - deploying and the update commands in context.
- [COST.md](COST.md) - unrelated, but another operator reference.

## Tip

To watch an update happen, keep Settings open: the banner flips from Update available to the new version once the stack comes back.

## Summary

Baked version in, latest release out, an admin button that runs compose in a side container. Data is kept; migrations run; the app restarts.

## Reconnecting

If the page shows a connection error during the restart, wait a few seconds; it reconnects automatically once the api is back.

## Single operator

REDCELL has one operator account, which is the admin, so the admin gate means the signed-in operator.

## Watching the updater

The updater runs as its own container; `docker ps` shows it briefly, and its logs show the pull and recreate.

## Latest is cached

The latest-release lookup is cached for a few minutes, so a brand-new release can take a moment to appear in the banner.

## Manual trigger

You can trigger the same update from the shell with the compose commands above; the button is a convenience, not the only path.

## Where the version comes from

The banner's current version is whatever `REDCELL_VERSION` the running image was built with; a locally built image without the build-arg reports `dev`.

## The update panel

Triggering an update opens a panel that shows progress instead of a single line of text.

It shows four steps: starting the update, pulling images and restarting, reconnecting to the console, and up to date.

Progress is driven by polling the version endpoint: while the app is reachable and still on the old version it shows "applying"; while the api restarts and the endpoint is unreachable it shows "reconnecting"; once the version catches up it shows "up to date".

On completion the panel reloads the console so the new web bundle and version load. A Reload now button is offered as well.

If the update cannot start (for example when in-app update is disabled on the deployment) or takes too long, the panel shows an error and a close action.

The panel can be opened from the sidebar Update pill or the Settings banner.

While the update is applying the panel stays put; you can dismiss it once it is done or has failed.

The update runs server-side, so closing or navigating away does not stop it; the panel just visualizes it.

### Panel states

**Starting** - the update request is being sent to the server.

**Applying** - images are pulling and the app services are recreating.

**Reconnecting** - the api is restarting and the console is waiting for it to answer again.

**Up to date** - the running version matches the latest release; the panel reloads shortly.

**Failed** - the update could not start or did not complete in time; close and check the server.

### Timing

The panel polls every few seconds, so it advances within seconds of each real transition.

There is a brief window where the api is down during recreate; the panel shows reconnecting rather than an error.

After a long wait with no progress the panel gives up and shows an error so you are not left staring at a spinner.

### Accessibility

The panel is a labelled dialog with an aria-live region, so state changes are announced.

Actions are ordinary buttons, reachable and operable by keyboard.

Backdrop dismissal is only enabled once the update is done or failed, so a click does not close it mid-apply.

### For contributors

The panel is `apps/web/src/app/UpdateDialog.tsx`; it takes an open flag, an onClose, and the target version.

Render it wherever an update can be triggered and pass the latest version as the target; it handles the request and polling itself.

It treats the update as done when the version endpoint reports the target version or no longer reports an update available.

A ref guards against starting the update twice if the effect re-runs while open.

A cancelled flag stops polling and the reload if the panel closes mid-flight.

### Verifying

In mock mode the updater is stateful: after the update call the version flips to the target, so the panel walks through to done.

Verify the panel in a browser: open it, watch the steps check off, and confirm it reloads.

On a real deployment the same panel reflects the actual restart and version flip.

### Troubleshooting

**Panel does not open.** The trigger only appears when an update is available; otherwise there is nothing to apply.

**"Could not start the update."** In-app update is disabled (no compose dir set) or the server rejected it; check the deployment.

**Stuck on reconnecting.** The api is taking a while to come back; give it time, then reload manually if needed.

**Did not reload.** Use the Reload now button; the new bundle loads on the next full load.

### Panel FAQ

**Can I close it and keep working?** Yes, once it is done or failed. The update itself runs server-side regardless.

**Is the progress real?** The steps reflect real transitions (request, restart, version flip); it is not a fake timer.

**Why does it reload?** The web bundle is part of the update, so a reload loads the new frontend.

**Do I get logged out?** No; the session cookie persists across the restart and reload.

**What if I click twice?** A guard prevents starting the update more than once while the panel is open.

### References

- `apps/web/src/app/UpdateDialog.tsx` - the panel.

- `apps/web/src/app/DashboardShell.tsx` - the sidebar trigger.

- `apps/web/src/app/UpdateBanner.tsx` - the Settings trigger.

- Issue #78 - the update progress panel.

### Notes

Both triggers render the same panel component, so the experience is identical wherever you start.

The target version passed to the panel is the latest release, used to detect completion precisely.

Polling is capped so a broken update surfaces as an error instead of polling forever.

Seeing reconnecting briefly is normal; it means the app services are being recreated.

Only the app services restart during an update, so the proxy stays up and the panel can keep polling through it.

The panel's title changes with state: Updating REDCELL while in progress, Updated when done, Update failed on error.

Each step shows a spinner while active, a check when complete, and a marker if the update failed at that point.

The target version is shown next to the title so you can confirm what you are updating to.

The detail line under the steps gives a short human message for the current state.

The footer shows a reassurance while applying, a Reload now button when done, and a Close button on error.

The panel does not block the rest of the app from finishing in-flight work; it only reflects the update.

Because the check compares versions numerically, it recognizes completion even across a multi-part version bump.

If the version endpoint briefly returns the old version right after the request, the panel simply keeps showing applying.

The reconnecting state is entered on any fetch failure, which is the expected signal during the api restart.

The panel is intentionally small and centered, matching the console's other dialogs.

It reuses the shared overlay and modal styles, with its own step list styles.

The spinner respects reduced-motion preferences.

The steps are a fixed sequence, so their order is predictable and easy to scan.

The panel closes on its own only by reloading when done; otherwise you dismiss it.

Triggering from the sidebar keeps you on your current page while the update runs.

Triggering from Settings keeps the update near the version information there.

The same admin gate applies on the server no matter where the panel was opened.

The panel is safe to open again after a failure to retry the update.

There is no partial state persisted; each open starts a fresh attempt.

The panel is a thin client over the version and update endpoints, with no extra server support needed.

Keeping the panel open is fine; it does not consume server resources beyond the light version poll.

The panel's polling stops as soon as it reaches done or error, or when it is closed.

A reload after done is the cleanest way to guarantee the new assets are in use.

If you dismiss the done state without reloading, the app keeps the old bundle until the next full load.

The panel does not attempt to stream container logs; it infers progress from observable state.

This keeps it robust: it works even though the api that serves it restarts mid-update.

The reconnect handling is why the panel survives the very restart it is reporting on.

For a no-op update (already current), the panel reaches done almost immediately.

The panel is unit tested for opening, triggering the update, and rendering the steps.

Its end-to-end behavior, including the reload, is verified in a browser.

The mock updater is stateful so the browser walk-through reaches the done state.

The panel and the sidebar version indicator share the same version data source.

Together they give a clear loop: see an update, apply it, watch it land.

No configuration is needed to use the panel beyond the in-app update being enabled on the deployment.

If in-app update is disabled, opening the panel surfaces that clearly rather than failing silently.

The panel is theme-aware and reads well in both light and dark.

It is small enough not to obscure the whole screen, so context stays visible behind it.

That is the update panel: honest, staged progress that survives the restart and lands on the new version.
