import pytest
from redcell_core.engine.execution import SimBackend
from redcell_core.engine.tools import orchestrator_system


def test_context_sections_render():
    p = orchestrator_system("Goal", ["*.t"], ["t"], "no dos",
                            brief="focus on prompt injection, skip recon",
                            instruction="this run: try IDOR instead",
                            files=["challenge.bin", "capture.pcap"])
    assert "Engagement brief: focus on prompt injection, skip recon" in p
    assert "This run's instructions: this run: try IDOR instead" in p
    assert "follow this run's instructions" in p
    assert "/root/assessment/: challenge.bin, capture.pcap" in p


def test_empty_sections_omitted():
    p = orchestrator_system("Goal", [], [], None)
    assert "Engagement brief:" not in p
    assert "This run's instructions:" not in p
    assert "/root/assessment/" not in p


@pytest.mark.asyncio
async def test_sim_backend_stage_file_is_noop():
    await SimBackend().stage_file("/root/assessment/x.bin", b"\x00\x01binary")
