from __future__ import annotations

_DOCKER_SOCK = "/var/run/docker.sock"


async def _docker_info() -> dict | None:
    try:
        import httpx

        transport = httpx.AsyncHTTPTransport(uds=_DOCKER_SOCK)
        async with httpx.AsyncClient(transport=transport, base_url="http://docker", timeout=5.0) as client:
            r = await client.get("/info")
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def _feature(available: bool, reason: str) -> dict:
    return {"available": available, "reason": reason}


def derive_capabilities(info: dict | None) -> dict:
    reachable = info is not None
    info = info or {}
    os_name = str(info.get("OperatingSystem", ""))
    os_type = str(info.get("OSType", ""))
    kernel = str(info.get("KernelVersion", ""))
    arch = str(info.get("Architecture", ""))
    cpus = int(info.get("NCPU", 0) or 0)
    mem = int(info.get("MemTotal", 0) or 0)
    ram_gb = round(mem / (1024 ** 3), 1) if mem else 0.0
    is_desktop = "Docker Desktop" in os_name
    linux_native = reachable and os_type == "linux" and not is_desktop

    host = {
        "docker_reachable": reachable, "os": os_name, "os_type": os_type,
        "kernel": kernel, "arch": arch, "cpus": cpus, "ram_gb": ram_gb,
    }
    features = {
        "live_execution": _feature(
            reachable,
            "Docker is reachable on the deployment host" if reachable
            else "Docker is not reachable from this deployment; live execution is unavailable"),
        "reverse_shell_catch": _feature(
            linux_native,
            "native Linux Docker host" if linux_native
            else "needs a native Linux Docker host; limited on Docker Desktop, where the host and "
                 "container are on separate networks"),
        "network_pivot": _feature(
            linux_native,
            "native Linux Docker host" if linux_native
            else "needs a native Linux Docker host; not available on Docker Desktop (network split)"),
        "dynamic_mobile": _feature(
            linux_native,
            "runs the app live on this host with redroid (requires the binder kernel module on the host)"
            if linux_native
            else f"this host can't run Android live ({os_name or 'this OS'} has no binder module); "
                 f"attach a Linux host with redroid as a device host to run apps live"),
    }
    return {"host": host, "features": features}


async def host_capabilities() -> dict:
    return derive_capabilities(await _docker_info())
