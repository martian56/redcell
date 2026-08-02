"""Repair pasted SSH private keys. PEM/OpenSSH keys are newline-sensitive, but
copy/paste can strip the line breaks, producing a blob no parser accepts.
normalize_private_key reflows it back into valid PEM; non-key input is returned unchanged."""

from __future__ import annotations

import re

_PEM = re.compile(
    r"-----BEGIN ([A-Z0-9 ]+?)-----(.*?)-----END \1-----",
    re.DOTALL,
)


def normalize_private_key(text: str | None) -> str | None:
    if not text:
        return text
    s = text.strip()
    if "PRIVATE KEY" not in s:
        return text  # a password or something else; leave it alone
    m = _PEM.search(s)
    if not m:
        return text  # can't recognize it; let the parser report the real error
    label, body = m.group(1).strip(), m.group(2)
    # Already properly line-wrapped between the markers? Keep as-is.
    if "\n" in body.strip():
        return s if s.endswith("\n") else s + "\n"
    b64 = re.sub(r"\s+", "", body)
    wrapped = "\n".join(b64[i : i + 64] for i in range(0, len(b64), 64))
    return f"-----BEGIN {label}-----\n{wrapped}\n-----END {label}-----\n"
