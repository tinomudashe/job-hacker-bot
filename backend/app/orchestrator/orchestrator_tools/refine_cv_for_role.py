import logging
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models_db import User, Resume
from app.resume import ResumeData
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class RefineCVInput(BaseModel):
    target_role: str = Field(description="The specific job title or role the user is targeting, e.g., 'Software Engineer'.")
    job_description: Optional[str] = Field(default="", description="The full job description for the target role.")
    company_name: Optional[str] = Field(default="", description="The name of the company.")

# Step 2: Define the core logic as a plain async function.
async def _refine_cv_for_role(
    db: AsyncSession,
    user: User,
    target_role: str,
    job_description: str = "",
    company_name: str = ""
) -> str:
    """The underlying implementation for refining a user's CV for a specific role."""
    try:
        log.info(f"CV refinement requested for role: {target_role}")
        
        db_resume, base_resume_data = await get_or_create_resume(db, user)
        
        parser = PydanticOutputParser(pydantic_object=ResumeData)
        
        prompt = PromptTemplate(
            template="""You are an expert career coach and resume writer. Your task is to refine a user's resume and return it as a structured JSON object.
            
            USER'S CURRENT RESUME DATA:
            {context}

            TARGET ROLE: {target_role}
            COMPANY: {company_name}
            JOB DESCRIPTION: {job_description}

            **CRITICAL, NON-NEGOTIABLE DIRECTIVE:**
            - **You MUST ONLY use the information provided in the 'USER'S CURRENT RESUME DATA' section.**
            - **You are STRICTLY FORBIDDEN from inventing, creating, or hallucinating any new information.**
            - Your ONLY task is to REFORMAT, REPHRASE, and TAILOR the *existing* information to better match the target role.
            - If a section is empty in the user's data, it should remain empty.
            - Return ONLY a valid JSON object matching the provided schema. Do not add any extra text or formatting.

            {format_instructions}
            """,
            input_variables=["context", "target_role", "company_name", "job_description"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        # Use the user-specified Gemini Pro model.
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.3)
        chain = prompt | llm | parser
        
        refined_resume_data = await chain.ainvoke({
            "context": base_resume_data.json(),
            "target_role": target_role,
            "company_name": company_name or "target companies",
            "job_description": job_description or f"General {target_role} position requirements",
        })
        
        db_resume.data = refined_resume_data.dict()
        attributes.flag_modified(db_resume, "data")
        await db.commit()
        
        return (f"I've successfully refined your CV for the **{target_role}** role. "
                "A download button will appear on this message. [DOWNLOADABLE_RESUME]")
        
    except Exception as e:
        log.error(f"Error in _refine_cv_for_role: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return f"❌ Sorry, an error occurred while refining your CV. Please try again."

# Step 3: Manually construct the Tool object with the explicit schema.
refine_cv_for_role = Tool(
    name="refine_cv_for_role",
    description="⭐ PRIMARY CV REFINEMENT TOOL ⭐ Refines a user's resume for a target role.",
    func=_refine_cv_for_role,
    args_schema=RefineCVInput
)