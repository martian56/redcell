# Pre-authentication surface

What an unauthenticated client can observe from a REDCELL deployment, and the project's stance on each. REDCELL is offensive tooling, so the login boundary is a real target.

## Principles

- Reveal as little as possible before authentication. Nothing that helps an attacker fingerprint or target the instance.
- No version or build identifier is shown before login. Knowing the exact version lets an attacker match it to known issues.
- No credentials or credential hints are shown on a production login page.
- No internal topology (bind addresses, internal hostnames, ports) is described in the UI.
- Authentication errors are generic and do not distinguish unknown user from wrong password.

## Reachable without authentication

- **The login page** (`/`, static assets). Serves the console shell; the app data behind it requires a session cookie.
- **`GET /api/v1/auth/first-run`** reports whether the instance is on its default admin password so the UI can prompt a change. It does not return the password itself.
- **`POST /api/v1/auth/login`** accepts credentials and sets a session cookie. Rate limited.
- **`GET /api/v1/health`** returns a liveness signal for orchestration. It carries no version or build detail.
- Every other API route requires a valid session; unauthenticated calls return 401.
