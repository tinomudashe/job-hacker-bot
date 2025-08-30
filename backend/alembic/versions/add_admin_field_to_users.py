"""add admin field to users table

Revision ID: add_admin_field
Revises: create_tailored_resumes
Create Date: 2025-08-30 14:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_admin_field'
down_revision = 'create_tailored_resumes'
branch_labels = None
depends_on = None

def upgrade():
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

def downgrade():
    # Remove is_admin column
    op.drop_column('users', 'is_admin')