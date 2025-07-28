import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
# FIX: Import 'Education' and 'Dates' from the correct central model file.
from ..education_input import Education, Dates

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class AddEducationInput(BaseModel):
    """Input for adding an education entry to the user's resume."""
    institution: str = Field(description="The name of the educational institution.")
    degree: str = Field(description="The degree or field of study.")
    start_date: str = Field(description="The start date of the education, e.g., 'YYYY-MM-DD'.")
    end_date: Optional[str] = Field(default=None, description="The end date of the education. Can be 'Present' or a date.")
    gpa: Optional[float] = Field(default=None, description="The user's Grade Point Average.")

def parse_date_range(start_date: str, end_date: Optional[str]) -> Dates:
    """Parses a date range string into start and end dates."""
    return Dates(start_date=start_date, end_date=end_date or "Present")

# Step 2: Define the core logic as a plain async function.
async def _add_education(
    db: AsyncSession,
    user: User,
    institution: str,
    degree: str,
    start_date: str,
    end_date: Optional[str] = None,
    gpa: Optional[float] = None,
) -> str:
    """The underlying implementation for adding an education entry to the user's resume."""
    if not db or not user:
        return "❌ Error: Database session and user must be provided to add education."

    try:
        db_resume, resume_data = await get_or_create_resume(db, user)

        if not resume_data:
            return "❌ Error: Could not find or create a resume for the user."

        parsed_dates = parse_date_range(start_date, end_date)
        description_parts = []
        if gpa: description_parts.append(f"GPA: {gpa}")
        full_description = "\n".join(description_parts)

        new_education = Education(
            id=str(uuid.uuid4()),
            degree=degree,
            institution=institution,
            dates=parsed_dates,
            description=full_description
        )
                
        if not hasattr(resume_data, 'education') or resume_data.education is None:
            resume_data.education = []
                
        resume_data.education.append(new_education)

        db_resume.data = resume_data.dict()
        flag_modified(db_resume, "data")
        
        await db.commit()
        await db.refresh(db_resume)

        return f"✅ Education for '{new_education.degree}' was successfully added."
        
    except Exception as e:
        if db.in_transaction():
            await db.rollback()
        log.error(f"Error adding education: {e}", exc_info=True)
        return f"❌ DATABASE ERROR: The attempt to add education failed. Details: {str(e)}"

# Step 3: Manually construct the Tool object with the explicit schema.
add_education = Tool(
    name="add_education",
    description="Adds a comprehensive education entry to the user's resume.",
    func=_add_education,
    args_schema=AddEducationInput
)