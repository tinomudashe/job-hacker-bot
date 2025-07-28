import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from langchain_core.tools import Tool

from app.models_db import Resume, User

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema (even if empty).
class ShowDownloadOptionsInput(BaseModel):
    pass

# Step 2: Define the core logic as a plain async function.
async def _show_resume_download_options(db: AsyncSession, user: User) -> str:
    """The underlying implementation for showing resume download options."""
    try:
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        if not db_resume or not db_resume.data:
            return "❌ **No Resume Found**: Please create your resume first using the resume-building tools."
        
        # This special string is a command for the frontend to open the PDF generation dialog.
        return "[DOWNLOADABLE_RESUME]\n\nYour resume is ready. A dialog should appear to select your preferred style and download the PDF."
        
    except Exception as e:
        log.error(f"Error in _show_resume_download_options for user {user.id}: {e}", exc_info=True)
        return f"❌ An error occurred while preparing your resume for download."

# Step 3: Manually construct the Tool object with the explicit schema.
show_resume_download_options = Tool(
    name="show_resume_download_options",
    description="Shows download options for the user's resume, triggering the PDF styling and generation dialog on the frontend.",
    func=_show_resume_download_options,
    args_schema=ShowDownloadOptionsInput
)