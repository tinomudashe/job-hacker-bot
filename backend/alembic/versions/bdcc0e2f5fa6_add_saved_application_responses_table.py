"""Add saved_application_responses table

Revision ID: bdcc0e2f5fa6
Revises: 699721152906
Create Date: 2025-08-25 08:47:45.455418

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'bdcc0e2f5fa6'
down_revision: Union[str, None] = '699721152906'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create saved_application_responses table
    op.create_table('saved_application_responses',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('field_category', sa.String(), nullable=False),
        sa.Column('field_label', sa.String(), nullable=False),
        sa.Column('field_value', sa.Text(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=True, default=False),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient lookups
    op.create_index(op.f('ix_saved_application_responses_field_category'), 'saved_application_responses', ['field_category'], unique=False)
    op.create_index('ix_saved_responses_user_category', 'saved_application_responses', ['user_id', 'field_category'], unique=False)
    op.create_index('ix_saved_responses_user_default', 'saved_application_responses', ['user_id', 'is_default'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('ix_saved_responses_user_default', table_name='saved_application_responses')
    op.drop_index('ix_saved_responses_user_category', table_name='saved_application_responses')
    op.drop_index(op.f('ix_saved_application_responses_field_category'), table_name='saved_application_responses')
    
    # Drop table
    op.drop_table('saved_application_responses')