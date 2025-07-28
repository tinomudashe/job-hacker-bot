import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
import uuid

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
# FIX: Import 'Project' from the correct central model file.
from ..education_input import Project
from sqlalchemy.orm.attributes import flag_modified

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class AddProjectsInput(BaseModel):
    """Input for adding a project to the user's resume."""
    project_name: str = Field(description="The name of the project.")
    description: str = Field(description="A brief description of the project.")
    technologies_used: Optional[List[str]] = Field(default=None, description="A list of technologies used in the project.")
    project_url: Optional[str] = Field(default=None, description="A URL to the project if available.")

# Step 2: Define the core logic as a plain async function.
async def _add_projects(
    db: AsyncSession,
    user: User,
    project_name: str,
    description: str,
    technologies_used: Optional[List[str]] = None,
    project_url: Optional[str] = None,
) -> str:
    """The underlying implementation for adding a new project to the user's resume."""
    if not db or not user:
        return "❌ Error: Database session and user must be provided to add project."

    try:
        db_resume, resume_data = await get_or_create_resume(db, user)

        if not resume_data:
            return "❌ Error: Could not find or create a resume for the user."

        if not hasattr(resume_data, 'projects') or resume_data.projects is None:
            resume_data.projects = []
        
        full_description = description
        details = []
        if technologies_used:
            details.append(f"Technologies: {', '.join(technologies_used)}")
        if project_url:
            details.append(f"Live URL: {project_url}")
        
        if details:
            full_description += "\n\n" + "\n".join(details)
        
        new_project = Project(
            id=str(uuid.uuid4()),
            name=project_name,
            description=full_description,
            technologies=technologies_used or [],
            url=project_url or ""
        )
        
        resume_data.projects.append(new_project)
        db_resume.data = resume_data.dict()
        flag_modified(db_resume, "data")
        
        await db.commit()
        await db.refresh(db_resume)

        return f"✅ Project '{new_project.name}' was successfully added."
        
    except Exception as e:
        if db.in_transaction():
            await db.rollback()
        log.error(f"Error adding project: {e}", exc_info=True)
        return f"❌ DATABASE ERROR: The attempt to add a project failed. Details: {str(e)}"

# Step 3: Manually construct the Tool object with the explicit schema.
add_projects = Tool(
    name="add_projects",
    description="Adds a new project to the user's resume.",
    func=_add_projects,
    args_schema=AddProjectsInput
)