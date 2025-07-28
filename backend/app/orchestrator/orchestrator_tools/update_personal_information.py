import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
# FIX: Import 'PersonalInfo' from the correct central model file.
from ..education_input import PersonalInfo

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class UpdatePersonalInfoInput(BaseModel):
    name: Optional[str] = Field(default=None, description="User's full name.")
    email: Optional[str] = Field(default=None, description="User's email address.")
    phone: Optional[str] = Field(default=None, description="User's phone number.")
    linkedin: Optional[str] = Field(default=None, description="URL of the user's LinkedIn profile.")
    location: Optional[str] = Field(default=None, description="User's city and country, e.g., 'San Francisco, USA'.")
    summary: Optional[str] = Field(default=None, description="A professional summary or headline.")

# Step 2: Define the core logic as a plain async function.
async def _update_personal_information(db: AsyncSession, user: User, **kwargs) -> str:
    """The underlying implementation for updating the personal information section of the user's resume."""
    try:
        db_resume, resume_data = await get_or_create_resume(db=db, user=user)
        
        if isinstance(resume_data, str): # Error case
            return resume_data

        if not resume_data.personal_info:
            resume_data.personal_info = PersonalInfo()

        updated_fields = []
        for field, value in kwargs.items():
            if value is not None:
                setattr(resume_data.personal_info, field, value)
                updated_fields.append(field)

        if not updated_fields:
            return "No information was provided to update."

        db_resume.data = resume_data.model_dump(exclude_none=True)
        attributes.flag_modified(db_resume, "data")
        await db.commit()

        return f"✅ Personal information updated for: {', '.join(updated_fields)}."
    except Exception as e:
        log.error(f"Error in _update_personal_information for user {user.id}: {e}", exc_info=True)
        await db.rollback()
        return f"❌ An error occurred while updating personal information: {e}"

# Step 3: Manually construct the Tool object with the explicit schema.
update_personal_information = Tool(
    name="update_personal_information",
    description="Updates the user's personal information (name, email, phone, location, etc.) on their resume.",
    func=_update_personal_information,
    args_schema=UpdatePersonalInfoInput
)