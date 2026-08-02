from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AppSettings
from ..schemas import Settings as SettingsSchema


async def get(s: AsyncSession) -> AppSettings:
    row = await s.get(AppSettings, "global")
    if row is None:
        defaults = SettingsSchema()
        row = AppSettings(
            id="global",
            llm=defaults.llm.model_dump(),
            execution=defaults.execution.model_dump(),
            scope=defaults.scope.model_dump(),
            proxy=defaults.proxy.model_dump(),
            report=defaults.report.model_dump(),
        )
        s.add(row)
        await s.flush()
    return row


async def save(s: AsyncSession, data: dict) -> AppSettings:
    row = await get(s)
    row.llm = data.get("llm", row.llm)
    row.execution = data.get("execution", row.execution)
    row.scope = data.get("scope", row.scope)
    row.proxy = data.get("proxy", row.proxy)
    row.report = data.get("report", row.report)
    await s.flush()
    return row
