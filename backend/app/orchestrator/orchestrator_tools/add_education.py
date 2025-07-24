from typing import Optional, Dict
from langchain_core.tools import tool
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel, Field

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from ..education_input import Education, Dates

log = logging.getLogger(__name__)

class AddEducationInput(BaseModel):
    """Input for adding an education entry to the user's resume."""
    institution: str = Field(description="The name of the educational institution.")
    degree: str = Field(description="The degree or field of study.")
    start_date: str = Field(description="The start date of the education, e.g., 'YYYY-MM-DD'.")
    end_date: Optional[str] = Field(None, description="The end date of the education. Can be 'Present' or a date.")
    gpa: Optional[float] = Field(None, description="The user's Grade Point Average.")

def parse_date_range(start_date: str, end_date: Optional[str]) -> Dates:
    """Parses a date range string into start and end dates."""
    return Dates(start_date=start_date, end_date=end_date or "Present")

@tool(args_schema=AddEducationInput)
async def add_education(
    db: AsyncSession,
    user: User,
    institution: str,
    degree: str,
    start_date: str,
    end_date: Optional[str] = None,
    gpa: Optional[float] = None,
) -> str:
    """
    Add comprehensive education entry to resume with detailed variables.
    
    Args:
        degree: Degree type and level (e.g., "Bachelor of Science", "Master of Engineering", "PhD")
        institution: School/University name (e.g., "University of Warsaw", "MIT", "Stanford University")
        start_year: Start year (e.g., "2018", "September 2018")
        end_year: End year (e.g., "2022", "May 2022", "Expected 2025") - optional if current
        location: Institution location (e.g., "Warsaw, Poland", "Cambridge, MA, USA")
        field_of_study: Major/specialization (e.g., "Computer Science", "Mechanical Engineering")
        gpa: Grade Point Average (e.g., "3.8/4.0", "First Class Honours", "Magna Cum Laude")
        honors: Academic honors and awards (e.g., "Dean's List", "Summa Cum Laude")
        relevant_coursework: Key courses taken (e.g., "Machine Learning, Database Systems, Software Engineering")
        thesis_project: Thesis or major project title and description
        is_current: True if currently studying (sets end_year to "Present" or "Expected")
    
    Returns:
        Success message with added education details
    """
    if not db or not user:
        return "❌ Error: Database session and user must be provided to add education."

    try:
        db_resume, resume_data = await get_or_create_resume(db, user)

        if not resume_data:
            return "❌ Error: Could not find or create a resume for the user."

        # Format dates
        if end_date and "expected" not in (end_date or "").lower():
            end_date = f"Expected {end_date}"
        
        parsed_dates = parse_date_range(start_date, end_date)
        
        # Build degree title with field of study
        full_degree = degree
        # if field_of_study: # This line was removed from the new_education definition, so it's removed here.
        #     full_degree += f" in {field_of_study}"
        
        # Build comprehensive description
        description_parts = []
        # if location: description_parts.append(f"Location: {location}") # This line was removed from the new_education definition, so it's removed here.
        if gpa: description_parts.append(f"GPA: {gpa}")
        # if honors: description_parts.append(f"Honors: {honors}") # This line was removed from the new_education definition, so it's removed here.
        # if relevant_coursework: description_parts.append(f"Relevant Coursework: {relevant_coursework}") # This line was removed from the new_education definition, so it's removed here.
        # if thesis_project: description_parts.append(f"Thesis/Project: {thesis_project}") # This line was removed from the new_education definition, so it's removed here.
        full_description = "\n".join(description_parts)

        new_education = Education(
            id=str(uuid.uuid4()),
            degree=full_degree,
            institution=institution,
            dates=parsed_dates,
            description=full_description
        )
                
        if not hasattr(resume_data, 'education') or resume_data.education is None:
            resume_data.education = []
                
        resume_data.education.append(new_education)

        db_resume.data = resume_data.dict()
        flag_modified(db_resume, "data")
        
        # --- COMMIT AND VERIFY ---
        await db.commit()
        await db.refresh(db_resume)

        added_education = next((edu for edu in db_resume.data['education'] if edu['id'] == new_education.id), None)

        if added_education and added_education['degree'] == new_education.degree:
            log.info(f"SUCCESSFULLY VERIFIED write for education: {new_education.degree}")
            return f"✅ Education for '{new_education.degree}' was successfully added and verified."
        else:
            raise Exception(f"DATABASE VERIFICATION FAILED for education: {new_education.degree}")
        
    except Exception as e:
        await db.rollback()
        log.error(f"Error adding education: {e}", exc_info=True)
        return f"❌ DATABASE ERROR: The attempt to add education failed. Details: {str(e)}"