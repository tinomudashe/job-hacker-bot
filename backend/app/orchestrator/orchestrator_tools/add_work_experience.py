import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import uuid

from app.models_db import User, Resume
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.work_experience_input import Experience, Dates
from sqlalchemy.orm.attributes import flag_modified

log = logging.getLogger(__name__)

# NEW: Explicitly define the input schema for the LLM
class AddWorkExperienceInput(BaseModel):
    """Input model for adding a work experience to the resume."""
    company: str = Field(description="The name of the company where the user worked.")
    role: str = Field(description="The user's job title or role at the company.")
    start_date: str = Field(description="The start date of the employment, e.g., 'YYYY-MM-DD' or 'Month YYYY'.")
    end_date: Optional[str] = Field(None, description="The end date of the employment. Can be 'Present' or a date.")
    responsibilities: Optional[List[str]] = Field(None, description="A list of key responsibilities or achievements in the role.")
    location: Optional[str] = Field(None, description="The location of the job, e.g., 'San Francisco, CA'.")

def parse_date_range(start_date: str, end_date: Optional[str]) -> Dates:
    """Parses start and end dates into a Dates object."""
    return Dates(start_date=start_date, end_date=end_date or "Present")

# UPDATED: Add the args_schema to the tool decorator
@tool(args_schema=AddWorkExperienceInput)
async def add_work_experience(
    db: AsyncSession,
    user: User,
    company: str,
    role: str,
    start_date: str,
    end_date: Optional[str] = None,
    responsibilities: Optional[List[str]] = None,
    location: Optional[str] = None,
) -> str:
    """Adds a new work experience to the user's resume, creating the resume if it doesn't exist."""
    
    # The rest of the function logic remains the same...
    if not db or not user:
        return "Database session or user not provided. Cannot add work experience."

    try:
        resume = await get_or_create_resume(db, user)
        if isinstance(resume, str):
            return resume

        new_experience = Experience(
            id=str(uuid.uuid4()),
            company=company,
            role=role,
            dates=parse_date_range(start_date, end_date),
            responsibilities=responsibilities or [],
            location=location or ""
        )

        if not resume.data:
            resume.data = {"work_experience": [], "education": [], "skills": [], "personal_info": {}}
        
        if "work_experience" not in resume.data:
            resume.data["work_experience"] = []

        resume.data["work_experience"].append(new_experience.model_dump())
        
        flag_modified(resume, "data")
        
        await db.commit()
        await db.refresh(resume)

        # Verification step
        updated_experience = next((exp for exp in resume.data.get("work_experience", []) if exp['id'] == new_experience.id), None)
        
        if updated_experience:
            log.info(f"Successfully added and verified work experience for user {user.id}")
            return f"Successfully added work experience at {company} to your resume."
        else:
            log.error(f"Verification failed after adding work experience for user {user.id}")
            await db.rollback()
            return "Failed to add work experience due to a verification error. The change has been rolled back."

    except Exception as e:
        log.error(f"Error adding work experience for user {user.id}: {e}", exc_info=True)
        await db.rollback()
        return f"An unexpected error occurred while adding work experience: {e}"
