"""File storage."""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from redcell_core.config import settings
from redcell_core.repositories import files as files_repo
from redcell_core.repositories import ids
from redcell_core.schemas import FileMeta
from redcell_core.security import current_user
from redcell_core.storage import safe_filename, storage
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import db

router = APIRouter(tags=["files"], dependencies=[Depends(current_user)])


@router.post("/sessions/{sid}/files", response_model=FileMeta)
async def upload(sid: str, file: UploadFile, kind: str = Form("upload"),
                 s: AsyncSession = Depends(db)) -> FileMeta:
    if not safe_filename(file.filename):
        raise HTTPException(400, "invalid filename")
    data = await file.read()
    key = f"{sid}/{ids.new_id('f')}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"
    await storage.put(settings.bucket_uploads, key, data, content_type)
    row = await files_repo.create(s, {
        "session_id": sid, "bucket": settings.bucket_uploads, "object_key": key,
        "filename": file.filename, "kind": kind or "upload", "content_type": content_type,
        "size": len(data), "visibility": "private", "source": "operator",
    })
    return FileMeta.model_validate(row)


@router.get("/sessions/{sid}/files", response_model=list[FileMeta])
async def list_files(sid: str, s: AsyncSession = Depends(db)) -> list[FileMeta]:
    return [FileMeta.model_validate(f) for f in await files_repo.list_for_session(s, sid)]


@router.get("/files/{fid}")
async def download(fid: str, s: AsyncSession = Depends(db)):
    row = await files_repo.get(s, fid)
    if row is None:
        raise HTTPException(404, "file not found")
    raw = row.filename or fid
    ascii_name = raw.encode("ascii", "ignore").decode().replace('"', "").replace("\r", "").replace("\n", "") or "download"
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(raw)}"
    return StreamingResponse(
        storage.stream_get(row.bucket, row.object_key),
        media_type=row.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": disposition,
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )


@router.delete("/files/{fid}", status_code=204)
async def remove(fid: str, s: AsyncSession = Depends(db)) -> None:
    row = await files_repo.get(s, fid)
    if row is None:
        raise HTTPException(404, "file not found")
    await storage.delete(row.bucket, row.object_key)
    await files_repo.delete(s, fid)
