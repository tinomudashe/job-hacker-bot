"""create tailored_resumes table

Revision ID: create_tailored_resumes
Revises: bdcc0e2f5fa6
Create Date: 2025-08-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_tailored_resumes'
down_revision = 'bdcc0e2f5fa6'
branch_labels = None
depends_on = None


def upgrade():
    # Create tailored_resumes table
    op.create_table(
        'tailored_resumes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('base_resume_id', sa.String(), nullable=False),
        sa.Column('job_title', sa.String(), nullable=True),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('job_description', sa.Text(), nullable=True),
        sa.Column('tailored_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_tailored_resumes_user_id', 
        'tailored_resumes', 
        'users', 
        ['user_id'], 
        ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_tailored_resumes_base_resume_id',
        'tailored_resumes',
        'resumes', 
        ['base_resume_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Add indexes for performance
    op.create_index('idx_tailored_resumes_user_id', 'tailored_resumes', ['user_id'])
    op.create_index('idx_tailored_resumes_base_resume_id', 'tailored_resumes', ['base_resume_id'])
    op.create_index('idx_tailored_resumes_job_title', 'tailored_resumes', ['job_title'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_tailored_resumes_job_title', table_name='tailored_resumes')
    op.drop_index('idx_tailored_resumes_base_resume_id', table_name='tailored_resumes')
    op.drop_index('idx_tailored_resumes_user_id', table_name='tailored_resumes')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_tailored_resumes_base_resume_id', 'tailored_resumes', type_='foreignkey')
    op.drop_constraint('fk_tailored_resumes_user_id', 'tailored_resumes', type_='foreignkey')
    
    # Drop table
    op.drop_table('tailored_resumes')