# Security Policy

REDCELL is a red-team platform that runs real offensive tooling. Two things fall
under this policy: vulnerabilities in REDCELL itself, and responsible use of the
tool.

## Supported versions

REDCELL is under active development. Security fixes land on the `main` branch.
Until there is a tagged release, treat the latest `main` as the only supported
version.

## Reporting a vulnerability

Report security issues privately. Do not open a public issue, pull request, or
discussion for anything exploitable.

Preferred: use GitHub's private vulnerability reporting on this repository. Go to
the Security tab and click "Report a vulnerability". This opens a private
advisory that only you and the maintainers can see.

Alternative: email the maintainer at fuadelizade469@gmail.com.

Please include:

- what the issue is and where it lives (file, endpoint, or component),
- steps to reproduce or a proof of concept,
- the impact you believe it has.

You can expect an acknowledgement within a few days. Once a fix is ready we will
coordinate disclosure with you.

## Responsible use

REDCELL exists for authorized security testing: engagements you are contracted
for, CTFs, and your own labs. Do not point it at systems you do not own or have
written permission to test. Doing so is likely illegal, and the responsibility
is yours, not the maintainers'. See the responsible-use note in the README.
