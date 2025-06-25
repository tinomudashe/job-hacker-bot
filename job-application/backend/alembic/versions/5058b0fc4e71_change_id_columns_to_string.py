"""change_id_columns_to_string

Revision ID: 5058b0fc4e71
Revises: 9fe025aabff1
Create Date: 2025-06-10 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5058b0fc4e71'
down_revision: Union[str, None] = '9fe025aabff1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop foreign key constraints first
    op.drop_constraint('applications_user_id_fkey', 'applications', type_='foreignkey')
    op.drop_constraint('applications_job_id_fkey', 'applications', type_='foreignkey')
    op.drop_constraint('applications_resume_id_fkey', 'applications', type_='foreignkey')
    op.drop_constraint('applications_cover_letter_id_fkey', 'applications', type_='foreignkey')
    op.drop_constraint('documents_user_id_fkey', 'documents', type_='foreignkey')
    op.drop_constraint('notifications_user_id_fkey', 'notifications', type_='foreignkey')

    # Change column types
    op.alter_column('users', 'id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('job_listings', 'id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('documents', 'id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('documents', 'user_id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('notifications', 'id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('notifications', 'user_id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('applications', 'id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('applications', 'user_id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('applications', 'job_id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('applications', 'resume_id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)
    op.alter_column('applications', 'cover_letter_id',
                    existing_type=sa.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)

    # Recreate foreign key constraints
    op.create_foreign_key('applications_user_id_fkey', 'applications', 'users', ['user_id'], ['id'])
    op.create_foreign_key('applications_job_id_fkey', 'applications', 'job_listings', ['job_id'], ['id'])
    op.create_foreign_key('applications_resume_id_fkey', 'applications', 'documents', ['resume_id'], ['id'])
    op.create_foreign_key('applications_cover_letter_id_fkey', 'applications', 'documents', ['cover_letter_id'], ['id'])
    op.create_foreign_key('documents_user_id_fkey', 'documents', 'users', ['user_id'], ['id'])
    op.create_foreign_key('notifications_user_id_fkey', 'notifications', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints first
    op.drop_constraint('applications_user_id_fkey', 'applications', type_='foreignkey')
    op.drop_constraint('applications_job_id_fkey', 'applications', type_='foreignkey')
    op.drop_constraint('applications_resume_id_fkey', 'applications', type_='foreignkey')
    op.drop_constraint('applications_cover_letter_id_fkey', 'applications', type_='foreignkey')
    op.drop_constraint('documents_user_id_fkey', 'documents', type_='foreignkey')
    op.drop_constraint('notifications_user_id_fkey', 'notifications', type_='foreignkey')

    # Change column types back to UUID
    op.alter_column('users', 'id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('job_listings', 'id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('documents', 'id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('documents', 'user_id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('notifications', 'id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('notifications', 'user_id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('applications', 'id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('applications', 'user_id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('applications', 'job_id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('applications', 'resume_id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)
    op.alter_column('applications', 'cover_letter_id',
                    existing_type=sa.String(),
                    type_=sa.UUID(),
                    existing_nullable=False)

    # Recreate foreign key constraints
    op.create_foreign_key('applications_user_id_fkey', 'applications', 'users', ['user_id'], ['id'])
    op.create_foreign_key('applications_job_id_fkey', 'applications', 'job_listings', ['job_id'], ['id'])
    op.create_foreign_key('applications_resume_id_fkey', 'applications', 'documents', ['resume_id'], ['id'])
    op.create_foreign_key('applications_cover_letter_id_fkey', 'applications', 'documents', ['cover_letter_id'], ['id'])
    op.create_foreign_key('documents_user_id_fkey', 'documents', 'users', ['user_id'], ['id'])
    op.create_foreign_key('notifications_user_id_fkey', 'notifications', 'users', ['user_id'], ['id'])
