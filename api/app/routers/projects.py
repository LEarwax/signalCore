import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_engineer
from app.core.database import get_db
from app.models.engineer import Engineer
from app.schemas.project import CreateProjectSchema, UpdateProjectSchema, ProjectSchema
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.get("/", response_model=list[ProjectSchema])
async def list_projects(
    engineer: Engineer = Depends(get_current_engineer),
    service: ProjectService = Depends(get_project_service),
):
    result = await service.list_projects(engineer.id)
    return result.to_response()


@router.post("/", response_model=ProjectSchema, status_code=201)
async def create_project(
    dto: CreateProjectSchema,
    engineer: Engineer = Depends(get_current_engineer),
    service: ProjectService = Depends(get_project_service),
):
    result = await service.create_project(engineer.id, dto)
    return result.to_response(status_code=201)


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: uuid.UUID,
    engineer: Engineer = Depends(get_current_engineer),
    service: ProjectService = Depends(get_project_service),
):
    result = await service.get_project(project_id, engineer.id)
    return result.to_response()


@router.patch("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: uuid.UUID,
    dto: UpdateProjectSchema,
    engineer: Engineer = Depends(get_current_engineer),
    service: ProjectService = Depends(get_project_service),
):
    result = await service.update_project(project_id, engineer.id, dto)
    return result.to_response()


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    engineer: Engineer = Depends(get_current_engineer),
    service: ProjectService = Depends(get_project_service),
):
    result = await service.delete_project(project_id, engineer.id)
    result.to_response()
