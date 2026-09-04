# Pre-authentication surface

What an unauthenticated client can observe from a REDCELL deployment, and the project's stance on each. REDCELL is offensive tooling, so the login boundary is a real target.

## Principles

- Reveal as little as possible before authentication. Nothing that helps an attacker fingerprint or target the instance.
- No version or build identifier is shown before login. Knowing the exact version lets an attacker match it to known issues.
- No credentials or credential hints are shown on a production login page.
