from types import SimpleNamespace

from redcell_core.engine.runner import summarize_progress


def _f(title, severity, location="", status="candidate"):
    return SimpleNamespace(title=title, severity=severity, location=location, status=status)


def _h(host, ip=None, ports=None, tech=None):
    return SimpleNamespace(host=host, ip=ip, ports=ports or [], tech=tech or [])


def _l(kind, label):
    return SimpleNamespace(kind=kind, label=label)


def test_summary_none_when_empty():
    assert summarize_progress([], [], []) is None


def test_summary_ignores_dismissed_findings():
    assert summarize_progress([_f("SQLi", "critical", "/x", "dismissed")], [], []) is None


def test_summary_includes_findings_hosts_and_loot():
    text = summarize_progress(
        [_f("SQL injection", "critical", "/api/v2/search", "verified")],
        [_h("app.acme.io", "1.2.3.4", [443, {"port": 8443}], ["nginx"])],
        [_l("credential", "admin@acme")],
    )
    assert text is not None
    assert "SQL injection" in text
    assert "/api/v2/search" in text
    assert "critical" in text
    assert "app.acme.io" in text and "1.2.3.4" in text
    assert "443" in text and "8443" in text and "nginx" in text
    assert "credential: admin@acme" in text
