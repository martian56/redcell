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
