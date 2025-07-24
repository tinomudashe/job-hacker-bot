from typing import Optional
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
import logging
from pydantic import BaseModel, Field

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.education_input import ResumeData, PersonalInfo

log = logging.getLogger(__name__)

class UpdateUserProfileComprehensiveInput(BaseModel):
    """Input model for the comprehensive user profile update tool."""
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Full address or location")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    profile_headline: Optional[str] = Field(None, description="Professional headline or summary")
    skills: Optional[str] = Field(None, description="Comma-separated list of skills")
    email: Optional[str] = Field(None, description="User's email address")

@tool(args_schema=UpdateUserProfileComprehensiveInput)
async def update_user_profile_comprehensive(
    db: AsyncSession,
    user: User,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    linkedin: Optional[str] = None,
    profile_headline: Optional[str] = None,
    skills: Optional[str] = None,
    email: Optional[str] = None
) -> str:
    """🔧 COMPREHENSIVE PROFILE UPDATE: Updates user profile and resume data for consistency."""
    try:
        updated_fields = []
        
        # 1. Update User Profile in Database
        if first_name is not None:
            user.first_name = first_name.strip()
            updated_fields.append(f"First name: {user.first_name}")
        if last_name is not None:
            user.last_name = last_name.strip()
            updated_fields.append(f"Last name: {user.last_name}")
        if phone is not None:
            user.phone = phone.strip()
            updated_fields.append(f"Phone: {user.phone}")
        if address is not None:
            user.address = address.strip()
            updated_fields.append(f"Address: {user.address}")
        if linkedin is not None:
            user.linkedin = linkedin.strip()
            updated_fields.append(f"LinkedIn: {user.linkedin}")
        if profile_headline is not None:
            user.profile_headline = profile_headline.strip()
            updated_fields.append(f"Headline: {user.profile_headline}")
        if skills is not None:
            user.skills = skills.strip()
            updated_fields.append(f"Skills: {user.skills}")
        if email is not None:
            user.email = email.strip()
            updated_fields.append(f"Email: {user.email}")
        
        # 2. Update Resume Data Structure
        db_resume, resume_data = await get_or_create_resume(db, user)
        if isinstance(db_resume, str):
            return db_resume

        if resume_data.personal_info is None:
            resume_data.personal_info = PersonalInfo()

        # Map profile fields to resume personal info
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if full_name: resume_data.personal_info.name = full_name
        if user.email: resume_data.personal_info.email = user.email
        if user.phone: resume_data.personal_info.phone = user.phone
        if user.address: resume_data.personal_info.location = user.address
        if user.linkedin: resume_data.personal_info.linkedin = user.linkedin
        if user.profile_headline: resume_data.personal_info.summary = user.profile_headline
        if user.skills:
            resume_data.skills = [skill.strip() for skill in user.skills.split(',') if skill.strip()]
        
        # 3. Commit all changes
        db_resume.data = resume_data.model_dump()
        attributes.flag_modified(db_resume, "data")
        await db.commit()
        
        if not updated_fields:
            return "No profile updates were provided."
        
        return "Profile updated successfully:\n" + "\n".join(updated_fields)
        
    except Exception as e:
        if db.in_transaction():
            await db.rollback()
        log.error(f"Error updating user profile comprehensively: {e}", exc_info=True)
        return f"An error occurred while updating your profile: {e}"