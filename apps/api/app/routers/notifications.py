"""In-app notifications feed."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from redcell_core.repositories import notifications as notifications_repo
from redcell_core.schemas import Notification, NotificationFeed
from redcell_core.security import current_user
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import db

router = APIRouter(tags=["notifications"], dependencies=[Depends(current_user)])


async def _feed(s: AsyncSession) -> NotificationFeed:
    items = await notifications_repo.list_recent(s)
    unread = await notifications_repo.unread_count(s)
    return NotificationFeed(items=[Notification.model_validate(n) for n in items], unread=unread)


@router.get("/notifications", response_model=NotificationFeed)
async def list_notifications(s: AsyncSession = Depends(db)) -> NotificationFeed:
    return await _feed(s)


@router.post("/notifications/{notification_id}/read", response_model=NotificationFeed)
async def read_notification(notification_id: str, s: AsyncSession = Depends(db)) -> NotificationFeed:
    await notifications_repo.mark_read(s, notification_id)
    return await _feed(s)


@router.post("/notifications/read-all", response_model=NotificationFeed)
async def read_all_notifications(s: AsyncSession = Depends(db)) -> NotificationFeed:
    await notifications_repo.mark_all_read(s)
    return await _feed(s)
