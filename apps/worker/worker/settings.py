"""arq worker entrypoint:  uv run arq worker.settings.WorkerSettings"""

from __future__ import annotations

from redcell_core.bus import bus
from redcell_core.config import settings
from redcell_core.queue import redis_settings
from redcell_core.storage import storage

from .tasks import generate_report, operate_shell, resume_running, run_engagement


async def on_startup(ctx) -> None:
    await bus.connect()
    await storage.ensure_buckets()
    await ctx["redis"].enqueue_job("resume_running")


async def on_shutdown(ctx) -> None:
    await bus.close()


class WorkerSettings:
    functions = [run_engagement, resume_running, operate_shell, generate_report]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = redis_settings()
    # Concurrently active runs are long-lived asyncio tasks in one loop; keep the
    # ceiling modest and tunable (REDCELL_WORKER_MAX_JOBS) rather than arq's 10 or
    # a fixed 50.
    max_jobs = settings.worker_max_jobs
    # Run jobs stream far longer than arq's 300s default; a day is a ceiling,
    # not an expected duration (restart re-enqueues via resume_running).
    job_timeout = 60 * 60 * 24
    keep_result = 5

