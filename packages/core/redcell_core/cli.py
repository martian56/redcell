"""REDCELL admin CLI:  uv run rc <command>"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import typer

from . import seed

app = typer.Typer(help="REDCELL admin CLI", no_args_is_help=True)
db_app = typer.Typer(help="Database migrations")
app.add_typer(db_app, name="db")

_CORE_DIR = Path(__file__).resolve().parent.parent  # packages/core


@app.command("seed")
def seed_cmd(
    demo: bool = typer.Option(False, help="Also insert demo data."),
    unseed: bool = typer.Option(False, help="Wipe all app data (Postgres + MinIO)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the unseed guard."),
) -> None:
    async def run() -> None:
        if unseed:
            await seed.unseed(force=yes)
            typer.echo("unseeded: Postgres app data and MinIO buckets emptied")
            return
        await seed.bootstrap()
        typer.echo("bootstrapped: buckets, providers, admin, default settings")
        if demo:
            await seed.demo()
            typer.echo("demo data inserted")

    asyncio.run(run())


@db_app.command("upgrade")
def db_upgrade() -> None:
    subprocess.run(["alembic", "upgrade", "head"], cwd=str(_CORE_DIR), check=True)


@db_app.command("downgrade")
def db_downgrade(rev: str = typer.Argument("-1")) -> None:
    subprocess.run(["alembic", "downgrade", rev], cwd=str(_CORE_DIR), check=True)
