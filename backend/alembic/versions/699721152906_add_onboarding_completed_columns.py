"""add_onboarding_completed_columns

Revision ID: 699721152906
Revises: 0849b95dc29c
Create Date: 2025-08-24 08:20:43.984051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '699721152906'
down_revision: Union[str, None] = '0849b95dc29c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add onboarding_completed and onboarding_completed_at columns to users table."""
    # Add onboarding_completed column
    op.add_column('users', 
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Add onboarding_completed_at column
    op.add_column('users',
        sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Update existing users who have onboarding completed in preferences
    op.execute("""
        UPDATE users 
        SET onboarding_completed = TRUE,
            onboarding_completed_at = NOW()
        WHERE preferences LIKE '%"onboarding_completed": true%'
           OR preferences LIKE '%"onboarding_completed":true%'
    """)


def downgrade() -> None:
    """Remove onboarding_completed and onboarding_completed_at columns from users table."""
    op.drop_column('users', 'onboarding_completed_at')
    op.drop_column('users', 'onboarding_completed')