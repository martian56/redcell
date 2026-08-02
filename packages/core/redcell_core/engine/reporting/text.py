"""Humanize generated prose: strip typographic and phrasing tells that read as
AI-written. Safety net for the narrative prompt's style rules."""

from __future__ import annotations

import re

# Typographic substitutions.
_CHARS = {
    "—": ", ",   # em dash  -> comma
    "–": "-",     # en dash  -> hyphen
    "‘": "'", "’": "'",   # smart single quotes
    "“": '"', "”": '"',   # smart double quotes
    "…": "...",   # ellipsis
    " ": " ",     # non-breaking space
    "•": "-",     # bullet
    "‑": "-",     # non-breaking hyphen
    "​": "",      # zero-width space
}


def humanize(text: str | None) -> str:
    if not text:
        return ""
    for a, b in _CHARS.items():
        text = text.replace(a, b)
    # Clean up artifacts from the em-dash -> ", " swap.
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*,+", ", ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()
