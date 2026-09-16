"""Dynamic mobile actions against a redroid Android device over ADB + Frida.

The commands run inside the mobile-tools container (adb, frida, objection) that
the DeviceHostBackend brings up; adb talks to the device at 127.0.0.1:5555 and
frida is reached over an adb-forwarded port."""

from __future__ import annotations

from dataclasses import dataclass

FRIDA_PORT = 27042
DEVICE_SERIAL = "127.0.0.1:5555"

_FRIDA_ARCH = {
    "x86_64": "x86_64",
    "arm64-v8a": "arm64",
    "x86": "x86",
    "armeabi-v7a": "arm",
    "armeabi": "arm",
}

SSL_UNPIN_STARTUP = "android sslpinning disable"


def frida_arch(abi: str) -> str:
    return _FRIDA_ARCH.get((abi or "").strip(), (abi or "").strip())


def frida_server_url(version: str, abi: str) -> str:
    return (f"https://github.com/frida/frida/releases/download/{version}/"
            f"frida-server-{version}-android-{frida_arch(abi)}.xz")


def _q(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def adb(rest: str, serial: str = DEVICE_SERIAL) -> str:
    return f"adb -s {serial} {rest}"


def connect(serial: str = DEVICE_SERIAL) -> str:
    return f"adb connect {serial} >/dev/null 2>&1"


def frida_setup_script(version: str, abi: str, serial: str = DEVICE_SERIAL) -> str:
    url = frida_server_url(version, abi)
    return "; ".join([
        connect(serial),
        f"adb -s {serial} root >/dev/null 2>&1 || true",
        "sleep 2",
        connect(serial),
        f"curl -fsSL {_q(url)} -o /tmp/fs.xz",
        "xz -d -f /tmp/fs.xz",
        f"adb -s {serial} push /tmp/fs /data/local/tmp/frida-server >/dev/null 2>&1",
        f"adb -s {serial} shell chmod 755 /data/local/tmp/frida-server",
        f"adb -s {serial} shell 'pkill -f frida-server >/dev/null 2>&1 || true'",
        f"adb -s {serial} shell 'nohup /data/local/tmp/frida-server >/dev/null 2>&1 &'",
        "sleep 3",
        f"adb -s {serial} forward tcp:{FRIDA_PORT} tcp:{FRIDA_PORT} >/dev/null 2>&1",
        f"echo frida-server {version} started",
    ])


def frida_ps() -> str:
    return f"frida-ps -H 127.0.0.1:{FRIDA_PORT}"


def frida_run_script(package: str, script_path: str, timeout: int = 30) -> str:
    return (f"timeout {timeout} frida -H 127.0.0.1:{FRIDA_PORT} -f {_q(package)} "
            f"-l {_q(script_path)} --no-pause -q; true")


def objection_startup(package: str, startup: str, timeout: int = 40) -> str:
    return (f"timeout {timeout} objection -N -h 127.0.0.1 -p {FRIDA_PORT} -g {_q(package)} "
            f"explore --startup-command {_q(startup)}; true")


def install(remote_apk: str) -> str:
    return adb(f"install -r -g {_q(remote_apk)}")


def packages(third_party_only: bool = True) -> str:
    flag = " -3" if third_party_only else ""
    return adb(f"shell pm list packages{flag}")


def launch(package: str) -> str:
    return adb(f"shell monkey -p {_q(package)} -c android.intent.category.LAUNCHER 1")


def device_shell(command: str) -> str:
    return adb(f"shell {_q(command)}")


def input_action(kind: str, value: str) -> str:
    if kind == "tap":
        return adb(f"shell input tap {value}")
    if kind == "text":
        return adb(f"shell input text {_q(value)}")
    if kind == "key":
        return adb(f"shell input keyevent {_q(value)}")
    return adb(f"shell input {kind} {_q(value)}")


def pull_b64(remote_path: str) -> str:
    return adb(f"exec-out cat {_q(remote_path)} | base64 -w0")


def screencap_b64() -> str:
    return adb("exec-out screencap -p | base64 -w0")


@dataclass
class MobileResult:
    ok: bool
    output: str
    detail: str = ""
