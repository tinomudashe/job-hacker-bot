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
class CareerPlanInput(BaseModel):
    current_role: str = Field(description="The user's current job role or title.")
    target_role: str = Field(description="The desired future job role or title.")
    timeframe_years: int = Field(default=5, description="The timeframe in years for the career plan.")

# Step 2: Define the core logic as a plain async function.
async def _create_career_development_plan(
    db: AsyncSession,
    user: User,
    current_role: str,
    target_role: str,
    timeframe_years: int = 5,
) -> str:
    """The underlying implementation for creating a comprehensive career development plan."""
    try:
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        user_context = f"User: {user.name}"
        if db_resume and db_resume.data:
            fixed_data = fix_resume_data_structure(db_resume.data)
            resume_data = ResumeData(**fixed_data)
            user_context += f"\nSkills: {', '.join(resume_data.skills[:10]) if resume_data.skills else 'Not listed'}"

        prompt = ChatPromptTemplate.from_template(
            """You are a senior career strategist. Create a comprehensive, actionable career development plan.

            USER CONTEXT: {user_context}
            CURRENT ROLE: {current_role}
            TARGET ROLE: {target_role}
            TIMELINE: {timeline} years

            Create a detailed career development roadmap covering vision, milestones, learning strategy, networking, and progress tracking."""
        )
        
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7)
        chain = prompt | llm | StrOutputParser()
        
        plan = await chain.ainvoke({
            "user_context": user_context,
            "current_role": current_role,
            "target_role": target_role,
            "timeline": timeframe_years,
        })
        
        return f"## 🚀 **Career Development Plan: {current_role} → {target_role}**\n\n{plan}"
        
    except Exception as e:
        log.error(f"Error in _create_career_development_plan: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while creating your career plan: {str(e)}."

# Step 3: Manually construct the Tool object with the explicit schema.
create_career_development_plan = Tool(
    name="create_career_development_plan",
    description="Create a comprehensive career development plan with specific steps and milestones.",
    func=_create_career_development_plan,
    args_schema=CareerPlanInput
)