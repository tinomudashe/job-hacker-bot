import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from datetime import datetime

from app.models_db import Document, User
from app.enhanced_memory import EnhancedMemoryManager
from app.documents import _analyze_single_document
from .list_documents import _list_documents

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class AnalyzeDocumentInput(BaseModel):
    document_name: str = Field(description="Name or partial name of the document to analyze.")

# Step 2: Define the core logic as a plain async function.
async def _analyze_specific_document(
    document_name: str,
    db: AsyncSession,
    user: User
) -> str:
    """The underlying implementation for analyzing a specific document by name."""
    try:
        doc_result = await db.execute(
            select(Document).where(
                Document.user_id == user.id,
                Document.name.ilike(f"%{document_name}%")
            )
        )
        documents = doc_result.scalars().all()
        
        if not documents:
            available_docs = await _list_documents(db, user)
            return f"📄 Document Not Found: '{document_name}'.\nAvailable documents:\n{available_docs}"
        
        if len(documents) > 1:
            doc_list = "\n".join([f"- {doc.name}" for doc in documents])
            return f"📄 Multiple Documents Found for '{document_name}':\n{doc_list}\nPlease be more specific."
        
        document = documents[0]
        
        memory_manager = EnhancedMemoryManager(db=db, user=user)
        user_profile_dict = {"name": user.name, "skills": user.skills.split(',') if user.skills else []}

        analysis = await _analyze_single_document(document, user_profile_dict, memory_manager)
        
        response_parts = [f"📄 **Analysis of: {document.name}**\n"]
        if analysis.get("analysis_results"):
            results = analysis["analysis_results"]
            for key, value in results.items():
                if value:
                    response_parts.append(f"**{key.replace('_', ' ').title()}:** {value}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        log.error(f"Error in _analyze_specific_document: {e}", exc_info=True)
        return f"❌ Sorry, I couldn't analyze the document '{document_name}'. Please try again."

# Step 3: Manually construct the Tool object with the explicit schema.
analyze_specific_document = Tool(
    name="analyze_specific_document",
    description="Analyze a specific document by name and provide detailed feedback.",
    func=_analyze_specific_document,
    args_schema=AnalyzeDocumentInput
)