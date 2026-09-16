from redcell_core.config import settings
from redcell_core.engine.execution import DeviceHostBackend, build_device_backend
from redcell_core.schemas import ExecutionSettings


class _Server:
    host = "10.1.2.3"
    username = "root"


def test_redroid_run_cmd_uses_published_port_and_screen():
    b = DeviceHostBackend("h", "root", screen="1080x1920", redroid_image="redroid/redroid:13.0.0_64only-latest")
    cmd = b._redroid_run_cmd()
    assert "--privileged" in cmd
    assert "-p 127.0.0.1:5555:5555" in cmd
    assert "androidboot.redroid_width=1080" in cmd
    assert "androidboot.redroid_height=1920" in cmd
    assert "--name redcell-redroid" in cmd


def test_bad_screen_falls_back_to_default_dims():
    b = DeviceHostBackend("h", "root", screen="not-a-size")
    assert b._dims() == ("720", "1280")


def test_boot_wait_script_polls_boot_completed():
    b = DeviceHostBackend("h", "root")
    s = b._boot_wait_script(tries=5)
    assert "adb connect 127.0.0.1:5555" in s
    assert "getprop sys.boot_completed" in s
    assert "seq 1 5" in s


def test_build_device_backend_uses_mobile_image():
    cfg = ExecutionSettings(mobileDockerImage="ghcr.io/x/redcell-mobile:latest", redroidScreen="480x800")
    prev = settings.run_mode
    settings.run_mode = "live"
    try:
        b = build_device_backend(cfg, server=_Server(), server_secret="pw")
    finally:
        settings.run_mode = prev
    assert isinstance(b, DeviceHostBackend)
    assert b.image == "ghcr.io/x/redcell-mobile:latest"
    assert b.screen == "480x800"
    assert b.kind == "device-host"
