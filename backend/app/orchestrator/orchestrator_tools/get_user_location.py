from langchain_core.tools import tool
import logging
log = logging.getLogger(__name__)

from app.models.user import User
from app.database import db
from app.orchestrator import get_or_create_resume
from app.tools.get_user_location_context import get_user_location_context



from app.orchestrator import async_session_maker

@tool
async def update_user_location(
        location: str
    ) -> str:
        """
        Update the user's location in their profile.
        
        Args:
            location: New location (e.g., "Warsaw, Poland", "Berlin, Germany", "Remote")
        
        Returns:
            Success message with updated location context
        """
        try:
            # Update user's address field
            user.address = location.strip()
            
            # Also update resume data for consistency
            db_resume, resume_data = await get_or_create_resume()
            resume_data.personalInfo.location = location.strip()
            db_resume.data = resume_data.dict()
            
            await db.commit()
            
            # Get updated location context
            updated_context = await get_user_location_context()
            
            return f"""✅ **Location Updated Successfully!**

**New Location:** {location}

{updated_context}

**📄 Profile Sync:** Your resume and profile have been updated with the new location."""
            
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error updating user location: {e}")
            return f"❌ Error updating location: {str(e)}"
