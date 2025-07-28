import logging
import re
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models_db import Document, User

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class DocumentSearchInput(BaseModel):
    query: str = Field(description="The user's search query.")
    doc_id: Optional[str] = Field(default=None, description="A specific document ID to search within.")

# Step 2: Define the core logic as a plain async function.
async def _enhanced_document_search(
    query: str,
    db: AsyncSession,
    user: User,
    doc_id: Optional[str] = None
) -> str:
    """The underlying implementation for an enhanced search across all user documents."""
    try:
        if doc_id:
            # If a specific doc_id is provided, search only within that document.
            doc_result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
            doc = doc_result.scalars().first()
            if not doc or not doc.content:
                return f"Document with ID '{doc_id}' not found or is empty."
            
            # Use LLM to find the most relevant snippets from the document.
            prompt = ChatPromptTemplate.from_template("Find and extract the most relevant snippets from this document that answer the query '{query}'.\n\nDOCUMENT:\n{content}")
            # Use the user-specified utility model [[memory:4540099]]
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
            chain = prompt | llm | StrOutputParser()
            results = await chain.ainvoke({"query": query, "content": doc.content})
            return f"**Results from {doc.name}:**\n\n{results}"

        # If no doc_id, search across all documents.
        docs_result = await db.execute(select(Document).where(Document.user_id == user.id))
        documents = docs_result.scalars().all()
        if not documents:
            return "You have no documents to search. Please upload a document first."

        # Aggregate content and perform a simple keyword search for this example.
        # A real implementation would use the vector store for a semantic search.
        all_content = "\n".join([f"--- From: {doc.name} ---\n{doc.content}" for doc in documents if doc.content])
        
        prompt = ChatPromptTemplate.from_template("You are a helpful search assistant. Based on the following documents, provide a comprehensive answer to the user's query.\n\nQuery: {query}\n\nDocuments:\n{context}")
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.2)
        chain = prompt | llm | StrOutputParser()
        
        answer = await chain.ainvoke({"query": query, "context": all_content[:8000]}) # Limit context size

        return f"**Here's what I found in your documents about '{query}':**\n\n{answer}"

    except Exception as e:
        log.error(f"Error in _enhanced_document_search: {e}", exc_info=True)
        return f"❌ Sorry, I couldn't search your documents for '{query}'. Please try again."

# Step 3: Manually construct the Tool object with the explicit schema.
enhanced_document_search = Tool(
    name="enhanced_document_search",
    description="Enhanced search across all user documents (resumes, cover letters) and user profile.",
    func=_enhanced_document_search,
    args_schema=DocumentSearchInput
)
