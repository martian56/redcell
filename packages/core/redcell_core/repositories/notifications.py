from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Notification
from ..schemas import NotificationSettings
from . import ids
from . import settings as settings_repo

_KIND_PREF = {
    "run_completed": "run_finished",
    "run_failed": "run_failed",
    "finding": "critical_findings",
    "report_ready": "report_ready",
    "infra": "infra",
}


async def list_recent(s: AsyncSession, limit: int = 50) -> list[Notification]:
    rows = await s.execute(select(Notification).order_by(Notification.created_at.desc()).limit(limit))
    return list(rows.scalars().all())


async def unread_count(s: AsyncSession) -> int:
    result = await s.execute(
        select(func.count()).select_from(Notification).where(Notification.read.is_(False))
    )
    return int(result.scalar_one())


async def mark_read(s: AsyncSession, notification_id: str) -> None:
    await s.execute(update(Notification).where(Notification.id == notification_id).values(read=True))
    await s.flush()


async def mark_all_read(s: AsyncSession) -> None:
    await s.execute(update(Notification).where(Notification.read.is_(False)).values(read=True))
    await s.flush()


async def create(
    s: AsyncSession, *, kind: str, title: str, body: str = "", link: str | None = None
) -> Notification:
    row = Notification(
        id=ids.new_id("ntf"),
        kind=kind,
        title=title,
        body=body,
        link=link,
        read=False,
        created_at=ids.now_iso(),
    )
    s.add(row)
    await s.flush()
    return row


async def notify(
    s: AsyncSession, *, kind: str, title: str, body: str = "", link: str | None = None
) -> Notification | None:
    """Record a notification only when its category is enabled in settings."""
    pref_key = _KIND_PREF.get(kind)
    cfg = await settings_repo.get(s)
    prefs = {**NotificationSettings().model_dump(), **(cfg.notifications or {})}
    if pref_key is not None and not prefs.get(pref_key, False):
        return None
    return await create(s, kind=kind, title=title, body=body, link=link)
