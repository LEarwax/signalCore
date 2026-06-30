import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class CreateProjectSchema(BaseModel):
    name: str
    address: str | None = None
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UpdateProjectSchema(BaseModel):
    name: str | None = None
    address: str | None = None
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip() if v else v


class ProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    engineer_id: uuid.UUID
    name: str
    address: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
