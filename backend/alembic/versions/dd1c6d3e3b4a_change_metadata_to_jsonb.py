"""Change metadata to JSONB

Revision ID: dd1c6d3e3b4a
Revises: 4ac50c322fc8
Create Date: 2025-07-23 09:50:00.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dd1c6d3e3b4a'
down_revision: Union[str, None] = '4ac50c322fc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change the metadata column in langchain_pg_embedding from JSON to JSONB
    for improved performance and to resolve the LangChainPendingDeprecationWarning.
    """
    op.alter_column('langchain_pg_embedding', 'cmetadata',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(),
               existing_nullable=True,
               postgresql_using='cmetadata::text::jsonb')


def downgrade() -> None:
    """
    Revert the metadata column in langchain_pg_embedding from JSONB back to JSON.
    """
    op.alter_column('langchain_pg_embedding', 'cmetadata',
               existing_type=postgresql.JSONB(),
               type_=sa.JSON(),
               existing_nullable=True,
               postgresql_using='cmetadata::text::json') 