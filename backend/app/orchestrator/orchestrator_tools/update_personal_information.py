from typing import Optional
from langchain_core.tools import tool
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.orchestrator_models.resume_model import PersonalInfo

log = logging.getLogger(__name__)

@tool
async def update_personal_information(
    db: AsyncSession,
    user: User,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    linkedin: Optional[str] = None,
    location: Optional[str] = None,
    summary: Optional[str] = None
) -> str:
    """Updates the personal information part of the user's resume."""
    try:
        db_resume, resume_data = await get_or_create_resume(db=db, user=user)
        
        if not resume_data:
            return "❌ Error: Could not find or create a resume for the user."

        update_data = {
            "name": name, "email": email, "phone": phone, 
            "linkedin": linkedin, "location": location, "summary": summary
        }

        if not resume_data.personalInfo:
            resume_data.personalInfo = PersonalInfo()

        for field, value in update_data.items():
            if value is not None:
                setattr(resume_data.personalInfo, field, value)

        db_resume.data = resume_data.dict()
        flag_modified(db_resume, "data")
        await db.commit()
        return "✅ Personal information updated successfully."
    except Exception as e:
        await db.rollback()
        log.error(f"Error updating personal information: {e}")
        return f"❌ An error occurred while updating personal information: {e}"