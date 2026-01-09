"""add_ingestion_jobs

Revision ID: 8f1a3b5c7d9e
Revises: 700e7d016de9
Create Date: 2026-01-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8f1a3b5c7d9e'
down_revision: Union[str, Sequence[str], None] = '700e7d016de9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    
    # Create JobStatus enum (check if exists first)
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'jobstatus'"))
    if not result.fetchone():
        op.execute("CREATE TYPE jobstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled')")
    
    # Create ingestion_jobs table (check if exists first)
    result = conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'ingestion_jobs'"))
    if result.fetchone():
        return  # Table already exists, skip
    
    # Use postgresql.ENUM with create_type=False since we created it above
    jobstatus_enum = postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', name='jobstatus', create_type=False)
    
    op.create_table('ingestion_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subreddit', sa.String(length=100), nullable=False),
        sa.Column('status', jobstatus_enum, nullable=False),
        sa.Column('total_posts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_posts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_apps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_posts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('posts_data', sa.JSON(), nullable=True),
        sa.Column('created_app_ids', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('log_entries', sa.JSON(), nullable=True),
        sa.Column('cancel_requested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingestion_jobs_id'), 'ingestion_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_ingestion_jobs_status'), 'ingestion_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_ingestion_jobs_created_at'), 'ingestion_jobs', ['created_at'], unique=False)
    op.create_index(op.f('ix_ingestion_jobs_cancel_requested'), 'ingestion_jobs', ['cancel_requested'], unique=False)
    op.create_index(op.f('ix_ingestion_jobs_created_by_id'), 'ingestion_jobs', ['created_by_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_ingestion_jobs_created_by_id'), table_name='ingestion_jobs')
    op.drop_index(op.f('ix_ingestion_jobs_cancel_requested'), table_name='ingestion_jobs')
    op.drop_index(op.f('ix_ingestion_jobs_created_at'), table_name='ingestion_jobs')
    op.drop_index(op.f('ix_ingestion_jobs_status'), table_name='ingestion_jobs')
    op.drop_index(op.f('ix_ingestion_jobs_id'), table_name='ingestion_jobs')
    op.drop_table('ingestion_jobs')
    
    # Drop JobStatus enum
    op.execute('DROP TYPE IF EXISTS jobstatus')
