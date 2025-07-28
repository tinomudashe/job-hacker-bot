import logging
from typing import Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models_db import Resume, User
from app.orchestrator.education_input import ResumeData, PersonalInfo

log = logging.getLogger(__name__)

async def get_or_create_resume(db: AsyncSession, user: User) -> Tuple[Union[Resume, None], Union[ResumeData, str]]:
    """
    Retrieves the user's resume from the database. If it doesn't exist,
    it creates a new one with a default structure.
    Returns both the database object and the parsed Pydantic model.
    """
    if not db or not user:
        return None, "Database session or user not provided. Cannot access resume."

    try:
        user_id = user.id
        result = await db.execute(select(Resume).where(Resume.user_id == user_id))
        resume = result.scalar_one_or_none()

        if resume:
            log.info(f"Found existing resume for user {user_id}")
            # Ensure data is not None before parsing
            resume_data = ResumeData(**resume.data) if resume.data else ResumeData()
            return resume, resume_data
        else:
            log.info(f"No resume found for user {user_id}. Creating a new one.")
            # Create a default structure with a PersonalInfo object
            new_resume_data = ResumeData(
                personal_info=PersonalInfo(name=user.name or ""),
                work_experience=[],
                education=[],
                skills=[s.strip() for s in user.skills.split(',')] if user.skills else [],
                certifications=[],
                projects=[]
            )

            new_resume = Resume(
                user_id=user_id,
                data=new_resume_data.model_dump(exclude_none=True)
            )
            db.add(new_resume)
            # No commit here; let the calling tool manage the transaction.
            await db.flush()
            await db.refresh(new_resume)
            log.info(f"Successfully created new resume object for user {user_id}")
            return new_resume, new_resume_data
            
    except Exception as e:
        log.error(f"Error in get_or_create_resume for user {user.id}: {e}", exc_info=True)
        # No rollback here either, handled by the calling tool.
        return None, f"An unexpected error occurred while accessing the resume: {e}"