import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import User
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class ManageSkillsInput(BaseModel):
    skills_to_add: Optional[List[str]] = Field(default=None, description="A list of skills to add to the resume.")
    skills_to_remove: Optional[List[str]] = Field(default=None, description="A list of skills to remove from the resume.")
    replace_all_skills: Optional[List[str]] = Field(default=None, description="A new list of skills that will completely replace the existing skills.")

# Step 2: Define the core logic as a plain async function.
async def _manage_skills_comprehensive(
    db: AsyncSession,
    user: User,
    skills_to_add: Optional[List[str]] = None,
    skills_to_remove: Optional[List[str]] = None,
    replace_all_skills: Optional[List[str]] = None
) -> str:
    """The underlying implementation for comprehensively managing the user's skills list."""
    try:
        db_resume, resume_data = await get_or_create_resume(db, user)
        if isinstance(resume_data, str): # Error case
            return resume_data
        
        # Ensure skills list exists and is a set for efficient operations
        current_skills = set(resume_data.skills or [])
        actions_taken = []

        if replace_all_skills is not None:
            current_skills = {skill.strip() for skill in replace_all_skills if skill.strip()}
            actions_taken.append(f"Replaced all skills with {len(current_skills)} new skills.")
        else:
            if skills_to_add:
                added_count = len(current_skills)
                current_skills.update({skill.strip() for skill in skills_to_add if skill.strip()})
                actions_taken.append(f"Added {len(current_skills) - added_count} new skills.")
            
            if skills_to_remove:
                removed_count = len(current_skills)
                current_skills.difference_update({skill.strip() for skill in skills_to_remove if skill.strip()})
                actions_taken.append(f"Removed {removed_count - len(current_skills)} skills.")

        if not actions_taken:
            return "No skill management actions were specified. Please provide skills to add, remove, or replace."

        # Update both resume data and user profile skills for consistency
        sorted_skills = sorted(list(current_skills))
        resume_data.skills = sorted_skills
        user.skills = ", ".join(sorted_skills) # Sync with the user model

        db_resume.data = resume_data.model_dump(exclude_none=True)
        attributes.flag_modified(db_resume, "data")
        
        await db.commit()

        log.info(f"Successfully managed skills for user {user.id}: {', '.join(actions_taken)}")
        return f"✅ Skills updated successfully: {', '.join(actions_taken)}"

    except Exception as e:
        log.error(f"Error in _manage_skills_comprehensive for user {user.id}: {e}", exc_info=True)
        await db.rollback()
        return f"❌ An error occurred while managing your skills: {e}"

# Step 3: Manually construct the Tool object with the explicit schema.
manage_skills_comprehensive = Tool(
    name="manage_skills_comprehensive",
    description="Manages the user's skills list by adding, removing, or replacing skills.",
    func=_manage_skills_comprehensive,
    args_schema=ManageSkillsInput
)