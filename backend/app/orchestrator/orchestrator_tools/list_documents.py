import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from langchain_core.tools import Tool

from app.models_db import Document, User

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema (even if empty).
class ListDocumentsInput(BaseModel):
    pass

# Step 2: Define the core logic as a plain async function.
async def _list_documents(db: AsyncSession, user: User) -> str:
    """The underlying implementation for listing a user's available documents."""
    try:
        result = await db.execute(
            select(Document.name, Document.type).where(Document.user_id == user.id)
        )
        documents = result.all()
        
        if not documents:
            return "You have no documents uploaded. Use the attachment button to add your resume, cover letter, or other files."
            
        doc_list = [f"- {name} (Type: {doc_type or 'Unknown'})" for name, doc_type in documents]
        return "📄 **Your Documents:**\n" + "\n".join(doc_list)

    except Exception as e:
        log.error(f"Error in _list_documents for user {user.id}: {e}", exc_info=True)
        return "❌ An error occurred while listing your documents."

# Step 3: Manually construct the Tool object with the explicit schema.
list_documents = Tool(
    name="list_documents",
    description="Lists all documents the user has uploaded.",
    func=_list_documents,
    args_schema=ListDocumentsInput
)