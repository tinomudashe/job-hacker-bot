import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import Document, User

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class ReadDocumentInput(BaseModel):
    filename: str = Field(description="The name of the document to read.")

# Step 2: Define the core logic as a plain async function.
async def _read_document(filename: str, db: AsyncSession, user: User) -> str:
    """The underlying implementation for reading the content of a specified document."""
    try:
        # Use an exact match for clarity, or a more specific search if needed.
        doc_result = await db.execute(
            select(Document).where(Document.user_id == user.id, Document.name == filename)
        )
        document = doc_result.scalars().first()
        
        if not document:
            # If not found, try a case-insensitive search as a fallback.
            like_result = await db.execute(select(Document.name).where(Document.user_id == user.id, Document.name.ilike(f"%{filename}%")))
            possible_matches = like_result.scalars().all()
            if possible_matches:
                return f"Document '{filename}' not found. Did you mean one of these?\n- " + "\n- ".join(possible_matches)
            return f"❌ Error: Document '{filename}' not found."
        
        if not document.content:
            return f"⚠️ Warning: Document '{document.name}' was found but has no readable content."
        
        # Return a preview to avoid returning excessively long content to the agent.
        content_preview = document.content[:2000]
        return f"**Content of {document.name}:**\n\n{content_preview}{'...' if len(document.content) > 2000 else ''}"
        
    except Exception as e:
        log.error(f"Error in _read_document for user {user.id}, filename {filename}: {e}", exc_info=True)
        return f"❌ An error occurred while reading the document: {e}"

# Step 3: Manually construct the Tool object with the explicit schema.
read_document = Tool(
    name="read_document",
    description="Reads the content of a specified document from the database.",
    func=_read_document,
    args_schema=ReadDocumentInput
)