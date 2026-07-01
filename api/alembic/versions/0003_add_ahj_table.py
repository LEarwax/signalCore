"""Add ahj_records table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ahj_records',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),

        # Identity
        sa.Column('name',         sa.String(300), nullable=False),
        sa.Column('abbreviation', sa.String(30),  nullable=False),
        sa.Column('jurisdiction', sa.String(200), nullable=False),
        sa.Column('state',        sa.String(2),   nullable=False),
        sa.Column('website',      sa.String(500), server_default='', nullable=False),

        # RF Requirements
        sa.Column('min_signal_dbm',     sa.Numeric(6, 1), nullable=False, server_default='-95.0'),
        sa.Column('design_target_dbm',  sa.Numeric(6, 1), nullable=False, server_default='-85.0'),
        sa.Column('coverage_pct',       sa.Numeric(5, 1), nullable=False, server_default='95.0'),
        sa.Column('critical_areas_pct', sa.Numeric(5, 1), nullable=False, server_default='99.0'),

        # Frequency bands
        sa.Column('freq_bands', JSONB, nullable=False, server_default='["700MHz"]'),

        # Battery
        sa.Column('battery_hours', sa.Numeric(5, 1), nullable=False, server_default='24.0'),

        # High-rise
        sa.Column('highrise_threshold_ft', sa.Numeric(6, 1), nullable=False, server_default='55.0'),
        sa.Column('highrise_coverage_pct', sa.Numeric(5, 1), nullable=False, server_default='99.0'),

        # Submittal flags
        sa.Column('requires_preliminary',       sa.Boolean, nullable=False, server_default='true'),
        sa.Column('requires_construction_docs', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('requires_donor_path_study',  sa.Boolean, nullable=False, server_default='false'),
        sa.Column('requires_third_party_test',  sa.Boolean, nullable=False, server_default='false'),
        sa.Column('requires_facp_integration',  sa.Boolean, nullable=False, server_default='true'),
        sa.Column('requires_signed_plans',      sa.Boolean, nullable=False, server_default='true'),

        # Lists
        sa.Column('special_requirements', JSONB, nullable=False, server_default='[]'),
        sa.Column('codes',                JSONB, nullable=False, server_default='[]'),

        # Metadata
        sa.Column('confidence',  sa.String(20),  nullable=False, server_default='exact'),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
    )

    # Index for fast city lookups
    op.create_index('ix_ahj_records_jurisdiction_upper',
                    'ahj_records',
                    [sa.text('upper(jurisdiction)')],
                    unique=False)
    op.create_index('ix_ahj_records_state', 'ahj_records', ['state'])


def downgrade() -> None:
    op.drop_index('ix_ahj_records_state', table_name='ahj_records')
    op.drop_index('ix_ahj_records_jurisdiction_upper', table_name='ahj_records')
    op.drop_table('ahj_records')
