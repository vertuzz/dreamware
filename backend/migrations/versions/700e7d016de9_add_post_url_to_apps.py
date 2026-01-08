"""add_post_url_to_apps

Revision ID: 700e7d016de9
Revises: 4a8b2c9d3e0f
Create Date: 2026-01-08 18:45:21.782032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '700e7d016de9'
down_revision: Union[str, Sequence[str], None] = '4a8b2c9d3e0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('apps', sa.Column('post_url', sa.String(length=512), nullable=True))
    op.create_index(op.f('ix_apps_post_url'), 'apps', ['post_url'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_apps_post_url'), table_name='apps')
    op.drop_column('apps', 'post_url')
