from typing import Optional, List
from langchain_core.tools import tool
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import User
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

@tool
async def manage_skills_comprehensive(
    db: AsyncSession,
    user: User,
    technical_skills: Optional[str] = None,
    programming_languages: Optional[str] = None,
    frameworks_libraries: Optional[str] = None,
    databases: Optional[str] = None,
    cloud_platforms: Optional[str] = None,
    tools_software: Optional[str] = None,
    soft_skills: Optional[str] = None,
    languages_spoken: Optional[str] = None,
    certifications: Optional[str] = None,
    replace_all: bool = False
) -> str:
    """
    Comprehensive skills management with categorization and exact variables.
    
    Args:
        technical_skills: General technical skills (e.g., "Machine Learning, Data Analysis, Web Development")
        programming_languages: Programming languages (e.g., "Python, JavaScript, Java, C++, SQL")
        frameworks_libraries: Frameworks and libraries (e.g., "React, Django, TensorFlow, pandas")
        databases: Database systems (e.g., "PostgreSQL, MongoDB, Redis, MySQL")
        cloud_platforms: Cloud services (e.g., "AWS, Google Cloud, Azure, Docker, Kubernetes")
        tools_software: Tools and software (e.g., "Git, VS Code, Jupyter, Figma, Photoshop")
        soft_skills: Interpersonal skills (e.g., "Leadership, Communication, Problem Solving")
        languages_spoken: Spoken languages (e.g., "English (Native), Polish (Fluent), Spanish (Basic)")
        certifications: Professional certifications (e.g., "AWS Solutions Architect, PMP, Google Analytics")
        replace_all: If True, replaces all skills. If False, adds to existing skills.
    
    Returns:
        Success message with updated skills breakdown
    """
    try:
        db_resume, resume_data = await get_or_create_resume(db, user)
        
        # Collect all skills into categorized list
        all_skills = []
        skill_categories = []
        
        if technical_skills:
            tech_list = [skill.strip() for skill in technical_skills.split(",") if skill.strip()]
            all_skills.extend(tech_list)
            skill_categories.append(f"Technical Skills: {len(tech_list)} skills")
        
        if programming_languages:
            prog_list = [skill.strip() for skill in programming_languages.split(",") if skill.strip()]
            all_skills.extend(prog_list)
            skill_categories.append(f"Programming Languages: {len(prog_list)} languages")
        
        if frameworks_libraries:
            framework_list = [skill.strip() for skill in frameworks_libraries.split(",") if skill.strip()]
            all_skills.extend(framework_list)
            skill_categories.append(f"Frameworks & Libraries: {len(framework_list)} items")
        
        if databases:
            db_list = [skill.strip() for skill in databases.split(",") if skill.strip()]
            all_skills.extend(db_list)
            skill_categories.append(f"Databases: {len(db_list)} systems")
        
        if cloud_platforms:
            cloud_list = [skill.strip() for skill in cloud_platforms.split(",") if skill.strip()]
            all_skills.extend(cloud_list)
            skill_categories.append(f"Cloud Platforms: {len(cloud_list)} platforms")
        
        if tools_software:
            tools_list = [skill.strip() for skill in tools_software.split(",") if skill.strip()]
            all_skills.extend(tools_list)
            skill_categories.append(f"Tools & Software: {len(tools_list)} tools")
        
        if soft_skills:
            soft_list = [skill.strip() for skill in soft_skills.split(",") if skill.strip()]
            all_skills.extend(soft_list)
            skill_categories.append(f"Soft Skills: {len(soft_list)} skills")
        
        if languages_spoken:
            lang_list = [skill.strip() for skill in languages_spoken.split(",") if skill.strip()]
            all_skills.extend(lang_list)
            skill_categories.append(f"Languages: {len(lang_list)} languages")
        
        if certifications:
            cert_list = [skill.strip() for skill in certifications.split(",") if skill.strip()]
            all_skills.extend(cert_list)
            skill_categories.append(f"Certifications: {len(cert_list)} certifications")
        
        # Update skills in resume
        if replace_all or not resume_data.skills:
            resume_data.skills = all_skills
            action = "replaced"
        else:
            # Add to existing skills, avoiding duplicates
            existing_skills = set(resume_data.skills)
            new_skills = [skill for skill in all_skills if skill not in existing_skills]
            resume_data.skills.extend(new_skills)
            action = "added"
        
        # Also update user profile skills field for consistency
        user.skills = ", ".join(resume_data.skills)
        
        db_resume.data = resume_data.dict()
        await db.commit()
        
        result_message = f"✅ **Skills {action.title()} Successfully!**\n\n"
        
        if skill_categories:
            result_message += "**Updated Categories:**\n" + "\n".join(f"• {cat}" for cat in skill_categories)
            result_message += f"\n\n**Total Skills:** {len(resume_data.skills)}"
        else:
            result_message += "No skills provided to update."
        
        return result_message
        
    except Exception as e:
        if db.is_active:
            await db.rollback()
        log.error(f"Error managing skills: {e}")
        return f"❌ Error updating skills: {str(e)}"