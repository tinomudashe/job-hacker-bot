from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Document, User

@tool
async def list_documents(db: AsyncSession, user: User) -> str:
    """Lists the documents available to the user."""
    user_id = user.id
    result = await db.execute(
        select(Document.name).where(Document.user_id == user_id)
    )
    documents = result.scalars().all()
    if not documents:
        return "No documents found."
    return "Available documents:\n" + "\n".join(f"- {doc}" for doc in documents)