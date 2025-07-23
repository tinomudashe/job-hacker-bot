from langchain_core.tools import tool
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Document, User
from app.enhanced_memory import EnhancedMemoryManager
from app.documents import _analyze_single_document
from .list_documents import list_documents
from datetime import datetime

log = logging.getLogger(__name__)

@tool
async def analyze_specific_document(
    document_name: str,
    db: AsyncSession,
    user: User,
    memory_manager: EnhancedMemoryManager
) -> str:
    """Analyze a specific document by name and provide detailed feedback.
    
    Args:
        document_name: Name or partial name of the document to analyze
        
    Returns:
        Detailed analysis and personalized feedback for the specified document
    """
    try:
        # Search for documents matching the name
        doc_result = await db.execute(
            select(Document).where(
                Document.user_id == user.id,
                Document.name.ilike(f"%{document_name}%")
            )
        )
        documents = doc_result.scalars().all()
        
        if not documents:
            available_docs = await list_documents(db, user)
            return f"📄 **Document Not Found**\n\nI couldn't find any document matching '{document_name}'. \n\n**Available documents:**\n" + available_docs
        
        if len(documents) > 1:
            doc_list = "\n".join([f"- {doc.name} ({doc.type})" for doc in documents])
            return f"📄 **Multiple Documents Found**\n\nFound {len(documents)} documents matching '{document_name}':\n\n{doc_list}\n\nPlease be more specific with the document name."
        
        document = documents[0]
        
        # Get detailed analysis using enhanced memory system
        user_profile_dict = {
            "name": user.name or f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "profile_headline": user.profile_headline or "",
            "skills": user.skills.split(',') if user.skills else []
        }

        analysis = await _analyze_single_document(document, user_profile_dict, memory_manager)

        # Track specific document analysis
        if memory_manager:
            await memory_manager.save_user_behavior(
            action_type="specific_document_analysis_tool",
            context={
                "document_id": document.id,
                "document_name": document.name,
                "document_type": document.type,
                "relevance_score": analysis.get("relevance_score", 0),
                "timestamp": datetime.utcnow().isoformat()
            },
            success=True
        )
        
        # Format the detailed analysis response
        response_parts = [
            f"📄 **Analysis: {analysis['document_info']['name']}**\n",
            f"**Document Type:** {analysis['document_info']['type'].title()}",
            f"**Created:** {analysis['document_info']['created'][:10]}",
            f"**Last Updated:** {analysis['document_info']['updated'][:10]}\n"
        ]
        
        # Content analysis
        if analysis.get("content_analysis"):
            content = analysis["content_analysis"]
            response_parts.append("**📊 Content Analysis:**")
            response_parts.append(f"- Word Count: {content.get('word_count', 0)}")
            response_parts.append(f"- Reading Time: {content.get('estimated_reading_time', 'Unknown')}")
            response_parts.append("")
        
        # Relevance score
        if analysis.get("relevance_score"):
            score = analysis["relevance_score"]
            score_percentage = int(score * 100)
            response_parts.append(f"**🎯 Relevance to Your Career Goals:** {score_percentage}%")
            response_parts.append("")
        
        # Resume-specific analysis
        if analysis.get("sections_detected"):
            response_parts.append("**📋 Resume Sections Detected:**")
            response_parts.append(f"- Found: {', '.join(analysis['sections_detected'])}")
            response_parts.append("")
        
        if analysis.get("skills_found"):
            response_parts.append("**💼 Technical Skills Identified:**")
            response_parts.append(f"- {', '.join(analysis['skills_found'])}")
            response_parts.append("")
        
        # Cover letter analysis
        if analysis.get("tone_indicators"):
            response_parts.append("**🎭 Tone Analysis:**")
            response_parts.append(f"- Detected: {', '.join(analysis['tone_indicators'])}")
            response_parts.append("")
        
        # Personalized feedback
        if analysis.get("personalized_feedback"):
            response_parts.append("**💡 Personalized Feedback:**")
            for i, feedback in enumerate(analysis["personalized_feedback"], 1):
                response_parts.append(f"{i}. {feedback}")
            response_parts.append("")
        
        # Improvement suggestions
        if analysis.get("improvement_suggestions"):
            response_parts.append("**⚡ Improvement Suggestions:**")
            for i, suggestion in enumerate(analysis["improvement_suggestions"], 1):
                response_parts.append(f"{i}. {suggestion}")
            response_parts.append("")
        
        # Resume-specific feedback
        if analysis.get("resume_feedback"):
            response_parts.append("**📄 Resume-Specific Feedback:**")
            for i, feedback in enumerate(analysis["resume_feedback"], 1):
                response_parts.append(f"{i}. {feedback}")
            response_parts.append("")
        
        # Cover letter feedback
        if analysis.get("cover_letter_feedback"):
            response_parts.append("**✉️ Cover Letter Feedback:**")
            for i, feedback in enumerate(analysis["cover_letter_feedback"], 1):
                response_parts.append(f"{i}. {feedback}")
            response_parts.append("")
        
        response_parts.append("💬 **Want more specific help? I can help you rewrite sections, add keywords, or create new versions tailored to specific job applications!**")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        log.error(f"Error analyzing specific document: {e}", exc_info=True)
        return f"❌ Sorry, I couldn't analyze the document '{document_name}' right now. Please try again or upload the document if it's missing."