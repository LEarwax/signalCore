import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.result import Result
from app.models.project import Project
from app.schemas.project import CreateProjectSchema, UpdateProjectSchema, ProjectSchema

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(self, engineer_id: uuid.UUID) -> Result[list[ProjectSchema]]:
        try:
            result = await self.db.execute(
                select(Project)
                .where(Project.engineer_id == engineer_id)
                .order_by(Project.created_at.desc())
            )
            projects = result.scalars().all()
            return Result.ok([ProjectSchema.model_validate(p) for p in projects])
        except Exception:
            logger.exception("Error listing projects for engineer %s", engineer_id)
            return Result.failure("Failed to list projects")

    async def get_project(self, project_id: uuid.UUID, engineer_id: uuid.UUID) -> Result[ProjectSchema]:
        try:
            result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if project is None:
                return Result.not_found(f"Project {project_id} not found")
            if project.engineer_id != engineer_id:
                return Result.forbidden()
            return Result.ok(ProjectSchema.model_validate(project))
        except Exception:
            logger.exception("Error getting project %s", project_id)
            return Result.failure("Failed to get project")

    async def create_project(self, engineer_id: uuid.UUID, dto: CreateProjectSchema) -> Result[ProjectSchema]:
        try:
            project = Project(
                engineer_id=engineer_id,
                name=dto.name,
                address=dto.address,
                notes=dto.notes,
            )
            self.db.add(project)
            await self.db.commit()
            await self.db.refresh(project)
            logger.info("Created project %s for engineer %s", project.id, engineer_id)
            return Result.ok(ProjectSchema.model_validate(project))
        except Exception:
            logger.exception("Error creating project for engineer %s", engineer_id)
            await self.db.rollback()
            return Result.failure("Failed to create project")

    async def update_project(
        self, project_id: uuid.UUID, engineer_id: uuid.UUID, dto: UpdateProjectSchema
    ) -> Result[ProjectSchema]:
        try:
            result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if project is None:
                return Result.not_found(f"Project {project_id} not found")
            if project.engineer_id != engineer_id:
                return Result.forbidden()

            if dto.name is not None:
                project.name = dto.name
            if dto.address is not None:
                project.address = dto.address
            if dto.notes is not None:
                project.notes = dto.notes

            await self.db.commit()
            await self.db.refresh(project)
            return Result.ok(ProjectSchema.model_validate(project))
        except Exception:
            logger.exception("Error updating project %s", project_id)
            await self.db.rollback()
            return Result.failure("Failed to update project")

    async def delete_project(self, project_id: uuid.UUID, engineer_id: uuid.UUID) -> Result[None]:
        try:
            result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if project is None:
                return Result.not_found(f"Project {project_id} not found")
            if project.engineer_id != engineer_id:
                return Result.forbidden()

            await self.db.delete(project)
            await self.db.commit()
            logger.info("Deleted project %s", project_id)
            return Result.ok(None)
        except Exception:
            logger.exception("Error deleting project %s", project_id)
            await self.db.rollback()
            return Result.failure("Failed to delete project")
