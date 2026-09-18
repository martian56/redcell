"""SSH connections with host-key verification (trust on first use).

Every SSH client REDCELL opens verifies the server against a persisted
known_hosts file: the key is recorded the first time a host is seen and checked
on every later connection, so a man-in-the-middle that swaps the key after first
contact is rejected instead of silently trusted."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import asyncssh


def _known_hosts_path() -> Path:
    configured = os.environ.get("REDCELL_KNOWN_HOSTS") or "/var/lib/redcell/known_hosts"
    path = Path(configured)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.touch()
        os.access(path, os.W_OK)
        return path
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "redcell_known_hosts"
        fallback.touch(exist_ok=True)
        return fallback


def _host_pattern(host: str, port: int) -> str:
    return host if port == 22 else f"[{host}]:{port}"


def _host_known(path: Path, host: str, port: int) -> bool:
    pattern = _host_pattern(host, port)
    try:
        with path.open() as f:
            return any(line.split(" ", 1)[0] == pattern for line in f)
    except OSError:
        return False


async def _learn(path: Path, host: str, port: int) -> None:
    key = await asyncssh.get_server_host_key(host, port=port)
    if key is None:
        raise asyncssh.HostKeyNotVerifiable(f"no host key offered by {host}")
    line = f"{_host_pattern(host, port)} {key.export_public_key().decode().strip()}\n"
    with path.open("a") as f:
        f.write(line)


async def connect(host: str, *, username: str | None = None, password: str | None = None,
                  private_key: str | None = None, secret: str | None = None, port: int = 22):
    if secret is not None:
        if "PRIVATE KEY" in secret:
            private_key = secret
        else:
            password = secret
    opts: dict = {"username": username or "root", "port": port}
    if private_key:
        opts["client_keys"] = [asyncssh.import_private_key(private_key)]
    elif password:
        opts["password"] = password
    path = _known_hosts_path()
    known = _host_known(path, host, port)
    try:
        return await asyncssh.connect(host, known_hosts=str(path), **opts)
    except asyncssh.HostKeyNotVerifiable:
        if known:
            raise
        await _learn(path, host, port)
        return await asyncssh.connect(host, known_hosts=str(path), **opts)
