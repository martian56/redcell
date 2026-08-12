"""Reporting endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from redcell_core import queue
from redcell_core.repositories import reports as reports_repo
from redcell_core.schemas import CreateReportInput, Report
from redcell_core.security import current_user
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import db

router = APIRouter(tags=["reports"], dependencies=[Depends(current_user)])


@router.get("/sessions/{sid}/reports", response_model=list[Report])
async def list_reports(sid: str, s: AsyncSession = Depends(db)) -> list[Report]:
    return [Report.model_validate(r) for r in await reports_repo.list_for_session(s, sid)]


@router.post("/sessions/{sid}/reports", response_model=Report)
async def create_report(sid: str, body: CreateReportInput, s: AsyncSession = Depends(db)) -> Report:
    row = await reports_repo.create(s, sid, body.title, body.formats)
    schema = Report.model_validate(row)
    await s.commit()  # commit before enqueue; worker reads the report
    await queue.enqueue("generate_report", row.id)
    return schema


@router.get("/reports/{rid}", response_model=Report)
async def get_report(rid: str, s: AsyncSession = Depends(db)) -> Report:
    row = await reports_repo.get(s, rid)
    if row is None:
        raise HTTPException(404, "report not found")
    return Report.model_validate(row)


@router.delete("/reports/{rid}", status_code=204)
async def delete_report(rid: str, s: AsyncSession = Depends(db)) -> None:
    if not await reports_repo.delete(s, rid):
        raise HTTPException(404, "report not found")
