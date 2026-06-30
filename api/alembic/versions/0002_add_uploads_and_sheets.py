"""Add pdf_uploads and sheets tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pdf_uploads',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('engineer_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('s3_key', sa.String(500), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='ready'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engineer_id'], ['engineers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pdf_uploads_project_id', 'pdf_uploads', ['project_id'])

    op.create_table(
        'sheets',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('upload_id', sa.UUID(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(300), nullable=False),
        sa.Column('sheet_type', sa.String(50), nullable=False, server_default='other'),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['upload_id'], ['pdf_uploads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sheets_upload_id', 'sheets', ['upload_id'])
    op.create_index('ix_sheets_upload_page', 'sheets', ['upload_id', 'page_number'], unique=True)


def downgrade() -> None:
    op.drop_table('sheets')
    op.drop_table('pdf_uploads')
