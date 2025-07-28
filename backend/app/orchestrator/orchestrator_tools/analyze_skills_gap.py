import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models_db import Resume, User
from app.resume import ResumeData, fix_resume_data_structure

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class AnalyzeSkillsGapInput(BaseModel):
    """Input for analyzing the skills gap."""
    job_description: str = Field(description="The full text of the job description to compare against.")
    target_role: Optional[str] = Field(default="", description="The target role, if not clear from the description.")

# Step 2: Define the core logic as a plain async function.
async def _analyze_skills_gap(db: AsyncSession, user: User, job_description: str, target_role: str = "") -> str:
    """The underlying implementation for analyzing the user's skills gap against a job description."""
    try:
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        user_skills = ""
        if db_resume and db_resume.data:
            fixed_data = fix_resume_data_structure(db_resume.data)
            resume_data = ResumeData(**fixed_data)
            user_skills = ', '.join(resume_data.skills) if resume_data.skills else ""
        
        prompt = ChatPromptTemplate.from_template(
            """You are a career development expert. Analyze the skills gap between the user's current skills and the provided job description.

            CURRENT SKILLS: {current_skills}
            JOB DESCRIPTION: {job_description}

            Provide a comprehensive skills gap analysis, including strengths, areas for development, and a learning roadmap."""
        )
        
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7)
        chain = prompt | llm | StrOutputParser()
        
        analysis = await chain.ainvoke({
            "current_skills": user_skills or "No skills information provided",
            "job_description": job_description,
        })
        
        role_name = target_role or "the target role"
        return f"## 🔍 **Skills Gap Analysis for {role_name}**\n\n{analysis}"
        
    except Exception as e:
        log.error(f"Error in _analyze_skills_gap: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error during skills gap analysis: {str(e)}."

# Step 3: Manually construct the Tool object with the explicit schema.
analyze_skills_gap = Tool(
    name="analyze_skills_gap",
    description="Analyzes the user's skills from their resume against a job description to identify gaps.",
    func=_analyze_skills_gap,
    args_schema=AnalyzeSkillsGapInput
)