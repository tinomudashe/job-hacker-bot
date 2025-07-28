import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import Resume, User

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class GeneratePDFInput(BaseModel):
    style: Optional[str] = Field(default="modern", description="PDF style theme - 'modern', 'classic', or 'minimal'.")

# Step 2: Define the core logic as a plain async function.
async def _generate_resume_pdf(
    style: str,
    db: AsyncSession,
    user: User
) -> str:
    """The underlying implementation for generating a PDF version of the user's resume."""
    try:
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        if not db_resume or not db_resume.data:
            return "❌ No resume data found. Please build your resume first."
        
        # The frontend handles the actual PDF generation. This tool's job is to
        # confirm that data exists and return the trigger for the UI.
        return "[DOWNLOADABLE_RESUME]\n\nYour resume is ready for download. A dialog should appear to select your preferred style."
        
    except Exception as e:
        log.error(f"Error in _generate_resume_pdf: {e}", exc_info=True)
        return f"❌ Sorry, an error occurred while preparing your resume PDF: {str(e)}."

# Step 3: Manually construct the Tool object with the explicit schema.
generate_resume_pdf = Tool(
    name="generate_resume_pdf",
    description="Prepares the user's resume for PDF download and triggers the download dialog on the frontend.",
    func=_generate_resume_pdf,
    args_schema=GeneratePDFInput
)