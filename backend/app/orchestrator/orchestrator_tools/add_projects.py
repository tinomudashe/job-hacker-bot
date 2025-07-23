from typing import Optional, List
from langchain_core.tools import tool
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.orchestrator_models.resume_model import Project

log = logging.getLogger(__name__)

@tool
async def add_project(
    db: AsyncSession,
    user: User,
    project_name: str,
    description: str,
    technologies_used: Optional[str] = None,
    project_url: Optional[str] = None,
    github_url: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    team_size: Optional[str] = None,
    role: Optional[str] = None
) -> str:
    """
    Add a project entry to resume with detailed variables.
    
    Args:
        project_name: Name of the project (e.g., "E-commerce Platform", "Mobile App")
        description: Project description and your contributions
        technologies_used: Technologies used (e.g., "React, Node.js, PostgreSQL, AWS")
        project_url: Live project URL (e.g., "https://myproject.com")
        github_url: GitHub repository URL (e.g., "https://github.com/user/project")
        start_date: Start date (e.g., "January 2023", "2023-01")
        end_date: End date (e.g., "March 2023", "Ongoing")
        team_size: Team size (e.g., "Solo project", "Team of 4", "5 developers")
        role: Your role (e.g., "Lead Developer", "Full-stack Developer", "Frontend Developer")
    
    Returns:
        Success message with project details
    """
    if not db or not user:
        return "❌ Error: Database session and user must be provided to add project."

    try:
        db_resume, resume_data = await get_or_create_resume(db, user)

        if not resume_data:
            return "❌ Error: Could not find or create a resume for the user."

        # Ensure projects list exists
        if not hasattr(resume_data, 'projects') or resume_data.projects is None:
            resume_data.projects = []
        
        # Build comprehensive project description
        full_description = description
        
        details = []
        if role:
            details.append(f"Role: {role}")
        if team_size:
            details.append(f"Team Size: {team_size}")
        if technologies_used:
            details.append(f"Technologies: {technologies_used}")
        if project_url:
            details.append(f"Live URL: {project_url}")
        if github_url:
            details.append(f"GitHub: {github_url}")
        
        if details:
            full_description += "\n\n" + "\n".join(details)
        
        # Format dates
        date_info = ""
        if start_date:
            date_info = start_date
            if end_date:
                date_info += f" - {end_date}"
            elif end_date != "Ongoing":
                date_info += " - Present"
        
        new_project = Project(
            id=str(uuid.uuid4()),
            name=project_name,
            description=full_description,
            dates=date_info,
            technologies=technologies_used or "",
            url=project_url or "",
            github=github_url or ""
        )
        
        resume_data.projects.append(new_project)
        db_resume.data = resume_data.dict()
        flag_modified(db_resume, "data")
        
        # --- COMMIT AND VERIFY ---
        await db.commit()
        await db.refresh(db_resume)

        added_project = next((p for p in db_resume.data['projects'] if p['id'] == new_project.id), None)
        
        if added_project and added_project['name'] == new_project.name:
            log.info(f"SUCCESSFULLY VERIFIED write for project: {new_project.name}")
            return f"✅ Project '{new_project.name}' was successfully added and verified."
        else:
            raise Exception(f"DATABASE VERIFICATION FAILED for project: {new_project.name}")
        
    except Exception as e:
        await db.rollback()
        log.error(f"Error adding project: {e}")
        return f"❌ DATABASE ERROR: The attempt to add a project failed. Details: {str(e)}"