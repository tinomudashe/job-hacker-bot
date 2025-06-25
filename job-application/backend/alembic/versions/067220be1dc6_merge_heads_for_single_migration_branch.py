"""merge heads for single migration branch

Revision ID: 067220be1dc6
Revises: 1add_success_to_applications, 56bf93be7291
Create Date: 2025-06-12 14:46:52.923175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '067220be1dc6'
down_revision: Union[str, None] = ('1add_success_to_applications', '56bf93be7291')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
