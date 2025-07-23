from typing import List
from langchain_core.tools import tool
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_db import User
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

@tool
async def set_skills(skills: List[str], db: AsyncSession, user: User) -> str:
    """Replaces the entire skills list with the provided list of skills."""
    try:
        db_resume, resume_data = await get_or_create_resume(db=db, user=user)
        if not resume_data:
            return "❌ DATABASE ERROR: Could not find or create a resume."
            
        resume_data.skills = skills
        db_resume.data = resume_data.dict()
        flag_modified(db_resume, "data")
        
        # --- COMMIT AND VERIFY ---
        await db.commit()
        await db.refresh(db_resume)

        if db_resume.data['skills'] == skills:
            log.info(f"SUCCESSFULLY VERIFIED write for user {user.id}'s skills.")
            return "✅ Skills were successfully updated and verified in the database."
        else:
            raise Exception("DATABASE VERIFICATION FAILED for skills update.")

    except Exception as e:
        await db.rollback()
        log.error(f"Error setting skills: {e}")
        return f"❌ DATABASE ERROR: The attempt to set skills failed. Details: {str(e)}"