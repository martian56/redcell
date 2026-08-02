"""arq job queue helpers, shared by the API (enqueue side) and the worker."""

from __future__ import annotations

from arq import create_pool
from arq.connections import RedisSettings

from .config import settings


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


async def enqueue(func: str, *args, job_id: str | None = None) -> None:
    pool = await create_pool(redis_settings())
    try:
        await pool.enqueue_job(func, *args, _job_id=job_id)
    finally:
        await pool.aclose()
