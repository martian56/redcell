"""Test isolation for the whole suite.

The suite runs against REAL infrastructure (Postgres, Redis, MinIO) rather than
mocks. Those must NEVER be the same instances the dev app uses: some tests are
destructive (test_seed calls seed.unseed(), which DELETEs every row and empties
every bucket). To keep the dev data safe, this conftest rebinds all shared infra
to throwaway, test-only resources *before* the app's db/storage singletons touch
them:

  - Postgres : a separate `<db>_test` database (created here if missing)
  - Redis    : logical DB index 15 (the app uses 0)
  - MinIO    : `test-*` buckets (the app uses uploads/loot/reports/public)
  - Checkpts : disabled (SQLite checkpoint store off during tests)

The redirection happens at import time, ahead of importing redcell_core.db, so
the async engine binds to the test database from the start.
"""

import asyncio

import pytest

# 1) Redirect settings to test-only infra BEFORE anything binds to them. ----------
from redcell_core.config import settings  # noqa: E402
from sqlalchemy.engine import make_url


def _test_db_url(url: str) -> str:
    u = make_url(url)
    name = u.database or "redcell"
    if not name.endswith("_test"):
        u = u.set(database=f"{name}_test")
    return u.render_as_string(hide_password=False)


settings.database_url = _test_db_url(settings.database_url)
_redis_base = settings.redis_url.rsplit("/", 1)[0] if "/" in settings.redis_url.split("//", 1)[-1] else settings.redis_url
settings.redis_url = f"{_redis_base}/15"
settings.bucket_uploads = "test-uploads"
settings.bucket_loot = "test-loot"
settings.bucket_reports = "test-reports"
settings.bucket_public = "test-public"
settings.checkpoint_db = ""
# Pin tests to sim so the suite never shells out to real Docker, independent of
# the app's default run mode.
settings.run_mode = "sim"
# The suite logs in many times from one client; rate limiting would cause spurious
# 429s. The dedicated rate-limit test re-enables it explicitly.
settings.rate_limit_enabled = False


# 2) Create the test database + schema once, on a throwaway loop. -----------------
async def _prepare_test_database() -> None:
    import asyncpg

    u = make_url(settings.database_url)
    admin = await asyncpg.connect(host=u.host, port=u.port, user=u.username,
                                  password=u.password, database="postgres")
    try:
        exists = await admin.fetchval("select 1 from pg_database where datname=$1", u.database)
        if not exists:
            await admin.execute(f'CREATE DATABASE "{u.database}"')
    finally:
        await admin.close()

    # Import db (binds engine to the test URL) and models, then (re)build the
    # schema. Drop first so the throwaway test schema always matches the current
    # models even after a column is added (create_all alone won't alter tables).
    from redcell_core.db import engine
    from redcell_core.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def pytest_configure(config: pytest.Config) -> None:
    # Belt-and-suspenders: abort the whole run if the redirect ever failed to
    # produce a *_test database, so a destructive test can never hit real data.
    assert make_url(settings.database_url).database.endswith("_test"), \
        "test database is not isolated; refusing to run"
    asyncio.run(_prepare_test_database())


@pytest.fixture(autouse=True)
async def _dispose_engine_between_tests():
    """pytest-asyncio gives each test its own event loop; dispose the async
    engine's pool at the end of each test so no connection is closed on a loop
    that has already shut down."""
    yield
    try:
        from redcell_core.db import engine
        await engine.dispose()
    except Exception:
        pass
