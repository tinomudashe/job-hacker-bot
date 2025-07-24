import logging
from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models_db import Resume, User
from app.orchestrator.education_input import ResumeData

log = logging.getLogger(__name__)

async def get_or_create_resume(db: AsyncSession, user: User) -> Union[Resume, str]:
    """
    Retrieves the user's resume from the database. If it doesn't exist,
    it creates a new one with a default structure.
    """
    if not db or not user:
        return "Database session or user not provided. Cannot access resume."

    try:
        user_id = user.id
        result = await db.execute(select(Resume).where(Resume.user_id == user_id))
        resume = result.scalar_one_or_none()

        if resume:
            log.info(f"Found existing resume for user {user_id}")
            return resume
        else:
            log.info(f"No resume found for user {user_id}. Creating a new one.")
            new_resume_data = ResumeData(
                personal_info=None,
                work_experience=[],
                education=[],
                skills=[],
                certifications=[],
                projects=[]
            ).model_dump(exclude_none=True)

            new_resume = Resume(
                user_id=user_id,
                data=new_resume_data
            )
            db.add(new_resume)
            await db.commit()
            await db.refresh(new_resume)
            log.info(f"Successfully created new resume for user {user_id}")
            return new_resume
            
    except Exception as e:
        log.error(f"Error getting or creating resume for user {user.id}: {e}", exc_info=True)
        await db.rollback()
        return f"An unexpected error occurred while accessing the resume: {e}"