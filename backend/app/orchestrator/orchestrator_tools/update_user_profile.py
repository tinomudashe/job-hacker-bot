from typing import Optional
from langchain_core.tools import tool
from app.models.resume import get_or_create_resume
from app.database import db
import logging

log = logging.getLogger(__name__)   

from app.models.user import User

@tool
async def update_user_profile(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        linkedin: Optional[str] = None,
        preferred_language: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        profile_headline: Optional[str] = None,
        skills: Optional[str] = None
    ) -> str:
        """
        Update comprehensive user profile information in database.
        
        This tool updates the main user profile AND synchronizes with resume data.
        Use this for complete profile updates with exact field variables.
        
        Args:
            first_name: User's first name
            last_name: User's last name  
            phone: Phone number (e.g., "+48 123 456 789")
            address: Full address or location (e.g., "Warsaw, Poland")
            linkedin: LinkedIn profile URL (e.g., "https://linkedin.com/in/username")
            preferred_language: Preferred language (e.g., "English", "Polish")
            date_of_birth: Date of birth (e.g., "1990-01-15")
            profile_headline: Professional headline/summary
            skills: Comma-separated skills (e.g., "Python, React, AWS, Docker")
        
        Returns:
            Success message with updated fields
        """
        try:
            updated_fields = []
            
            # Update user profile fields
            if first_name is not None:
                user.first_name = first_name
                updated_fields.append(f"First name: {first_name}")
            
            if last_name is not None:
                user.last_name = last_name
                updated_fields.append(f"Last name: {last_name}")
            
            if phone is not None:
                user.phone = phone
                updated_fields.append(f"Phone: {phone}")
                
            if address is not None:
                user.address = address
                updated_fields.append(f"Address: {address}")
                
            if linkedin is not None:
                user.linkedin = linkedin
                updated_fields.append(f"LinkedIn: {linkedin}")
                
            if preferred_language is not None:
                user.preferred_language = preferred_language
                updated_fields.append(f"Language: {preferred_language}")
                
            if date_of_birth is not None:
                user.date_of_birth = date_of_birth
                updated_fields.append(f"Date of birth: {date_of_birth}")
                
            if profile_headline is not None:
                user.profile_headline = profile_headline
                updated_fields.append(f"Headline: {profile_headline}")
                
            if skills is not None:
                user.skills = skills
                updated_fields.append(f"Skills: {skills}")
            
            # Also update the user's name field for consistency
            if first_name or last_name:
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                if full_name:
                    user.name = full_name
                    updated_fields.append(f"Full name: {full_name}")
            
            # Synchronize with resume data
            db_resume, resume_data = await get_or_create_resume()
            
            # Update resume personal info to match profile
            if first_name or last_name:
                resume_data.personalInfo.name = user.name
            if user.email:
                resume_data.personalInfo.email = user.email
            if phone:
                resume_data.personalInfo.phone = phone
            if linkedin:
                resume_data.personalInfo.linkedin = linkedin
            if address:
                resume_data.personalInfo.location = address
            if profile_headline:
                resume_data.personalInfo.summary = profile_headline
            
            # Update skills in resume if provided
            if skills:
                skills_list = [skill.strip() for skill in skills.split(",") if skill.strip()]
                resume_data.skills = skills_list
            
            # Save changes
            db_resume.data = resume_data.dict()
            await db.commit()
            
            if updated_fields:
                return f"✅ **Profile Updated Successfully!**\n\nUpdated fields:\n" + "\n".join(f"• {field}" for field in updated_fields)
            else:
                return "ℹ️ No changes provided. Please specify which fields to update."
                
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error updating user profile: {e}")
            return f"❌ Error updating profile: {str(e)}"