import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import uuid

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.project_input import Project
from sqlalchemy.orm.attributes import flag_modified

log = logging.getLogger(__name__)

class AddProjectsInput(BaseModel):
    """Input for adding a project to the user's resume."""
    project_name: str = Field(description="The name of the project.")
    description: str = Field(description="A brief description of the project.")
    technologies_used: Optional[List[str]] = Field(None, description="A list of technologies used in the project.")
    project_url: Optional[str] = Field(None, description="A URL to the project if available.")

@tool(args_schema=AddProjectsInput)
async def add_projects(
    db: AsyncSession,
    user: User,
    project_name: str,
    description: str,
    technologies_used: Optional[List[str]] = None,
    project_url: Optional[str] = None,
) -> str:
    """Adds a new project to the user's resume."""
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
        if technologies_used:
            details.append(f"Technologies: {', '.join(technologies_used)}")
        if project_url:
            details.append(f"Live URL: {project_url}")
        
        if details:
            full_description += "\n\n" + "\n".join(details)
        
        # Format dates
        date_info = ""
        # The original code had start_date and end_date logic here, but the new_project object
        # doesn't have start_date and end_date attributes.
        # Assuming the intent was to use the provided parameters directly for dates.
        # If the user wants to keep the date logic, it needs to be re-added to the new_project object.
        # For now, removing the date logic as new_project doesn't have it.
        
        new_project = Project(
            id=str(uuid.uuid4()),
            name=project_name,
            description=full_description,
            # dates=date_info, # Removed as new_project doesn't have dates attribute
            technologies=technologies_used or "",
            url=project_url or "",
            # github=github_url or "" # Removed as new_project doesn't have github attribute
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