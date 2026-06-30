from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_engineer
from app.core.database import get_db
from app.models.engineer import Engineer

router = APIRouter(prefix="/api/packets", tags=["packets"])


@router.post("/", status_code=202)
async def generate_packet(
    project_id: str = Form(...),
    floor_plans: list[UploadFile] = File(..., description="One or more floor plan PDFs"),
    engineer: Engineer = Depends(get_current_engineer),
    db: AsyncSession = Depends(get_db),
):
    # TODO: upload PDFs to S3, dispatch ERRCS engine, return packet ID
    return {"message": "Packet generation not yet implemented", "project_id": project_id}


@router.get("/{packet_id}")
async def get_packet(
    packet_id: str,
    engineer: Engineer = Depends(get_current_engineer),
    db: AsyncSession = Depends(get_db),
):
    # TODO: implement
    return {}
