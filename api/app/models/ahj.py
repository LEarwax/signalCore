import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AHJRecord(Base):
    """
    Persisted AHJ (Authority Having Jurisdiction) profile.
    Seeded from the built-in AHJ_DB on first startup.
    Keyed by (jurisdiction, state) — one row per city/county entry.
    """
    __tablename__ = "ahj_records"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Identity
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(30), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    website: Mapped[str] = mapped_column(String(500), server_default="")

    # RF Requirements
    min_signal_dbm: Mapped[float] = mapped_column(Numeric(6, 1), nullable=False, server_default="-95.0")
    design_target_dbm: Mapped[float] = mapped_column(Numeric(6, 1), nullable=False, server_default="-85.0")
    coverage_pct: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False, server_default="95.0")
    critical_areas_pct: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False, server_default="99.0")

    # Frequency bands — list of strings e.g. ["700MHz", "800MHz"]
    freq_bands: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='["700MHz"]')

    # Battery
    battery_hours: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False, server_default="24.0")

    # High-rise thresholds
    highrise_threshold_ft: Mapped[float] = mapped_column(Numeric(6, 1), nullable=False, server_default="55.0")
    highrise_coverage_pct: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False, server_default="99.0")

    # Submittal requirement flags
    requires_preliminary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    requires_construction_docs: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    requires_donor_path_study: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    requires_third_party_test: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    requires_facp_integration: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    requires_signed_plans: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # Lists stored as JSONB
    special_requirements: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    codes: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    # Lookup metadata
    confidence: Mapped[str] = mapped_column(String(20), nullable=False, server_default="exact")

    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
