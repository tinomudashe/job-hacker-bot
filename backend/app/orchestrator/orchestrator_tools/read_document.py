from langchain_core.tools import tool
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Document, User

log = logging.getLogger(__name__)

@tool
async def read_document(
    filename: str,
    db: AsyncSession,
    user: User
) -> str:
    """Reads the content of a specified document from the database."""
    try:
        user_id = user.id
        # Search for document in database by name (case-insensitive partial match)
        doc_result = await db.execute(
            select(Document).where(
                Document.user_id == user_id,
                Document.name.ilike(f"%{filename}%")
            )
        )
        documents = doc_result.scalars().all()
        
        if not documents:
            return f"Error: Document '{filename}' not found in your uploaded documents."
        
        if len(documents) > 1:
            doc_list = "\n".join([f"- {doc.name}" for doc in documents])
            return f"Multiple documents found matching '{filename}':\n{doc_list}\n\nPlease be more specific with the document name."
        
        document = documents[0]
        
        if not document.content:
            return f"Error: Document '{document.name}' found but has no content."
        
        return f"Content of {document.name}:\n\n{document.content}"
        
    except Exception as e:
        log.error(f"Error reading document: {e}", exc_info=True)
        return f"Error reading document: {e}"