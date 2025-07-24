from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class Project(BaseModel):
    """A model representing a project in a user's resume."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str
    description: str
    technologies_used: Optional[List[str]] = None
    project_url: Optional[str] = None 