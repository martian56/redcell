"""Operator terminal: an interactive shell driven from the Terminals panel.
Keystrokes arrive on `shellin:{id}`; on Enter the buffered line runs in the
execution backend and output streams back on `shell:{id}`. Each command is a
fresh exec, so the working directory does not persist between commands."""

from __future__ import annotations

from ..bus import Bus, shell_channel, shell_input_channel
from ..config import settings
from ..db import session_scope
from ..repositories import settings as settings_repo
from ..repositories import shells as shells_repo
from ..schemas import ExecutionSettings

_PROMPT = "\x1b[38;5;43moperator@kali\x1b[0m:~$ "


async def _make_backend():
    async with session_scope() as s:
        cfg = await settings_repo.get(s)
    exec_cfg = ExecutionSettings(**cfg.execution) if cfg.execution else ExecutionSettings()
    from .execution import LocalDockerBackend, SimBackend, SSHBackend

    if settings.run_mode == "live" and exec_cfg.backend == "local-docker":
        b = LocalDockerBackend(exec_cfg.docker_image, name="redcell-opsh")
        try:
            await b.ensure()
            return b
        except Exception:
            return SimBackend()
    if settings.run_mode == "live" and exec_cfg.backend == "ssh-vps" and exec_cfg.ssh_host:
        return SSHBackend(exec_cfg.ssh_host, exec_cfg.ssh_user or "root")
    return SimBackend()


async def run_operator_shell(bus: Bus, shell_id: str) -> None:
    backend = await _make_backend()
    await bus.publish(shell_channel(shell_id),
                      f"\x1b[38;5;43m# {backend.kind} terminal ready\x1b[0m\r\n{_PROMPT}")
    buf = ""
    async for chunk in bus.subscribe(shell_input_channel(shell_id)):
        for ch in chunk:
            if ch in ("\r", "\n"):
                cmd = buf.strip()
                buf = ""
                await bus.publish(shell_channel(shell_id), "\r\n")
                # stop if the operator closed the terminal
                async with session_scope() as s:
                    if await shells_repo.get(s, shell_id) is None:
                        return
                if cmd:
                    try:
                        await backend.run(cmd, on_output=lambda line: bus.publish(shell_channel(shell_id), line))
                    except Exception as exc:
                        await bus.publish(shell_channel(shell_id), f"error: {exc}\r\n")
                await bus.publish(shell_channel(shell_id), _PROMPT)
            elif ch == "\x7f":  # backspace
                if buf:
                    buf = buf[:-1]
            else:
                buf += ch
