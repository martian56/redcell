"""Unit tests for BrowserManager: command construction, lazy start, operator
control gating, and tolerant JSON parsing. No real browser or container."""

from redcell_core.engine.browser import BrowserManager


class _Res:
    def __init__(self, output: str) -> None:
        self.output = output


class FakeBackend:
    def __init__(self, output: str = '{"ok": true}') -> None:
        self.commands: list[str] = []
        self.output = output

    async def run(self, cmd: str, **kw):
        self.commands.append(cmd)
        return _Res(self.output)


def _mgr(output='{"ok": true}'):
    be = FakeBackend(output)
    return BrowserManager(be, "ses-1"), be


async def test_ensure_started_runs_once():
    m, be = _mgr()
    await m.ensure_started()
    await m.ensure_started()
    assert be.commands.count("rc-browserd start") == 1


async def test_open_runs_rc_browser_and_parses_json():
    m, be = _mgr('{"ok": true, "url": "https://x", "title": "X"}')
    out = await m.open("https://x")
    assert out["url"] == "https://x"
    assert any(c.startswith("rc-browser open ") for c in be.commands)


async def test_operator_control_blocks_agent_actions():
    m, be = _mgr()
    m.set_owner("operator")
    out = await m.open("https://x")
    assert out == {"status": "operator_has_control"}
    assert not any(c.startswith("rc-browser") for c in be.commands)


async def test_releasing_control_lets_agent_act_again():
    m, be = _mgr()
    m.set_owner("operator")
    await m.open("https://x")
    m.set_owner("agent")
    await m.open("https://y")
    assert any("rc-browser open" in c for c in be.commands)


async def test_type_with_submit_includes_flag_and_quotes_spaces():
    m, be = _mgr()
    await m.type("#q", "a b", submit=True)
    cmd = next(c for c in be.commands if c.startswith("rc-browser type"))
    assert "--submit" in cmd
    assert "'a b'" in cmd


async def test_stop_runs_rc_browserd_stop():
    m, be = _mgr()
    await m.ensure_started()
    await m.stop()
    assert "rc-browserd stop" in be.commands


async def test_parse_tolerates_log_noise_before_json():
    m, be = _mgr('boot log line\nanother\n{"ok": true, "url": "u"}')
    out = await m.read()
    assert out["url"] == "u"
