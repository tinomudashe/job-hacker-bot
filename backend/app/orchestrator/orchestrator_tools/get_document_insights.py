import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from langchain_core.tools import Tool

from app.models_db import Document, User
from app.enhanced_memory import EnhancedMemoryManager
from app.documents import _generate_comprehensive_document_insights

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema (even if empty).
class GetInsightsInput(BaseModel):
    pass

# Step 2: Define the core logic as a plain async function.
async def _get_document_insights(db: AsyncSession, user: User) -> str:
    """The underlying implementation for getting personalized insights about a user's documents."""
    try:
        doc_result = await db.execute(select(Document).where(Document.user_id == user.id))
        documents = doc_result.scalars().all()

        if not documents:
            return "📄 **No Documents Found**: Please upload your resume or other career documents to get personalized insights."
        
        memory_manager = EnhancedMemoryManager(db=db, user=user)
        user_profile = await memory_manager.get_conversation_context()

        insights = await _generate_comprehensive_document_insights(documents, user_profile, memory_manager)
        
        response_parts = ["📄 **Document Insights & Analysis**\n"]
        if insights.get("summary"):
            response_parts.append(f"**Summary:** {insights['summary']}\n")
        
        if insights.get("recommendations"):
            response_parts.append("**💡 Recommendations:**")
            for rec in insights["recommendations"]:
                response_parts.append(f"- {rec}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        log.error(f"Error in _get_document_insights: {e}", exc_info=True)
        return "❌ Sorry, I couldn't retrieve your document insights right now. Please try again."

# Step 3: Manually construct the Tool object with the explicit schema.
get_document_insights = Tool(
    name="get_document_insights",
    description="Get personalized insights about user's uploaded documents including analysis and recommendations.",
    func=_get_document_insights,
    args_schema=GetInsightsInput
)