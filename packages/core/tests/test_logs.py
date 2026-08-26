import logging

from redcell_core.logs import configure, get_logger


def test_get_logger_is_redcell_child():
    assert get_logger("engine.test").name == "redcell.engine.test"


def test_configure_is_idempotent():
    configure()
    n = len(logging.getLogger("redcell").handlers)
    configure()
    assert len(logging.getLogger("redcell").handlers) == n
