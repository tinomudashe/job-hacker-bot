import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models_db import Document, User, Resume
from app.resume import ResumeData
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema (even if empty).
class ExtractAndPopulateInput(BaseModel):
    pass

# Step 2: Define the core logic as a plain async function.
async def _extract_and_populate_profile_from_documents(db: AsyncSession, user: User) -> str:
    """The underlying implementation for extracting and populating user profile from documents."""
    try:
        doc_result = await db.execute(select(Document).where(Document.user_id == user.id))
        documents = doc_result.scalars().all()
        if not documents:
            return "❌ No documents found. Please upload your CV/resume first."

        document_content = "\n\n---\n\n".join([doc.content for doc in documents if doc.content])
        if not document_content.strip():
            return "❌ Uploaded documents have no readable content."

        parser = PydanticOutputParser(pydantic_object=ResumeData)
        prompt = ChatPromptTemplate(
            template="""You are an expert information extractor. From the document content, extract all resume information.
            Return ONLY a valid JSON object matching the schema. Use null for missing fields and empty arrays for missing lists.

            DOCUMENT CONTENT: {document_content}
            
            {format_instructions}""",
            input_variables=["document_content"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        # Use a powerful model for this complex extraction task [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.1)
        chain = prompt | llm | parser

        extracted_data: ResumeData = await chain.ainvoke({"document_content": document_content[:20000]})

        # --- Populate Database ---
        db_resume, _ = await get_or_create_resume(db, user)
        db_resume.data = extracted_data.model_dump(exclude_none=True)
        attributes.flag_modified(db_resume, "data")

        # Sync key fields back to the User model for quick access
        if extracted_data.personal_info:
            p_info = extracted_data.personal_info
            user.name = p_info.name
            user.email = p_info.email
            user.phone = p_info.phone
            user.address = p_info.location
            user.linkedin = p_info.linkedin
            user.profile_headline = p_info.summary
        if extracted_data.skills:
            user.skills = ", ".join(extracted_data.skills)

        await db.commit()
        return "✅ Profile and resume successfully populated from your documents."

    except Exception as e:
        log.error(f"Error in _extract_and_populate_profile_from_documents for user {user.id}: {e}", exc_info=True)
        await db.rollback()
        return f"❌ An error occurred while populating your profile: {e}"

# Step 3: Manually construct the Tool object with the explicit schema.
extract_and_populate_profile_from_documents = Tool(
    name="extract_and_populate_profile_from_documents",
    description="Extracts comprehensive information from uploaded CV/resume documents to automatically populate the user's profile and resume data.",
    func=_extract_and_populate_profile_from_documents,
    args_schema=ExtractAndPopulateInput
)