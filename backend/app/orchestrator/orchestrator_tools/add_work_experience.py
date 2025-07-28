import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
import uuid

from app.models_db import User, Resume
from .get_or_create_resume import get_or_create_resume
# FIX: Import 'Experience' and 'Dates' from the correct model file.
from ..work_experience_input import Experience, Dates
from sqlalchemy.orm.attributes import flag_modified

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class AddWorkExperienceInput(BaseModel):
    """Input model for adding a work experience to the resume."""
    company: str = Field(description="The name of the company where the user worked.")
    role: str = Field(description="The user's job title or role at the company.")
    start_date: str = Field(description="The start date of the employment, e.g., 'YYYY-MM-DD' or 'Month YYYY'.")
    end_date: Optional[str] = Field(default=None, description="The end date of the employment. Can be 'Present' or a date.")
    responsibilities: Optional[List[str]] = Field(default=None, description="A list of key responsibilities or achievements in the role.")
    location: Optional[str] = Field(default=None, description="The location of the job, e.g., 'San Francisco, CA'.")

def parse_date_range(start_date: str, end_date: Optional[str]) -> Dates:
    """Parses start and end dates into a Dates object."""
    return Dates(start_date=start_date, end_date=end_date or "Present")

# Step 2: Define the core logic as a plain async function.
async def _add_work_experience(
    db: AsyncSession,
    user: User,
    company: str,
    role: str,
    start_date: str,
    end_date: Optional[str] = None,
    responsibilities: Optional[List[str]] = None,
    location: Optional[str] = None,
) -> str:
    """The underlying implementation for adding a new work experience to the user's resume."""
    if not db or not user:
        return "Database session or user not provided. Cannot add work experience."

    try:
        resume, _ = await get_or_create_resume(db, user)
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

        # Ensure resume.data is a mutable dictionary
        if resume.data is None:
            resume.data = {}
        
        if "work_experience" not in resume.data:
            resume.data["work_experience"] = []

        # Use .append for list operations
        resume.data["work_experience"].append(new_experience.model_dump())
        
        flag_modified(resume, "data")
        
        await db.commit()
        await db.refresh(resume)

        return f"Successfully added work experience at {company} to your resume."

    except Exception as e:
        log.error(f"Error adding work experience for user {user.id}: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return f"An unexpected error occurred while adding work experience: {e}"

# Step 3: Manually construct the Tool object with the explicit schema.
add_work_experience = Tool(
    name="add_work_experience",
    description="Adds a new work experience to the user's resume.",
    func=_add_work_experience,
    args_schema=AddWorkExperienceInput
)
