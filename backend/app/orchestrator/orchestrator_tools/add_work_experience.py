from typing import Optional, Dict
from langchain_core.tools import tool
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.orchestrator_models.resume_model import Experience, Dates

log = logging.getLogger(__name__)

def parse_date_range(date_range_str: str) -> Dict[str, Optional[str]]:
    """Parses a date range string into start and end dates."""
    parts = [p.strip() for p in date_range_str.split('-')]
    start_date = parts[0] if parts else None
    end_date = parts[1] if len(parts) > 1 else None
    return {"start_date": start_date, "end_date": end_date}

@tool
async def add_work_experience(
    job_title: str,
    company: str,
    start_date: str,
    end_date: Optional[str] = None,
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    description: str = "",
    achievements: Optional[str] = None,
    technologies_used: Optional[str] = None,
    is_current_job: bool = False,
    db: AsyncSession = None,
    user: User = None
) -> str:
    """
    Add comprehensive work experience entry to resume with detailed variables.
    
    Args:
        job_title: Position title (e.g., "Senior Software Engineer", "Marketing Manager")
        company: Company name (e.g., "Google", "Microsoft", "Startup Inc.")
        start_date: Start date (e.g., "January 2022", "2022-01", "Jan 2022")
        end_date: End date (e.g., "December 2023", "Present", "Current") - optional if current job
        location: Work location (e.g., "Warsaw, Poland", "Remote", "San Francisco, CA")
        employment_type: Type of employment (e.g., "Full-time", "Part-time", "Contract", "Internship")
        description: Main job responsibilities and duties
        achievements: Key achievements and accomplishments (optional)
        technologies_used: Technologies, tools, languages used (optional)
        is_current_job: True if this is current position (sets end_date to "Present")
    
    Returns:
        Success message with added experience details
    """
    if not db or not user:
        return "❌ Error: Database session and user must be provided to add work experience."

    try:
        db_resume, resume_data = await get_or_create_resume(db, user)

        if not resume_data:
            return "❌ Error: Could not find or create a resume for the user."

        # Format dates
        if is_current_job:
            end_date = "Present"
        
        date_range_str = f"{start_date} - {end_date}" if end_date else start_date
        parsed_dates = parse_date_range(date_range_str)
        
        # Build comprehensive description
        full_description = description
        if achievements:
            full_description += f"\n\nKey Achievements:\n{achievements}"
        if technologies_used:
            full_description += f"\n\nTechnologies: {technologies_used}"
        
        # Combine location and employment type into a single line for clarity
        meta_parts = []
        if location: meta_parts.append(f"Location: {location}")
        if employment_type: meta_parts.append(f"Type: {employment_type}")
        if meta_parts:
            full_description += "\n\n" + " | ".join(meta_parts)

        new_experience = Experience(
            id=str(uuid.uuid4()),
            jobTitle=job_title,
            company=company,
            dates=Dates(**parsed_dates),
            description=full_description.strip(),
        )

        if not hasattr(resume_data, 'experience') or resume_data.experience is None:
            resume_data.experience = []
            
        resume_data.experience.append(new_experience)

        db_resume.data = resume_data.dict()
        flag_modified(db_resume, "data")
        
        # --- COMMIT AND VERIFY ---
        await db.commit()
        await db.refresh(db_resume)
        
        added_experience = next((exp for exp in db_resume.data['experience'] if exp['id'] == new_experience.id), None)
        
        if added_experience and added_experience['jobTitle'] == new_experience.jobTitle:
            log.info(f"SUCCESSFULLY VERIFIED write for work experience: {new_experience.jobTitle}")
            return f"✅ Work experience for '{new_experience.jobTitle}' was successfully added and verified."
        else:
            raise Exception(f"DATABASE VERIFICATION FAILED for work experience: {new_experience.jobTitle}")
    
    except Exception as e:
        await db.rollback()
        log.error(f"Error adding work experience: {e}", exc_info=True)
        return f"❌ DATABASE ERROR: The attempt to add work experience failed. Details: {str(e)}"
