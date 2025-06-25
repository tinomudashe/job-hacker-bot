"""add success column to applications table

Revision ID: 1add_success_to_applications
Revises: abf8887c03b6
Create Date: 2024-06-12 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1add_success_to_applications'
down_revision = 'abf8887c03b6'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('applications', sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.true()))

def downgrade():
    op.drop_column('applications', 'success') 