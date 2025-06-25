"""merge user profile fields and other head

Revision ID: a9a81802adb8
Revises: 067220be1dc6, 2add_user_profile_fields
Create Date: 2025-06-12 15:51:38.556484

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9a81802adb8'
down_revision: Union[str, None] = ('067220be1dc6', '2add_user_profile_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
