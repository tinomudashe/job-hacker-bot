from langchain_core.tools import tool
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Resume, User

log = logging.getLogger(__name__)

@tool
async def generate_resume_pdf(
    style: str,
    db: AsyncSession,
    user: User
) -> str:
    """Generate a professionally styled PDF version of your resume.
    
    Args:
        style: PDF style theme - "modern", "classic", or "minimal"
    
    Returns:
        Download links for the resume PDF in different styles
    """
    if style is None:
        style = "modern"
        
    try:
        # Check if user has resume data
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        if not db_resume:
            return "❌ No resume data found. Please add your personal information, experience, and skills first using the resume tools."
        
        return f"""[DOWNLOADABLE_RESUME]

## 📄 Resume PDF Ready

✅ **Your resume is ready for download!**

You can download your resume in multiple professional styles using the download dialog. Choose from Modern, Classic, or Minimal styles, edit content if needed, and preview before downloading.

**A download button (📥) should appear on this message to access all styling and editing options.**"""
        
    except Exception as e:
        log.error(f"Error generating resume PDF: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while preparing your resume PDF: {str(e)}. Please try again."