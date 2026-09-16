from redcell_core.engine import mobile


def test_frida_arch_maps_android_abis():
    assert mobile.frida_arch("x86_64") == "x86_64"
    assert mobile.frida_arch("arm64-v8a") == "arm64"
    assert mobile.frida_arch("armeabi-v7a") == "arm"
    assert mobile.frida_arch("weird") == "weird"


def test_frida_server_url():
    url = mobile.frida_server_url("17.18.0", "arm64-v8a")
    assert url == ("https://github.com/frida/frida/releases/download/17.18.0/"
                   "frida-server-17.18.0-android-arm64.xz")


def test_setup_script_roots_and_forwards():
    s = mobile.frida_setup_script("17.18.0", "x86_64")
    assert "adb -s 127.0.0.1:5555 root" in s
    assert "frida-server-17.18.0-android-x86_64.xz" in s
    assert f"forward tcp:{mobile.FRIDA_PORT} tcp:{mobile.FRIDA_PORT}" in s
    assert "/data/local/tmp/frida-server" in s


def test_install_and_packages_builders():
    assert "install -r -g" in mobile.install("/root/assessment/app.apk")
    assert mobile.packages(True).endswith("pm list packages -3")
    assert mobile.packages(False).endswith("pm list packages")


def test_input_action_variants():
    assert mobile.input_action("tap", "200 400").endswith("input tap 200 400")
    assert "input text" in mobile.input_action("text", "hello")
    assert "input keyevent" in mobile.input_action("key", "KEYCODE_HOME")


def test_frida_run_uses_forwarded_host_and_timeout():
    cmd = mobile.frida_run_script("com.x.app", "/tmp/h.js", timeout=45)
    assert "timeout 45 frida -H 127.0.0.1:27042" in cmd
    assert "-f 'com.x.app'" in cmd
    assert "-l '/tmp/h.js'" in cmd
