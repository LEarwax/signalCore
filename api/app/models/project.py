import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    engineer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("engineers.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"), onupdate=datetime.utcnow)

    # Relationships
    engineer: Mapped["Engineer"] = relationship(back_populates="projects")
    packets: Mapped[list["SubmittalPacket"]] = relationship(back_populates="project", cascade="all, delete-orphan")
