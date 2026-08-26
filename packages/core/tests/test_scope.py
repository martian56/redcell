from redcell_core.engine.scope import in_scope, is_destructive, target_host


def test_target_host_forms():
    assert target_host("https://app.example.com/path?q=1") == "app.example.com"
    assert target_host("app.example.com:8080") == "app.example.com"
    assert target_host("http://10.1.2.3:80") == "10.1.2.3"
    assert target_host("EXAMPLE.com.") == "example.com"


def test_empty_scope_is_unrestricted():
    assert in_scope("anything.com", []) is True
    assert in_scope("10.0.0.1", None) is True


def test_exact_and_subdomain():
    scope = ["example.com"]
    assert in_scope("example.com", scope) is True
    assert in_scope("https://api.example.com", scope) is True
    assert in_scope("evil.com", scope) is False
    assert in_scope("notexample.com", scope) is False


def test_wildcard():
    scope = ["*.example.com"]
    assert in_scope("api.example.com", scope) is True
    assert in_scope("example.com", scope) is True
    assert in_scope("api.other.com", scope) is False


def test_cidr():
    scope = ["10.0.0.0/16"]
    assert in_scope("10.0.5.9", scope) is True
    assert in_scope("http://10.0.1.1:8080", scope) is True
    assert in_scope("10.1.0.1", scope) is False
    assert in_scope("example.com", scope) is False


def test_out_of_scope_when_unparseable():
    assert in_scope("", ["example.com"]) is False


def test_destructive_matches():
    assert is_destructive("rm -rf /")
    assert is_destructive("rm -rf /*")
    assert is_destructive("sudo rm -fr /etc")
    assert is_destructive("mkfs.ext4 /dev/sda1")
    assert is_destructive("dd if=/dev/zero of=/dev/sda")
    assert is_destructive(":(){ :|:& };:")
    assert is_destructive("shutdown -h now")


def test_destructive_allows_normal_commands():
    assert not is_destructive("nmap -sV 10.0.0.1")
    assert not is_destructive("rm -rf /tmp/scan-output")
    assert not is_destructive("curl -s https://target/api")
    assert not is_destructive("cat /etc/passwd")
