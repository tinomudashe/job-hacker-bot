"""merge_migration_heads

Revision ID: 2213ff448010
Revises: 5e8b6b3e3e3e, a1602375de57
Create Date: 2025-08-21 00:57:16.030824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2213ff448010'
down_revision: Union[str, None] = ('5e8b6b3e3e3e', 'a1602375de57')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
