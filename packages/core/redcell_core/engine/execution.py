"""Execution backends: where agent commands run.

  - SimBackend    : no external deps; canned output.
  - LocalDocker   : `docker exec` into a long-lived Kali container on this host.
  - SSHBackend    : asyncssh to a remote VPS.

Backends stream output line by line through an async callback."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ..config import settings
from ..schemas import ExecutionSettings

OnOutput = Callable[[str], Awaitable[None]]


@dataclass
class ExecResult:
    exit_code: int
    output: str


class ExecutionBackend:
    kind = "base"

    async def start(self, on_status: OnOutput | None = None) -> None:
        return None

    async def run(self, command: str, on_output: OnOutput | None = None) -> ExecResult:
        raise NotImplementedError

    async def close(self) -> None:
        return None


class SimBackend(ExecutionBackend):
    kind = "sim"

    _CANNED = {
        "nmap": "Starting Nmap\n443/tcp open  https\n22/tcp open  ssh\nNmap done: 1 host up",
        "httpx": "https://app.acme-corp.io [200] [nginx]\nhttps://api.acme-corp.io [200] [Kong]",
        "sqlmap": "[INFO] parameter 'q' is injectable\navailable databases [4]: acme_prod, mysql, sys, information_schema",
        "curl": "HTTP/1.1 200 OK\nserver: nginx",
    }

    async def run(self, command: str, on_output: OnOutput | None = None) -> ExecResult:
        head = command.strip().split() or ["sh"]
        body = self._CANNED.get(head[0], f"$ {command}\n(simulated) ok")
        for line in body.splitlines():
            if on_output:
                await on_output(line + "\r\n")
            await asyncio.sleep(0.15)
        return ExecResult(exit_code=0, output=body)


class LocalDockerBackend(ExecutionBackend):
    kind = "local-docker"

    def __init__(self, image: str, name: str = "redcell-exec",
                 proxy_env: dict[str, str] | None = None,
                 mounts: list[str] | None = None) -> None:
        self.image = image
        self.name = name
        self.proxy_env = proxy_env or {}
        self.mounts = mounts or []  # entries like "/host/path:/src:ro"

    async def start(self, on_status: OnOutput | None = None) -> None:
        await self._docker("rm", "-f", self.name, check=False)
        if not await self._image_present():
            if on_status:
                await on_status(f"pulling image {self.image} (first run, this can take a few minutes)...")
            await self._pull()
            if on_status:
                await on_status(f"image {self.image} ready")
        args = ["run", "-d", "--name", self.name, "--network", "host"]
        for m in self.mounts:
            args += ["-v", m]
        args += [self.image, "sleep", "infinity"]
        await self._docker(*args)

    async def ensure(self, on_status: OnOutput | None = None) -> None:
        """Create the container only if it is not already running (idempotent)."""
        proc = await asyncio.create_subprocess_exec(
            "docker", "inspect", "-f", "{{.State.Running}}", self.name,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        assert proc.stdout is not None
        out = (await proc.stdout.read()).decode(errors="replace").strip()
        await proc.wait()
        if out == "true":
            return
        await self.start(on_status=on_status)

    async def _image_present(self) -> bool:
        proc = await asyncio.create_subprocess_exec(
            "docker", "image", "inspect", self.image,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0

    async def _pull(self) -> None:
        proc = await asyncio.create_subprocess_exec(
            "docker", "pull", self.image,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout is not None
        out = await proc.stdout.read()
        await proc.wait()
        if proc.returncode != 0:
            lines = out.decode(errors="replace").strip().splitlines()
            raise RuntimeError(f"docker pull {self.image} failed: {lines[-1] if lines else 'unknown error'}")

    async def run(self, command: str, on_output: OnOutput | None = None) -> ExecResult:
        env_args: list[str] = []
        for k, v in self.proxy_env.items():
            env_args += ["-e", f"{k}={v}"]
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", *env_args, self.name, "sh", "-c", command,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        chunks: list[str] = []
        assert proc.stdout is not None
        async for raw in proc.stdout:
            line = raw.decode(errors="replace")
            chunks.append(line)
            if on_output:
                await on_output(line.rstrip("\n") + "\r\n")
        await proc.wait()
        return ExecResult(exit_code=proc.returncode or 0, output="".join(chunks))

    async def close(self) -> None:
        await self._docker("rm", "-f", self.name, check=False)

    async def _docker(self, *args: str, check: bool = True) -> None:
        proc = await asyncio.create_subprocess_exec(
            "docker", *args,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        if check and proc.returncode != 0:
            raise RuntimeError(f"docker {' '.join(args)} failed ({proc.returncode})")


class SSHBackend(ExecutionBackend):
    kind = "ssh-vps"

    def __init__(self, host: str, user: str, password: str | None = None, private_key: str | None = None,
                 proxy_env: dict[str, str] | None = None) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.private_key = private_key
        self.proxy_env = proxy_env or {}
        self._conn = None

    def _wrap(self, command: str) -> str:
        if not self.proxy_env:
            return command
        prefix = " ".join(f"{k}={_shq(v)}" for k, v in self.proxy_env.items())
        return f"env {prefix} sh -c {_shq(command)}"

    async def start(self, on_status: OnOutput | None = None) -> None:
        import asyncssh  # lazy

        opts: dict = {"username": self.user, "known_hosts": None}
        if self.private_key:
            opts["client_keys"] = [asyncssh.import_private_key(self.private_key)]
        elif self.password:
            opts["password"] = self.password
        self._conn = await asyncssh.connect(self.host, **opts)

    async def run(self, command: str, on_output: OnOutput | None = None) -> ExecResult:
        import asyncssh  # lazy

        if self._conn is None:
            await self.start()
        assert self._conn is not None
        # Merge stderr into stdout with asyncssh.STDOUT. Passing a bare `1` makes
        # asyncssh treat it as a LOCAL fd to wrap, which throws "[WinError 6] The
        # handle is invalid" on Windows and breaks every SSH command.
        proc = await self._conn.create_process(self._wrap(command), stderr=asyncssh.STDOUT)
        chunks: list[str] = []
        async for line in proc.stdout:
            chunks.append(line)
            if on_output:
                await on_output(line.rstrip("\n") + "\r\n")
        result = await proc.wait()
        return ExecResult(exit_code=result.exit_status or 0, output="".join(chunks))

    async def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            await self._conn.wait_closed()


class RemoteDockerBackend(ExecutionBackend):
    """A Kali container on a remote host, driven over one outbound SSH connection
    (ssh host -> `docker exec kali ...`). The container uses --network host so
    listeners bind on the host public IP and can catch reverse shells. Docker is
    auto-installed on the remote via get.docker.com if missing."""

    kind = "remote-docker"

    def __init__(self, host: str, user: str, password: str | None = None, private_key: str | None = None,
                 image: str = "redcell/kali:latest", name: str = "redcell-exec",
                 proxy_env: dict[str, str] | None = None, mounts: list[str] | None = None) -> None:
        self.host = host
        self.user = user or "root"
        self.password = password
        self.private_key = private_key
        self.image = image
        self.name = name
        self.proxy_env = proxy_env or {}
        self.mounts = mounts or []
        self._conn = None

    async def connection(self):
        if self._conn is None:
            import asyncssh
            opts: dict = {"username": self.user, "known_hosts": None}
            if self.private_key:
                opts["client_keys"] = [asyncssh.import_private_key(self.private_key)]
            elif self.password:
                opts["password"] = self.password
            self._conn = await asyncssh.connect(self.host, **opts)
        return self._conn

    async def _sh(self, cmd: str) -> tuple[int, str]:
        conn = await self.connection()
        r = await conn.run(cmd, check=False)
        return (r.exit_status or 0), ((r.stdout or "") + (r.stderr or ""))

    async def _install_docker(self, on_status: OnOutput | None) -> None:
        if on_status:
            await on_status("Docker not found on the remote; installing via the official get.docker.com script...")
        sudo = "" if self.user == "root" else "sudo "
        # Official Docker install (https://docs.docker.com/engine/install/): the
        # get.docker.com convenience script covers Debian/Ubuntu/Kali/CentOS/etc.
        await self._sh(f"{sudo}sh -c 'curl -fsSL https://get.docker.com | sh'")
        await self._sh(f"{sudo}sh -c 'systemctl enable --now docker 2>/dev/null || "
                       f"service docker start 2>/dev/null || dockerd >/dev/null 2>&1 &'")
        code, out = await self._sh("docker --version")
        if code != 0:
            raise RuntimeError(f"Docker install failed on remote: {out.strip()[-200:]}")
        if on_status:
            await on_status(f"Docker ready on remote: {out.strip()[:80]}")

    async def start(self, on_status: OnOutput | None = None) -> None:
        await self.connection()
        code, _ = await self._sh("command -v docker >/dev/null 2>&1")
        if code != 0:
            await self._install_docker(on_status)
        await self._ensure_image(on_status)
        await self._sh(f"docker rm -f {self.name} >/dev/null 2>&1")
        mounts = "".join(f"-v {_shq(m)} " for m in self.mounts)
        code, out = await self._sh(
            f"docker run -d --name {self.name} --network host {mounts}{self.image} sleep infinity")
        if code != 0:
            raise RuntimeError(f"remote docker run failed: {out.strip()[-200:]}")
        # The listener/catcher needs python3; a slim base image may lack it.
        await self._sh(f"docker exec {self.name} sh -c 'command -v python3 >/dev/null 2>&1 || "
                       f"(apt-get update && apt-get install -y --no-install-recommends python3) >/dev/null 2>&1 || true'")
        if on_status:
            await on_status(f"Kali container running on {self.host} ({self.name}, host network)")

    async def _ensure_image(self, on_status: OnOutput | None) -> None:
        if (await self._sh(f"docker image inspect {self.image} >/dev/null 2>&1"))[0] == 0:
            return
        if on_status:
            await on_status(f"pulling {self.image} on the remote...")
        if (await self._sh(f"docker pull {self.image}"))[0] == 0:
            return
        # Not in a registry (e.g. a locally-built redcell/kali). Transfer the
        # local image to the remote once via `docker save | ssh docker load`.
        if not await self._local_image_present():
            raise RuntimeError(f"remote can't pull {self.image} and it isn't available locally to transfer")
        if on_status:
            await on_status(f"{self.image} isn't in a registry; transferring it to the remote (one-time, large)...")
        await self._transfer_image()
        if (await self._sh(f"docker image inspect {self.image} >/dev/null 2>&1"))[0] != 0:
            raise RuntimeError(f"image transfer to remote did not produce {self.image}")
        if on_status:
            await on_status(f"{self.image} loaded on the remote")

    async def _local_image_present(self) -> bool:
        proc = await asyncio.create_subprocess_exec(
            "docker", "image", "inspect", self.image,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await proc.wait()
        return proc.returncode == 0

    async def _transfer_image(self) -> None:
        conn = await self.connection()
        local = await asyncio.create_subprocess_exec(
            "docker", "save", self.image,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        remote = await conn.create_process("docker load", encoding=None)
        assert local.stdout is not None
        try:
            while True:
                chunk = await local.stdout.read(1 << 16)
                if not chunk:
                    break
                remote.stdin.write(chunk)
                await remote.stdin.drain()
            remote.stdin.write_eof()
        finally:
            await local.wait()
            await remote.wait()

    async def ensure(self, on_status: OnOutput | None = None) -> None:
        await self.connection()
        _, out = await self._sh(f"docker inspect -f '{{{{.State.Running}}}}' {self.name} 2>/dev/null")
        if out.strip() == "true":
            return
        await self.start(on_status=on_status)

    async def run(self, command: str, on_output: OnOutput | None = None) -> ExecResult:
        import asyncssh

        conn = await self.connection()
        envs = "".join(f"-e {_shq(f'{k}={v}')} " for k, v in self.proxy_env.items())
        full = f"docker exec {envs}{self.name} sh -c {_shq(command)}"
        proc = await conn.create_process(full, stderr=asyncssh.STDOUT)
        chunks: list[str] = []
        async for line in proc.stdout:
            chunks.append(line)
            if on_output:
                await on_output(line.rstrip("\n") + "\r\n")
        result = await proc.wait()
        return ExecResult(exit_code=result.exit_status or 0, output="".join(chunks))

    async def close(self) -> None:
        # Leave the container running on the remote (caught shells / artifacts
        # outlive one run); drop the SSH connection.
        if self._conn is not None:
            self._conn.close()
            try:
                await self._conn.wait_closed()
            except Exception:
                pass
            self._conn = None


def _shq(s: str) -> str:
    """POSIX single-quote a value for safe use in a remote shell command."""
    return "'" + s.replace("'", "'\\''") + "'"


def _looks_like_private_key(secret: str | None) -> bool:
    return bool(secret) and "PRIVATE KEY" in secret


def proxy_env_from_url(url: str | None) -> dict[str, str]:
    """Build the standard proxy env vars from a proxy URL. Empty dict if no url."""
    if not url:
        return {}
    keep_local = "localhost,127.0.0.1,::1"
    env = {}
    for k in ("http_proxy", "https_proxy", "all_proxy"):
        env[k] = url
        env[k.upper()] = url
    env["no_proxy"] = keep_local
    env["NO_PROXY"] = keep_local
    return env


def make_backend(cfg: ExecutionSettings | None = None) -> ExecutionBackend:
    cfg = cfg or ExecutionSettings()
    if settings.run_mode != "live":
        return SimBackend()
    if cfg.backend == "local-docker":
        return LocalDockerBackend(cfg.docker_image)
    if cfg.backend == "ssh-vps" and cfg.ssh_host:
        return SSHBackend(cfg.ssh_host, cfg.ssh_user or "root")
    return SimBackend()


def build_backend(cfg: ExecutionSettings | None = None, *, server=None, server_secret: str | None = None,
                  proxy_url: str | None = None, name: str = "redcell-exec",
                  mounts: list[str] | None = None) -> ExecutionBackend:
    """Backend for one run, honoring a session's chosen server + proxy.

    - server given  -> SSH onto that saved host (credentials from server_secret).
    - else cfg.backend decides (local-docker container, or a global ssh-vps host).
    Proxy env (from proxy_url) is injected into every command the backend runs."""
    cfg = cfg or ExecutionSettings()
    if settings.run_mode != "live":
        return SimBackend()
    penv = proxy_env_from_url(proxy_url)
    if server is not None:
        # Remote server: run inside a Kali container on that host over SSH.
        pk = server_secret if _looks_like_private_key(server_secret) else None
        pw = None if pk else (server_secret or None)
        return RemoteDockerBackend(server.host, getattr(server, "username", None) or "root",
                                   password=pw, private_key=pk, image=cfg.docker_image,
                                   name=name, proxy_env=penv, mounts=mounts)
    # No server chosen: local execution on this host (execution host is a
    # per-session choice, not a global backend switch).
    return LocalDockerBackend(cfg.docker_image, name=name, proxy_env=penv, mounts=mounts)
