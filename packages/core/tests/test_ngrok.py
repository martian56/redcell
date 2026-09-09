import pytest
from redcell_core.engine.ngrok import NgrokError, NgrokManager


class _FakeStdout:
    def __init__(self, lines):
        self._lines = list(lines)

    async def readline(self):
        return self._lines.pop(0) if self._lines else b""


class _FakeProc:
    def __init__(self, lines):
        self.stdout = _FakeStdout(lines)


@pytest.mark.asyncio
async def test_parse_public_url_from_json_logs():
    mgr = NgrokManager()
    proc = _FakeProc([
        b'{"lvl":"info","msg":"starting agent"}\n',
        b'not json at all\n',
        b'{"msg":"started tunnel","url":"tcp://5.tcp.ngrok.io:12345"}\n',
    ])
    assert await mgr._read_public_url(proc) == "5.tcp.ngrok.io:12345"


@pytest.mark.asyncio
async def test_parse_raises_on_error_line():
    mgr = NgrokManager()
    proc = _FakeProc([b'{"err":"authentication failed","msg":"x"}\n'])
    with pytest.raises(NgrokError):
        await mgr._read_public_url(proc)


@pytest.mark.asyncio
async def test_parse_returns_none_on_eof():
    mgr = NgrokManager()
    proc = _FakeProc([b'{"msg":"no url here"}\n'])
    assert await mgr._read_public_url(proc) is None
