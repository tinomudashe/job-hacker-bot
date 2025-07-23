from langchain_core.tools import tool
import logging
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from app.models_db import Document, User
from app.resume import ResumeData
from .get_or_create_resume import get_or_create_resume

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

@tool
async def create_resume_from_scratch(
    db: AsyncSession,
    user: User,
    target_role: str,
    experience_level: str = "mid-level",
    industry: str = "",
    key_skills: str = ""
) -> str:
    """Create a complete professional resume from scratch based on your career goals."""
    try:
        # 1. Extract comprehensive information from user's documents.
        doc_result = await db.execute(
            select(Document).where(Document.user_id == user.id).order_by(Document.date_created.desc())
        )
        documents = doc_result.scalars().all()
        
        document_content = ""
        if documents:
            for doc in documents[:5]:
                if doc.content and len(doc.content) > 100:
                    document_content += f"\n\n=== DOCUMENT: {doc.name} ===\n{doc.content[:3000]}"
        
        comprehensive_info = ""
        if document_content:
            extraction_prompt = ChatPromptTemplate.from_template(
                """Extract comprehensive resume information from these documents and return it as a valid JSON object.
                
                {document_content}
                
                The JSON object should have keys: 'personalInfo', 'experience', 'education', 'skills'."""
            )
            
            extraction_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.1)
            extraction_chain = extraction_prompt | extraction_llm | JsonOutputParser()
            
            try:
                comprehensive_info = await extraction_chain.ainvoke({"document_content": document_content})
            except Exception as e:
                log.warning(f"Failed to extract comprehensive info as JSON: {e}")
                comprehensive_info = {}

        # 2. Verify if critical information was found.
        missing_sections = []
        if not comprehensive_info or not comprehensive_info.get("experience"):
            missing_sections.append("work experience")
        if not comprehensive_info or not comprehensive_info.get("education"):
            missing_sections.append("education history")
        if not comprehensive_info or not comprehensive_info.get("skills"):
            missing_sections.append("key skills")
        
        # 3. If information is missing, ask the user for it.
        if missing_sections:
            missing_str = ", ".join(missing_sections)
            return (
                f"I've started drafting your resume for a {target_role} role, but I couldn't find details about your {missing_str} in your documents. "
                "To create the best resume for you, could you please provide this information?"
            )
        
        # 4. If data exists, create a structured resume using the AI.
        parser = PydanticOutputParser(pydantic_object=ResumeData)
        prompt = ChatPromptTemplate.from_template(
            """You are an expert resume writer. Create a complete, populated resume using the user's information.
            
            USER INFORMATION (JSON):
            {context}

            CAREER GOAL:
            - Target Role: {target_role}

            INSTRUCTIONS:
            - Use ONLY the information from the user's JSON context.
            - Do NOT use placeholders.
            - Format the output as a valid JSON object matching the schema.

            {format_instructions}
            """
        )
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7)
        chain = prompt | llm | parser
        
        new_resume_data = await chain.ainvoke({
            "context": json.dumps(comprehensive_info),
            "target_role": target_role,
            "format_instructions": parser.get_format_instructions(),
        })

        # 5. Save the structured JSON to the master Resume record.
        db_resume, _ = await get_or_create_resume(db, user)
        db_resume.data = new_resume_data.dict()
        attributes.flag_modified(db_resume, "data")
        await db.commit()
        
        return (f"I have created a new resume draft for you, tailored for a {target_role} role. "
                "You can now preview, edit, and download it. [DOWNLOADABLE_RESUME]")
        
    except Exception as e:
        log.error(f"Error creating resume from scratch: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return f"❌ Sorry, I encountered an error while creating your resume: {str(e)}."