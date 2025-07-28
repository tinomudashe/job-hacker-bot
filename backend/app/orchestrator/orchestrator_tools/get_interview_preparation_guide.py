import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models_db import User, Resume
from app.resume import ResumeData, fix_resume_data_structure
from ._try_browser_extraction import _try_browser_extraction

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class InterviewPrepInput(BaseModel):
    job_title: str = Field(description="The job title for the interview.")
    company_name: Optional[str] = Field(default=None, description="The name of the company.")
    job_description_url: Optional[str] = Field(default=None, description="A URL to the job description.")

# Step 2: Define the core logic as a plain async function.
async def _get_interview_preparation_guide(
    db: AsyncSession,
    user: User,
    job_title: str,
    company_name: Optional[str] = None,
    job_description_url: Optional[str] = None,
) -> str:
    """The underlying implementation for providing a tailored interview preparation guide."""
    try:
        job_description = ""
        if job_description_url:
            success, extracted_data = await _try_browser_extraction(job_description_url)
            if success and extracted_data:
                job_title = extracted_data.get("job_title", job_title)
                company_name = extracted_data.get("company_name", company_name)
                job_description = extracted_data.get("job_description", "")

        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        user_context = f"User: {user.name}"
        if db_resume and db_resume.data:
            resume_data = ResumeData(**fix_resume_data_structure(db_resume.data))
            user_context += f"\nSummary: {resume_data.personalInfo.summary}\nSkills: {', '.join(resume_data.skills)}"

        prompt = ChatPromptTemplate.from_template(
            """You are an expert interview coach. Create a comprehensive, personalized interview preparation guide.

            USER CONTEXT: {user_context}
            TARGET ROLE: {job_title}
            COMPANY: {company_name}
            JOB DESCRIPTION: {job_description}

            Create a detailed guide covering role-specific questions, company research, and performance tips."""
        )
        
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.3)
        chain = prompt | llm | StrOutputParser()
        
        guide = await chain.ainvoke({
            "user_context": user_context, "job_title": job_title,
            "company_name": company_name or "the target company",
            "job_description": job_description or "Not specified"
        })
        
        return f"## Interview Guide: {job_title} at {company_name or 'Company'}**\n\n{guide}"

    except Exception as e:
        log.error(f"Error in _get_interview_preparation_guide: {e}", exc_info=True)
        return "❌ An error occurred while generating the interview guide."

# Step 3: Manually construct the Tool object with the explicit schema.
get_interview_preparation_guide = Tool(
    name="get_interview_preparation_guide",
    description="Provides a tailored interview preparation guide based on job details.",
    func=_get_interview_preparation_guide,
    args_schema=InterviewPrepInput
)
