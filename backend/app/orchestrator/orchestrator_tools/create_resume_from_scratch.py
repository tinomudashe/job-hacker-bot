import logging
import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models_db import Document, User
from app.resume import ResumeData
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class CreateResumeFromScratchInput(BaseModel):
    target_role: str = Field(description="The user's target job role.")
    experience_level: Optional[str] = Field(default="mid-level", description="The user's experience level.")
    industry: Optional[str] = Field(default="", description="The target industry.")
    key_skills: Optional[str] = Field(default="", description="Key skills to highlight.")

# Step 2: Define the core logic as a plain async function.
async def _create_resume_from_scratch(
    db: AsyncSession,
    user: User,
    target_role: str,
    experience_level: str = "mid-level",
    industry: str = "",
    key_skills: str = ""
) -> str:
    """The underlying implementation for creating a complete professional resume from scratch."""
    try:
        doc_result = await db.execute(
            select(Document).where(Document.user_id == user.id).order_by(Document.date_created.desc())
        )
        documents = doc_result.scalars().all()
        
        document_content = "\n".join([doc.content for doc in documents if doc.content])
        
        if not document_content:
             return "I couldn't find any documents to build your resume from. Please upload a document (like an old resume or bio) first."

        extraction_prompt = ChatPromptTemplate.from_template(
            "Extract comprehensive resume information from these documents: {document_content}. Return it as a valid JSON object with keys: 'personalInfo', 'experience', 'education', 'skills'."
        )
        
        # Use the user-specified utility model [[memory:4540099]]
        extraction_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.1)
        extraction_chain = extraction_prompt | extraction_llm | JsonOutputParser()
        
        comprehensive_info = await extraction_chain.ainvoke({"document_content": document_content})

        if not comprehensive_info or not comprehensive_info.get("experience"):
            return "I was able to read your documents, but couldn't find your work experience. Could you please provide it so I can create your resume?"
        
        parser = PydanticOutputParser(pydantic_object=ResumeData)
        prompt = ChatPromptTemplate.from_template(
            """You are an expert resume writer. Create a complete, populated resume using the user's information.
            
            USER INFORMATION (JSON): {context}
            CAREER GOAL: Target Role: {target_role}
            INSTRUCTIONS: Use ONLY the information from the user's JSON context. Do NOT use placeholders. Format the output as a valid JSON object matching the schema.
            {format_instructions}
            """
        )
        
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7)
        chain = prompt | llm | parser
        
        new_resume_data = await chain.ainvoke({
            "context": json.dumps(comprehensive_info),
            "target_role": target_role,
            "format_instructions": parser.get_format_instructions(),
        })

        db_resume, _ = await get_or_create_resume(db, user)
        db_resume.data = new_resume_data.dict()
        attributes.flag_modified(db_resume, "data")
        await db.commit()
        
        return (f"I have created a new resume draft for you, tailored for a {target_role} role. "
                "You can now preview, edit, and download it. [DOWNLOADABLE_RESUME]")
        
    except Exception as e:
        log.error(f"Error in _create_resume_from_scratch: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return f"❌ Sorry, I encountered an error while creating your resume: {str(e)}."

# Step 3: Manually construct the Tool object with the explicit schema.
create_resume_from_scratch = Tool(
    name="create_resume_from_scratch",
    description="Create a complete professional resume from scratch based on your career goals.",
    func=_create_resume_from_scratch,
    args_schema=CreateResumeFromScratchInput
)