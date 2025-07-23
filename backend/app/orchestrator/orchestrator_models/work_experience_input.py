from pydantic import BaseModel
from typing import Optional

class WorkExperienceInput(BaseModel):
    """Schema for adding a single work-experience entry."""
    job_title: str
    company: str
    dates: str
    description: str