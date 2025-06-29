"""Enhanced memory tables

Revision ID: enhanced_memory_001
Revises: 81fcc1a80524
Create Date: 2025-01-26 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'enhanced_memory_001'
down_revision = '81fcc1a80524'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('preference_key', sa.String(), nullable=False),
        sa.Column('preference_value', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'preference_key', name='unique_user_preference')
    )
    
    # Create user_behaviors table
    op.create_table('user_behaviors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_user_preferences_user_id', 'user_preferences', ['user_id'])
    op.create_index('idx_user_preferences_key', 'user_preferences', ['preference_key'])
    op.create_index('idx_user_behaviors_user_id', 'user_behaviors', ['user_id'])
    op.create_index('idx_user_behaviors_action_type', 'user_behaviors', ['action_type'])
    op.create_index('idx_user_behaviors_created_at', 'user_behaviors', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_behaviors_created_at', 'user_behaviors')
    op.drop_index('idx_user_behaviors_action_type', 'user_behaviors')
    op.drop_index('idx_user_behaviors_user_id', 'user_behaviors')
    op.drop_index('idx_user_preferences_key', 'user_preferences')
    op.drop_index('idx_user_preferences_user_id', 'user_preferences')
    
    # Drop tables
    op.drop_table('user_behaviors')
    op.drop_table('user_preferences') 