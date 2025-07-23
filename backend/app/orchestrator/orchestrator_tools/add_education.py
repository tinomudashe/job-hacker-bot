from typing import Optional, Dict
from langchain_core.tools import tool
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from ..education_input import Education, Dates

log = logging.getLogger(__name__)

def parse_date_range(date_range_str: str) -> Dict[str, Optional[str]]:
    """Parses a date range string into start and end dates."""
    parts = [p.strip() for p in date_range_str.split('-')]
    start_date = parts[0] if parts else None
    end_date = parts[1] if len(parts) > 1 else None
    return {"start_date": start_date, "end_date": end_date}

@tool
async def add_education(
    degree: str,
    institution: str,
    start_year: str,
    end_year: Optional[str] = None,
    location: Optional[str] = None,
    field_of_study: Optional[str] = None,
    gpa: Optional[str] = None,
    honors: Optional[str] = None,
    relevant_coursework: Optional[str] = None,
    thesis_project: Optional[str] = None,
    is_current: bool = False,
    db: AsyncSession = None,
    user: User = None
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
        if is_current:
            if "expected" not in (end_year or "").lower():
                end_year = f"Expected {end_year}" if end_year else "Present"
        
        date_range_str = f"{start_year} - {end_year}" if end_year else start_year
        parsed_dates = parse_date_range(date_range_str)
        
        # Build degree title with field of study
        full_degree = degree
        if field_of_study:
            full_degree += f" in {field_of_study}"
        
        # Build comprehensive description
        description_parts = []
        if location: description_parts.append(f"Location: {location}")
        if gpa: description_parts.append(f"GPA: {gpa}")
        if honors: description_parts.append(f"Honors: {honors}")
        if relevant_coursework: description_parts.append(f"Relevant Coursework: {relevant_coursework}")
        if thesis_project: description_parts.append(f"Thesis/Project: {thesis_project}")
        full_description = "\n".join(description_parts)

        new_education = Education(
            id=str(uuid.uuid4()),
            degree=full_degree,
            institution=institution,
            dates=Dates(**parsed_dates),
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