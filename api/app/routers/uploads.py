"""
routers/uploads.py — PDF upload and file-serving endpoints.
"""
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_engineer
from app.core.database import get_db
from app.models.engineer import Engineer
from app.models.project import Project
from app.schemas.upload import SheetOut, UploadOut
from app.services.pdf_service import process_upload
from app.services.storage_service import storage, LOCAL_DIR

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_MB = 500


@router.post("/api/projects/{project_id}/upload", response_model=UploadOut)
async def upload_plan_set(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    engineer: Engineer = Depends(get_current_engineer),
):
    # Validate project ownership
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid project ID")

    result = await db.execute(
        select(Project).where(Project.id == pid, Project.engineer_id == engineer.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check content type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        # Be lenient — browser FormData sometimes sends wrong content-type
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=422, detail="Only PDF files are accepted")

    # Read file (with size guard)
    file_bytes = await file.read()
    size_mb = len(file_bytes) / 1_000_000
    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.0f} MB). Maximum is {MAX_UPLOAD_MB} MB.",
        )

    logger.info("Processing upload: %s (%.1f MB)", file.filename, size_mb)

    upload = await process_upload(
        session=db,
        project_id=project.id,
        engineer_id=engineer.id,
        filename=file.filename or "upload.pdf",
        file_bytes=file_bytes,
    )

    return UploadOut(
        upload_id=str(upload.id),
        filename=upload.filename,
        page_count=upload.page_count,
        sheets=[
            SheetOut(
                id=str(s.id),
                page_number=s.page_number,
                label=s.label,
                type=s.sheet_type,
                thumbnail_url=s.thumbnail_url,
            )
            for s in upload.sheets
        ],
    )


@router.get("/api/files/{file_path:path}")
async def serve_local_file(file_path: str):
    """
    Serve files from local storage (dev only — in prod files are served from S3).
    """
    path = LOCAL_DIR / file_path
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    # Basic path traversal guard
    try:
        path.relative_to(LOCAL_DIR)
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden")
    return FileResponse(str(path))
