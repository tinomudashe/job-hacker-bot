"""fix_embedding_dimension_to_768

Revision ID: 0849b95dc29c
Revises: 2213ff448010
Create Date: 2025-08-20 23:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0849b95dc29c'
down_revision: Union[str, None] = '2213ff448010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing embedding column with wrong dimension
    op.execute("ALTER TABLE langchain_pg_embedding DROP COLUMN IF EXISTS embedding")
    
    # Add the embedding column with correct dimension for Google's text-embedding-004
    op.execute("ALTER TABLE langchain_pg_embedding ADD COLUMN embedding vector(768)")


def downgrade() -> None:
    # Drop the 768-dimension column
    op.execute("ALTER TABLE langchain_pg_embedding DROP COLUMN IF EXISTS embedding")
    
    # Re-add with 1536 dimensions
    op.execute("ALTER TABLE langchain_pg_embedding ADD COLUMN embedding vector(1536)")