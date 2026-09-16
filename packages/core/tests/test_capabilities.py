from redcell_core.capabilities import derive_capabilities

_LINUX = {"OSType": "linux", "OperatingSystem": "Ubuntu 26.04.1 LTS",
          "KernelVersion": "7.0.0-30-generic", "Architecture": "x86_64",
          "NCPU": 2, "MemTotal": 4_000_000_000}
_DESKTOP = {"OSType": "linux", "OperatingSystem": "Docker Desktop",
            "KernelVersion": "x", "Architecture": "x86_64", "NCPU": 4, "MemTotal": 8_000_000_000}


def _avail(caps):
    return {k: v["available"] for k, v in caps["features"].items()}


def test_native_linux_supports_everything():
    caps = derive_capabilities(_LINUX)
    assert caps["host"]["docker_reachable"] and caps["host"]["ram_gb"] == 3.7
    assert all(_avail(caps).values())


def test_docker_desktop_blocks_host_bound_features():
    a = _avail(derive_capabilities(_DESKTOP))
    assert a["live_execution"] is True
    assert a["reverse_shell_catch"] is False
    assert a["network_pivot"] is False
    assert a["dynamic_mobile"] is False


def test_no_docker_disables_all():
    caps = derive_capabilities(None)
    assert caps["host"]["docker_reachable"] is False
    assert not any(_avail(caps).values())
