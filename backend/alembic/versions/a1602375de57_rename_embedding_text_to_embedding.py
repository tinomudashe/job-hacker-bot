"""rename_embedding_text_to_embedding

Revision ID: a1602375de57
Revises: dd1c6d3e3b4a
Create Date: 2025-08-20 22:29:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'a1602375de57'
down_revision: Union[str, None] = 'dd1c6d3e3b4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, drop the old text column if it exists
    op.execute("ALTER TABLE langchain_pg_embedding DROP COLUMN IF EXISTS embedding_text")
    
    # Add the new embedding column as a vector type
    # Using raw SQL to handle vector type properly
    op.execute("ALTER TABLE langchain_pg_embedding ADD COLUMN IF NOT EXISTS embedding vector(1536)")


def downgrade() -> None:
    # Drop the vector column
    op.execute("ALTER TABLE langchain_pg_embedding DROP COLUMN IF EXISTS embedding")
    
    # Re-add the text column
    op.add_column('langchain_pg_embedding', 
                  sa.Column('embedding_text', sa.Text(), nullable=True))