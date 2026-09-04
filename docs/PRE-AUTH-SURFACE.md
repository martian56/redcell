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

## What the login page shows

The login page shows only the product name and the sign-in form. It does not show a version string.

It does not claim a bind address. Where the console binds is a deployment detail, not something to advertise on the login screen.

In development, when the admin password is still the default, a hint block explains how to change it. Set real `REDCELL_ADMIN_*` values (or let the deploy generate them) so no hint is shown in production.

## HTTP headers

Responses should not carry a version or framework banner. Avoid `X-Powered-By` and a descriptive `Server` header on public responses.

Behind a reverse proxy you can strip or rewrite server-identifying headers at the edge as a second layer.

## Authentication errors

A failed login returns a generic message. The UI shows "Invalid credentials." for both an unknown username and a wrong password, so the response does not confirm which usernames exist.

Avoid leaking account existence through response timing where practical.

## Rate limiting

`POST /auth/login` is rate limited to slow credential stuffing and brute force. The draft-chat endpoint is rate limited too.

Add IP-based rate limiting or a WAF at the proxy for defense in depth.

## Session cookies

The session cookie is HttpOnly so page scripts cannot read it.

Over HTTPS the cookie is marked Secure (`REDCELL_COOKIE_SECURE=true`), so it is never sent over plain HTTP.

The cookie uses a SameSite policy to limit cross-site submission.

## Transport
