import uuid
from datetime import datetime
from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Engineer(Base):
    __tablename__ = "engineers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    auth0_sub: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"), onupdate=datetime.utcnow)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(back_populates="engineer", cascade="all, delete-orphan")
