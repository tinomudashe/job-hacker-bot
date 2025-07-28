import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import User
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class SetSkillsInput(BaseModel):
    skills: List[str] = Field(description="A list of skills to set for the user, replacing any existing skills.")

# Step 2: Define the core logic as a plain async function.
async def _set_skills(skills: List[str], db: AsyncSession, user: User) -> str:
    """The underlying implementation for replacing the user's skills list."""
    try:
        db_resume, resume_data = await get_or_create_resume(db=db, user=user)
        if isinstance(resume_data, str): # Error case
            return resume_data
            
        # Standardize by removing whitespace and duplicates
        standardized_skills = sorted(list(set([skill.strip() for skill in skills if skill.strip()])))
        
        resume_data.skills = standardized_skills
        db_resume.data = resume_data.model_dump(exclude_none=True)
        attributes.flag_modified(db_resume, "data")
        
        await db.commit()

        log.info(f"Successfully set {len(standardized_skills)} skills for user {user.id}")
        return f"✅ Your skills list has been updated with {len(standardized_skills)} skills."

    except Exception as e:
        log.error(f"Error in _set_skills for user {user.id}: {e}", exc_info=True)
        await db.rollback()
        return f"❌ An error occurred while setting your skills: {e}"

# Step 3: Manually construct the Tool object with the explicit schema.
set_skills = Tool(
    name="set_skills",
    description="Replaces the entire skills list in the user's resume with the provided list.",
    func=_set_skills,
    args_schema=SetSkillsInput
)