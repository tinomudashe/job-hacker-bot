from langchain_core.tools import tool
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Resume, User

log = logging.getLogger(__name__)

@tool
async def show_resume_download_options(db: AsyncSession, user: User) -> str:
    """Show download options for the user's resume with PDF styling choices.
    
    Returns:
        Professional resume download interface with multiple PDF styles
    """
    try:
        # Check if user has resume data
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        if not db_resume:
            return "❌ **No Resume Found**\n\nPlease create your resume first by adding:\n- Personal information\n- Work experience\n- Education\n- Skills\n\nUse the resume tools to build your professional resume!"
        
        return f"""[DOWNLOADABLE_RESUME]

## 📄 **CV/Resume Ready for Download**

✅ **Your CV/Resume is ready for download!**

You can download your CV/Resume in multiple professional styles. The download dialog will let you:

- **Choose from 3 professional styles** (Modern, Classic, Minimal)
- **Edit content** before downloading if needed
- **Preview** your CV/Resume before downloading
- **Download all styles** at once

**A download button (📥) should appear on this message to access all options.**"""
        
    except Exception as e:
        log.error(f"Error showing resume download options: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while preparing your resume download options: {str(e)}. Please try again."