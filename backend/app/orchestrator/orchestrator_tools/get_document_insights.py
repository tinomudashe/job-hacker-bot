from langchain_core.tools import tool
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Document, User
from app.enhanced_memory import EnhancedMemoryManager
from app.documents import _generate_comprehensive_document_insights
from datetime import datetime

log = logging.getLogger(__name__)

@tool
async def get_document_insights(
    db: AsyncSession,
    user: User,
    memory_manager: EnhancedMemoryManager
) -> str:
    """Get personalized insights about user's uploaded documents including analysis and recommendations.
    
        Returns:
        Comprehensive insights about user's documents, career alignment, and optimization recommendations
    """
    try:
        # First, fetch the user's documents from the database.
        doc_result = await db.execute(
            select(Document).where(Document.user_id == user.id).order_by(Document.date_created.desc())
        )
        documents = doc_result.scalars().all()

        # INTELLIGENT FIX: Ensure the correct memory manager is used for this advanced tool
        current_memory_manager = memory_manager
        if not isinstance(current_memory_manager, EnhancedMemoryManager):
            # If the provided manager is the simple one, create an enhanced one for this specific task
            log.warning("SimpleMemoryManager provided to advanced tool, creating temporary EnhancedMemoryManager.")
            current_memory_manager = EnhancedMemoryManager(db_session=db, user=user)
            await current_memory_manager.load_memory()

        if not documents:
            return "📄 **No Documents Found**\n\nYou haven't uploaded any documents yet. Upload your resume, cover letters, or other career documents to get personalized insights and recommendations!\n\n**To upload documents:**\n- Use the attachment button in the chat\n- Drag and drop files into the chat\n- Supported formats: PDF, DOCX, TXT"
        
        # Get user learning profile
        if current_memory_manager:
            context = await current_memory_manager.get_conversation_context()
            user_profile = context
        else:
            user_profile = None
        
        # Generate comprehensive insights
        insights = await _generate_comprehensive_document_insights(
            documents, user_profile, current_memory_manager
        )
        
        # Track insights tool usage
        if current_memory_manager:
            await current_memory_manager.save_user_behavior(
                action_type="document_insights_tool",
                context={
                "documents_count": len(documents),
                    "recommendations_count": len(insights.get("recommendations", [])),
                    "optimization_tips_count": len(insights.get("optimization_tips", [])),
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=True
            )
        
        # Format the response for chat
        response_parts = [
            "📄 **Document Insights & Analysis**\n",
            f"**Summary:** {insights['summary']}\n"
        ]
        
        # Document analysis
        if insights.get("document_analysis"):
            analysis = insights["document_analysis"]
            response_parts.append("**📊 Document Overview:**")
            response_parts.append(f"- Total Documents: {analysis.get('total_documents', 0)}")
            
            doc_types = analysis.get('document_types', {})
            if doc_types:
                type_summary = ", ".join([f"{count} {doc_type}(s)" for doc_type, count in doc_types.items()])
                response_parts.append(f"- Types: {type_summary}")
            
            if analysis.get('latest_update'):
                response_parts.append(f"- Last Updated: {analysis['latest_update'][:10]}")
            response_parts.append("")
        
        # Career alignment
        if insights.get("career_alignment"):
            alignment = insights["career_alignment"]
            response_parts.append("**🎯 Career Alignment:**")
            response_parts.append(f"- Target Roles: {', '.join(alignment.get('target_roles', []))}")
            response_parts.append(f"- Alignment Score: {alignment.get('document_relevance_score', 0)}/1.0 ({alignment.get('alignment_status', 'Unknown')})")
            response_parts.append("")
        
        # Recommendations
        if insights.get("recommendations"):
            response_parts.append("**💡 Personalized Recommendations:**")
            for i, recommendation in enumerate(insights["recommendations"], 1):
                response_parts.append(f"{i}. {recommendation}")
            response_parts.append("")
        
        # Optimization tips
        if insights.get("optimization_tips"):
            response_parts.append("**⚡ Optimization Tips:**")
            for i, tip in enumerate(insights["optimization_tips"], 1):
                response_parts.append(f"{i}. {tip}")
            response_parts.append("")
        
        response_parts.append("💬 **Need help with any specific document? Just ask me to analyze a particular file or help you improve your resume/cover letter!**")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        log.error(f"Error getting document insights: {e}", exc_info=True)
        return "❌ Sorry, I couldn't retrieve your document insights right now. Please try again or let me know if you need help with document analysis."