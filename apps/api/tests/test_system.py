"""Version comparison for the self-update endpoint."""

from app.routers.system import _norm, current_version, update_available


def test_norm_parses_versions():
    assert _norm("v1.2.3") == (1, 2, 3)
    assert _norm("0.3.2") == (0, 3, 2)


def test_update_available_when_newer():
    assert update_available("0.3.2", "v0.3.3") is True
    assert update_available("0.9.0", "v0.10.0") is True


def test_no_update_when_equal_or_older():
    assert update_available("0.3.2", "v0.3.2") is False
    assert update_available("0.3.3", "v0.3.2") is False


def test_no_update_when_dev_or_unknown():
    assert update_available("dev", "v1.0.0") is False
    assert update_available("0.3.2", None) is False


def test_current_version_is_a_string():
    assert isinstance(current_version(), str)
