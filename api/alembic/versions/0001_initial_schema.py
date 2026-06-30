"""Initial schema: engineers, projects, submittal_packets, shareable_links

Revision ID: 0001
Revises:
Create Date: 2026-06-30
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "engineers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("auth0_sub", sa.String(200), nullable=False, unique=True),
        sa.Column("email", sa.String(300), nullable=False, server_default=""),
        sa.Column("name", sa.String(200), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("engineer_id", UUID(as_uuid=True), sa.ForeignKey("engineers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(500)),
        sa.Column("notes", sa.String(2000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_projects_engineer_id", "projects", ["engineer_id"])

    op.create_table(
        "submittal_packets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ahj_name", sa.String(200)),
        sa.Column("ahj_abbreviation", sa.String(50)),
        sa.Column("freq_bands", JSONB),
        sa.Column("engine_type", sa.String(50)),
        sa.Column("floor_count", sa.Integer),
        sa.Column("occupancy_type", sa.String(50)),
        sa.Column("antenna_count", sa.Integer),
        sa.Column("coverage_pct", sa.Float),
        sa.Column("packet_s3_key", sa.String(500)),
        sa.Column("overlay_s3_key", sa.String(500)),
        sa.Column("equipment_s3_key", sa.String(500)),
        sa.Column("riser_s3_key", sa.String(500)),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_packets_project_id", "submittal_packets", ["project_id"])

    op.create_table(
        "shareable_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("packet_id", UUID(as_uuid=True), sa.ForeignKey("submittal_packets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(100), nullable=False, unique=True),
        sa.Column("snapshot_data", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_shareable_links_token", "shareable_links", ["token"])


def downgrade() -> None:
    op.drop_table("shareable_links")
    op.drop_table("submittal_packets")
    op.drop_table("projects")
    op.drop_table("engineers")
