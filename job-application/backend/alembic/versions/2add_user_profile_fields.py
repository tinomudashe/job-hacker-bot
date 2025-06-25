"""add user profile fields to users table

Revision ID: 2add_user_profile_fields
Revises: 1add_success_to_applications
Create Date: 2024-06-12 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2add_user_profile_fields'
down_revision = '1add_success_to_applications'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('address', sa.String(), nullable=True))
    op.add_column('users', sa.Column('linkedin', sa.String(), nullable=True))
    op.add_column('users', sa.Column('preferred_language', sa.String(), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.String(), nullable=True))
    op.add_column('users', sa.Column('profile_headline', sa.String(), nullable=True))
    op.add_column('users', sa.Column('skills', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('profile_picture_url', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'address')
    op.drop_column('users', 'linkedin')
    op.drop_column('users', 'preferred_language')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'profile_headline')
    op.drop_column('users', 'skills')
    op.drop_column('users', 'profile_picture_url') 