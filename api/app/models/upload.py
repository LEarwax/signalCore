import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PDFUpload(Base):
    __tablename__ = "pdf_uploads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    engineer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("engineers.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(500))
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="ready")  # ready | failed
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    # Relationships
    sheets: Mapped[list["Sheet"]] = relationship(
        back_populates="upload",
        cascade="all, delete-orphan",
        order_by="Sheet.page_number",
    )


class Sheet(Base):
    __tablename__ = "sheets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    upload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pdf_uploads.id", ondelete="CASCADE"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    sheet_type: Mapped[str] = mapped_column(String(50), default="other")
    # sheet_type values: floor_plan | elevation | section | detail | other
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    # Relationships
    upload: Mapped["PDFUpload"] = relationship(back_populates="sheets")
