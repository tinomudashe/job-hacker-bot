import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.education_input import PersonalInfo

log = logging.getLogger(__name__)

# This tool is functionally identical to update_user_profile_comprehensive.
# We will keep the schema and function for backward compatibility with the agent if needed,
# but the implementation will be a simplified pass-through.
# The 'comprehensive' tool should be preferred.

# Step 1: Define the explicit Pydantic input schema.
class UpdateUserProfileInput(BaseModel):
    first_name: Optional[str] = Field(default=None, description="User's first name")
    last_name: Optional[str] = Field(default=None, description="User's last name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    address: Optional[str] = Field(default=None, description="Full address or location")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    profile_headline: Optional[str] = Field(default=None, description="Professional headline or summary")
    skills: Optional[str] = Field(default=None, description="Comma-separated list of skills")

# Step 2: Define the core logic as a plain async function.
async def _update_user_profile(db: AsyncSession, user: User, **kwargs) -> str:
    """The underlying implementation for updating user profile and resume data."""
    try:
        updated_fields = []
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value.strip())
                updated_fields.append(f"{key.replace('_', ' ').title()}: {value.strip()}")

        if not updated_fields:
            return "No profile information was provided to update."

        db_resume, resume_data = await get_or_create_resume(db, user)
        if isinstance(db_resume, str):
            return db_resume

        if resume_data.personal_info is None:
            resume_data.personal_info = PersonalInfo()

        # Sync user model to resume data model
        resume_data.personal_info.name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        resume_data.personal_info.email = user.email
        resume_data.personal_info.phone = user.phone
        resume_data.personal_info.location = user.address
        resume_data.personal_info.linkedin = user.linkedin
        resume_data.personal_info.summary = user.profile_headline
        if user.skills:
            resume_data.skills = [s.strip() for s in user.skills.split(',') if s.strip()]
        
        db_resume.data = resume_data.model_dump()
        attributes.flag_modified(db_resume, "data")
        
        await db.commit()
        
        return "✅ Profile updated successfully:\n" + "\n".join(updated_fields)
        
    except Exception as e:
        log.error(f"Error in _update_user_profile: {e}", exc_info=True)
        await db.rollback()
        return f"❌ An error occurred while updating your profile: {e}"

# Step 3: Manually construct the Tool object with the explicit schema.
update_user_profile = Tool(
    name="update_user_profile",
    description="Updates user profile and resume personal data. Use 'update_user_profile_comprehensive' for a more robust option.",
    func=lambda **kwargs: _update_user_profile(**kwargs),
    args_schema=UpdateUserProfileInput
)