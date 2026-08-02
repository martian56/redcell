"""Worker tasks."""

from __future__ import annotations

from redcell_core.bus import bus
from redcell_core.config import settings
from redcell_core.db import session_scope
from redcell_core.engine.simulator import Simulator
from redcell_core.repositories import runs as runs_repo


async def run_engagement(ctx, run_id: str) -> None:
    async with session_scope() as s:
        await runs_repo.set_status(s, run_id, "running")
    if settings.run_mode == "live":
        from redcell_core.engine.runner import LiveRunner  # lazy: pulls litellm/langgraph
        await LiveRunner(bus, run_id).run()
    else:
        await Simulator(bus).run_one(run_id)


async def resume_running(ctx) -> None:
    async with session_scope() as s:
        running = await runs_repo.list_by_status(s, "running")
    for r in running:
        # No fixed job id: a retained id would block re-enqueue after a restart.
        await ctx["redis"].enqueue_job("run_engagement", r.id)


async def operate_shell(ctx, shell_id: str) -> None:
    """Drive an operator terminal: run typed commands in the exec backend."""
    from redcell_core.engine.opshell import run_operator_shell
    await run_operator_shell(bus, shell_id)


async def generate_report(ctx, report_id: str) -> None:
    """Generate a session report (PDF/JSON/SARIF) in the background."""
    from redcell_core.engine.reporting import generate_report as gen
    await gen(report_id)
