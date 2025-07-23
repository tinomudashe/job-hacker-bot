from typing import Optional
from langchain_core.tools import tool
from app.models.resume import get_or_create_resume
from app.database import db
import logging
log = logging.getLogger(__name__)

@tool
async def update_user_profile_comprehensive(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        linkedin: Optional[str] = None,
        preferred_language: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        profile_headline: Optional[str] = None,
        skills: Optional[str] = None,
        email: Optional[str] = None
    ) -> str:
        """🔧 COMPREHENSIVE PROFILE UPDATE TOOL
        
        Updates both user profile database AND resume data for complete consistency.
        
        Args:
            first_name: User's first name
            last_name: User's last name  
            phone: Phone number (e.g., "+1-555-123-4567")
            address: Full address or location (e.g., "San Francisco, CA")
            linkedin: LinkedIn profile URL or username
            preferred_language: Preferred language (e.g., "English", "Polish")
            date_of_birth: Date of birth (e.g., "1990-01-15")
            profile_headline: Professional headline/summary
            skills: Comma-separated skills (e.g., "Python, React, AWS")
            email: Email address (usually auto-populated from auth)
            
        Updates:
            ✅ User profile in database (for forms, applications)
            ✅ Resume data structure (for PDF generation)
            ✅ Maintains data consistency across the app
            
        Returns:
            Success message with details of what was updated
        """
        try:
            updated_fields = []
            
            # 1. Update User Profile in Database
            profile_updates = {}
            
            if first_name is not None:
                user.first_name = first_name.strip()
                profile_updates['first_name'] = first_name.strip()
                updated_fields.append(f"First name: {first_name}")
                
            if last_name is not None:
                user.last_name = last_name.strip()
                profile_updates['last_name'] = last_name.strip()
                updated_fields.append(f"Last name: {last_name}")
                
            if phone is not None:
                user.phone = phone.strip()
                profile_updates['phone'] = phone.strip()
                updated_fields.append(f"Phone: {phone}")
                
            if address is not None:
                user.address = address.strip()
                profile_updates['address'] = address.strip()
                updated_fields.append(f"Address: {address}")
                
            if linkedin is not None:
                linkedin_clean = linkedin.strip()
                if linkedin_clean and not linkedin_clean.startswith('http'):
                    if not linkedin_clean.startswith('linkedin.com'):
                        linkedin_clean = f"https://linkedin.com/in/{linkedin_clean}"
                    else:
                        linkedin_clean = f"https://{linkedin_clean}"
                user.linkedin = linkedin_clean
                profile_updates['linkedin'] = linkedin_clean
                updated_fields.append(f"LinkedIn: {linkedin_clean}")
                
            if preferred_language is not None:
                user.preferred_language = preferred_language.strip()
                profile_updates['preferred_language'] = preferred_language.strip()
                updated_fields.append(f"Language: {preferred_language}")
                
            if date_of_birth is not None:
                user.date_of_birth = date_of_birth.strip()
                profile_updates['date_of_birth'] = date_of_birth.strip()
                updated_fields.append(f"Date of birth: {date_of_birth}")
                
            if profile_headline is not None:
                user.profile_headline = profile_headline.strip()
                profile_updates['profile_headline'] = profile_headline.strip()
                updated_fields.append(f"Headline: {profile_headline}")
                
            if skills is not None:
                user.skills = skills.strip()
                profile_updates['skills'] = skills.strip()
                updated_fields.append(f"Skills: {skills}")
                
            if email is not None:
                user.email = email.strip()
                profile_updates['email'] = email.strip()
                updated_fields.append(f"Email: {email}")
            
            # 2. Update Resume Data Structure for consistency
            db_resume, resume_data = await get_or_create_resume()
            
            # Map profile fields to resume personal info
            resume_updates = {}
            
            if first_name or last_name:
                full_name = f"{first_name or user.first_name or ''} {last_name or user.last_name or ''}".strip()
                if full_name:
                    resume_data.personalInfo.name = full_name
                    resume_updates['name'] = full_name
                    
            if email:
                resume_data.personalInfo.email = email.strip()
                resume_updates['email'] = email.strip()
            elif user.email:
                resume_data.personalInfo.email = user.email
                resume_updates['email'] = user.email
                
            if phone:
                resume_data.personalInfo.phone = phone.strip()
                resume_updates['phone'] = phone.strip()
                
            if address:
                resume_data.personalInfo.location = address.strip()
                resume_updates['location'] = address.strip()
                
            if linkedin:
                resume_data.personalInfo.linkedin = linkedin_clean
                resume_updates['linkedin'] = linkedin_clean
                
            if profile_headline:
                resume_data.personalInfo.summary = profile_headline.strip()
                resume_updates['summary'] = profile_headline.strip()
                
            if skills:
                # Update both skills string and skills array in resume
                skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
                resume_data.skills = skills_list
                resume_updates['skills'] = skills_list
            
            # 3. Commit all changes
            db_resume.data = resume_data.dict()
            await db.commit()
            
            if not updated_fields:
                return "ℹ️ No profile updates were provided. Please specify which fields you'd like to update."
            
            # 4. Format success message
            success_message = "✅ **Profile Updated Successfully!**\n\n"
            success_message += "**Updated Fields:**\n"
            for field in updated_fields:
                success_message += f"• {field}\n"
                
            success_message += "\n**✨ Changes Applied To:**\n"
            success_message += "• User profile database (for job applications)\n"
            success_message += "• Resume data structure (for PDF generation)\n"
            success_message += "• Vector search index (for AI assistance)\n"
            
            if profile_updates:
                success_message += f"\n**🔄 Database Profile Updates:** {len(profile_updates)} fields\n"
            if resume_updates:
                success_message += f"**📄 Resume Data Updates:** {len(resume_updates)} fields\n"
                
            success_message += "\n💡 Your profile is now fully synchronized across all features!"
            
            log.info(f"Profile updated for user {user_id}: {updated_fields}")
            return success_message
            
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error updating user profile: {e}", exc_info=True)
            return f"❌ Error updating profile: {str(e)}. Please try again or contact support."