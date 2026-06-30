import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SubmittalPacket(Base):
    __tablename__ = "submittal_packets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # AHJ info (captured at generation time)
    ahj_name: Mapped[str | None] = mapped_column(String(200))
    ahj_abbreviation: Mapped[str | None] = mapped_column(String(50))
    freq_bands: Mapped[list | None] = mapped_column(JSON)  # e.g. ["700MHz", "800MHz"]

    # Building classification results
    engine_type: Mapped[str | None] = mapped_column(String(50))  # single_floor, parking, etc.
    floor_count: Mapped[int | None]
    occupancy_type: Mapped[str | None] = mapped_column(String(50))
    antenna_count: Mapped[int | None]
    coverage_pct: Mapped[float | None]

    # S3 keys for generated files
    packet_s3_key: Mapped[str | None] = mapped_column(String(500))  # ERRCS_Submittal_Packet.pdf
    overlay_s3_key: Mapped[str | None] = mapped_column(String(500))  # floor plan overlay
    equipment_s3_key: Mapped[str | None] = mapped_column(String(500))
    riser_s3_key: Mapped[str | None] = mapped_column(String(500))

    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | processing | complete | failed
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"), onupdate=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="packets")
    shareable_links: Mapped[list["ShareableLink"]] = relationship(back_populates="packet", cascade="all, delete-orphan")


class ShareableLink(Base):
    __tablename__ = "shareable_links"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    packet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submittal_packets.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    snapshot_data: Mapped[dict | None] = mapped_column(JSON)  # point-in-time snapshot
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    # Relationships
    packet: Mapped["SubmittalPacket"] = relationship(back_populates="shareable_links")
