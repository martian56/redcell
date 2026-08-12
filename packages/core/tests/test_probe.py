"""Unit tests for the server-probe output parser. probe_server/probe_proxy need
a live host, but _parse (turning the prefixed probe lines into facts) is pure."""

from redcell_core.probe import _parse


def test_parses_all_facts():
    out = _parse("H:web-01\nU:Linux 6.1.0\nC:4\nM:8192\nI:10.0.0.5 192.168.1.9")
    assert out["hostname"] == "web-01"
    assert out["os"] == "Linux 6.1.0"
    assert out["cpu"] == 4
    assert out["ram_gb"] == 8  # 8192 MB rounds to 8 GB
    assert out["ip"] == "10.0.0.5"  # first address only


def test_ignores_blank_and_non_numeric_values():
    out = _parse("H:\nC:notanumber\nM:\nI:")
    assert out.get("hostname") is None
    assert "cpu" not in out  # non-numeric CPU is dropped
    assert "ram_gb" not in out
    assert out.get("ip") is None


def test_ram_rounds_and_floors_at_one_gb():
    assert _parse("M:1500")["ram_gb"] == 1   # round(1.46) -> 1
    assert _parse("M:100")["ram_gb"] == 1    # max(1, round(0.1)) -> 1
    assert _parse("M:2600")["ram_gb"] == 3   # round(2.54) -> 3


def test_empty_output_yields_no_facts():
    assert _parse("") == {}
