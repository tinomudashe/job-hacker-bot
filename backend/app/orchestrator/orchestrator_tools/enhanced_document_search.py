from langchain_core.tools import tool
import logging
import re
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Document, User

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

# This tool needs to be wrapped by the dependency injector to get db and user
async def enhanced_document_search_logic(
    query: str,
    db: AsyncSession,
    user: User,
    doc_id: Optional[str] = None
) -> str:
    """
    Enhanced search across all user documents, including resumes, cover letters, and user profile.
    Prioritizes the most recently uploaded documents in case of ambiguity.
    If a file is mentioned in the query (e.g., "File Attached: resume.pdf"), it will be summarized directly.

    Args:
        query (str): The user's search query, which may include file attachment context.
        doc_id (Optional[str]): The specific ID of a document to search within.

    Returns:
        A formatted string containing the most relevant search results or a direct summary of an attached file.
    """
    try:
        user_id = user.id
        
        # INTELLIGENT FIX: Check for file attachment context in the user's message
        attachment_patterns = [
            r'File Attached:\s*(.+?)(?:\n|$)',
            r'CV/Resume uploaded successfully![\s\S]*?File:\s*(.+?)(?:\n|$)',
            # This new pattern looks for filenames mentioned directly in the query
            r'([\w.-]+\.(?:pdf|docx|doc|txt))\b'
        ]
        
        extracted_filename = None
        for pattern in attachment_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                extracted_filename = match.group(1).strip()
                break
        
        # If an attachment is explicitly mentioned, analyze it directly instead of searching
        if extracted_filename:
            log.info(f"Detected attached file in query: '{extracted_filename}'. Analyzing it directly.")
            
            # Find the specific document, prioritizing the most recent one
            doc_result = await db.execute(
                select(Document).where(
                    Document.user_id == user_id,
                    Document.name.ilike(f"%{extracted_filename}%")
                ).order_by(Document.date_created.desc())
            )
            documents = doc_result.scalars().all()

            if not documents:
                return f"I see you mentioned '{extracted_filename}', but I couldn't find that document in your uploads. Please try uploading it again."
            
            # Use the most recent document matching the name
            target_document = documents[0]
            
            if not target_document.content:
                return f"The document '{target_document.name}' was found but appears to be empty or unreadable."
            
            # Summarize the specific document's content to answer the user's implicit question
            summarization_prompt = ChatPromptTemplate.from_template(
                "You are a helpful assistant. Summarize the key points of the following document content in a few clear, concise paragraphs. Address the user directly and be informative.\n\n---\n\n{document_content}"
            )
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.2)
            chain = summarization_prompt | llm | StrOutputParser()
            
            # Limit content size for summarization to avoid token limits
            summary = await chain.ainvoke({"document_content": target_document.content[:4000]}) 
            
            user_first_name = user.first_name or "there"
            return f"Of course, {user_first_name}! Here is a summary of the document you just attached, '{target_document.name}':\n\n{summary}"

        # --- Fallback to original search logic if no attachment context is found ---
        log.info(f"No attachment context in query. Performing general search for: '{query}'")
        
        user_profile_content = (
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n"
            f"Location: {user.address}\n"
            f"LinkedIn: {user.linkedin}\n"
            f"Profile Headline: {user.profile_headline}\n"
            f"Skills: {user.skills}"
        )

        doc_result = await db.execute(
            select(Document).where(Document.user_id == user_id)
        )
        documents = doc_result.scalars().all()

        if not documents and not user_profile_content:
            return "No documents or user profile found to search."

        all_content = []
        if user_profile_content:
            all_content.append(
                {"id": "user_profile", "name": "USER PROFILE", "content": user_profile_content, "date_created": datetime.utcnow()}
            )
        for doc in documents:
            all_content.append(
                {"id": doc.id, "name": doc.name, "content": doc.content, "date_created": doc.date_created}
            )

        search_results = []
        for item in all_content:
            content_text = item.get("content", "") or ""
            if query.lower() in content_text.lower():
                search_results.append(item)

        search_results.sort(key=lambda x: x.get("date_created", datetime.min), reverse=True)

        if not search_results:
            return f"🔍 **No Results Found**\n\nI couldn't find any relevant information for '{query}' in your uploaded documents."

        response_parts = [
            f"**Search Results for '{query}'**\n",
            f"Found {len(search_results)} relevant sections:\n",
        ]
        for i, result in enumerate(search_results[:4], 1):
            content_preview = (result.get("content", "") or "")[:200]
            response_parts.append(
                f"**{i}.** [{result['name']}]\n{content_preview}..."
            )
        
        response_parts.append("\n💬 **Need more specific information? Ask me about any particular aspect or request a detailed analysis!**")
        return "\n\n".join(response_parts)

    except Exception as e:
        log.error(f"Error in enhanced document search: {e}", exc_info=True)
        return f"❌ Sorry, I couldn't search your documents for '{query}' right now. Please try again or let me know if you need help with document analysis."

# We create the tool from the logic function, but without the db and user parameters in the signature.
# The dependency injector will handle passing them at runtime.
@tool
async def enhanced_document_search(
    query: str,
    doc_id: Optional[str] = None
) -> str:
    # This wrapper is what the AI agent sees. It has a clean signature.
    # The actual implementation is in the _logic function, which will be called by the injector.
    pass

# Replace the original tool's function with our logic so the injector can find it.
enhanced_document_search.func = enhanced_document_search_logic
