from typing import Optional
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
import logging
from pydantic import BaseModel, Field

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.education_input import ResumeData

log = logging.getLogger(__name__)

class UpdateUserProfileInput(BaseModel):
    """Input model for updating the user's profile."""
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Full address or location")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    profile_headline: Optional[str] = Field(None, description="Professional headline or summary")
    skills: Optional[str] = Field(None, description="Comma-separated list of skills")

@tool(args_schema=UpdateUserProfileInput)
async def update_user_profile(
    db: AsyncSession,
    user: User,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    linkedin: Optional[str] = None,
    profile_headline: Optional[str] = None,
    skills: Optional[str] = None
) -> str:
    """
    Update comprehensive user profile information and synchronize it with their resume.
    """
    try:
        updated_fields = []
        
        # Update user profile fields directly on the passed 'user' object
        if first_name is not None:
            user.first_name = first_name
            updated_fields.append(f"First name: {first_name}")
        if last_name is not None:
            user.last_name = last_name
            updated_fields.append(f"Last name: {last_name}")
        if phone is not None:
            user.phone = phone
            updated_fields.append(f"Phone: {phone}")
        if address is not None:
            user.address = address
            updated_fields.append(f"Address: {address}")
        if linkedin is not None:
            user.linkedin = linkedin
            updated_fields.append(f"LinkedIn: {linkedin}")
        if profile_headline is not None:
            user.profile_headline = profile_headline
            updated_fields.append(f"Headline: {profile_headline}")
        if skills is not None:
            user.skills = skills
            updated_fields.append(f"Skills: {skills}")
        
        if first_name or last_name:
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if full_name:
                user.name = full_name
                updated_fields.append(f"Full name: {full_name}")
        
        # Synchronize with resume data
        db_resume, resume_data = await get_or_create_resume(db, user)
        if isinstance(db_resume, str):
             return db_resume

        # Ensure personalInfo exists
        if resume_data.personal_info is None:
            resume_data.personal_info = {}

        if first_name or last_name:
            resume_data.personal_info['name'] = user.name
        if user.email:
            resume_data.personal_info['email'] = user.email
        if phone:
            resume_data.personal_info['phone'] = phone
        if linkedin:
            resume_data.personal_info['linkedin'] = linkedin
        if address:
            resume_data.personal_info['location'] = address
        if profile_headline:
            resume_data.personal_info['summary'] = profile_headline
        
        if skills:
            resume_data.skills = [skill.strip() for skill in skills.split(",") if skill.strip()]
        
        # Save changes to both User and Resume
        db_resume.data = resume_data.model_dump()
        attributes.flag_modified(db_resume, "data")
        
        await db.commit()
        
        if updated_fields:
            return f"Profile updated successfully with the following fields:\n" + "\n".join(updated_fields)
        else:
            return "No changes were provided to update."
            
    except Exception as e:
        if db.in_transaction():
            await db.rollback()
        log.error(f"Error updating user profile: {e}", exc_info=True)
        return f"An error occurred while updating your profile: {e}"