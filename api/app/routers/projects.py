from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_engineer
from app.core.database import get_db
from app.models.engineer import Engineer

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/")
async def list_projects(
    engineer: Engineer = Depends(get_current_engineer),
    db: AsyncSession = Depends(get_db),
):
    # TODO: implement ProjectService
    return []


@router.post("/", status_code=201)
async def create_project(
    engineer: Engineer = Depends(get_current_engineer),
    db: AsyncSession = Depends(get_db),
):
    # TODO: implement ProjectService
    return {}
