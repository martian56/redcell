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

Serve the console over HTTPS in any real deployment. Plain HTTP exposes credentials and the session cookie in transit.

The deploy supports automatic HTTPS for a direct domain and a proxy mode for a fronting CDN. See [DEPLOY.md](DEPLOY.md).

## Operator recommendations

- Put the console behind a VPN or an identity-aware proxy if only your team needs it. The strongest pre-auth surface is one the public cannot reach at all.

- If a CDN fronts the origin, restrict the origin to the CDN's source ranges so nobody hits it directly.

- Change the default admin password immediately, or set `REDCELL_ADMIN_*` before first boot so there is never a default.

- Use strong, unique `REDCELL_JWT_SECRET` and `REDCELL_SECRET_KEY`. The deploy generates these per instance.

- Monitor failed logins and unusual access patterns. Alert on spikes.

- Keep the deployment current so fixes land quickly.

- Expose only ports 80 and 443. Keep Postgres, Redis, and MinIO on the internal network.

## Verifying

Load the login page and confirm no version string appears in the page or its assets.

Check response headers do not advertise a version:

```bash
curl -sI https://your-domain/ | grep -iE 'server|x-powered-by' || echo "no banner"
```

Confirm protected routes reject anonymous access:

```bash
curl -so /dev/null -w '%{http_code}\n' https://your-domain/api/v1/sessions
```

Confirm a bad login returns a generic error and does not reveal whether the username exists.

## This change

Issue #63 removed two pre-auth disclosures from the login page.

- The stale `v0.1` version string is gone. No version is shown before authentication.

- The `Console binds to 127.0.0.1` notice is gone. It was inaccurate behind a proxy and described internal topology.

- A regression test (`AuthGate.test.tsx`) asserts the login page contains no version pattern and no bind address.

## Related surfaces to keep clean

- Static asset names and comments should not embed a version.

- Production bundles should not ship source maps that reveal internal structure.
