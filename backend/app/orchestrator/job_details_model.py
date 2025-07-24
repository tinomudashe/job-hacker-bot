from typing import Optional, List
from pydantic import BaseModel, Field

class JobDetails(BaseModel):
    """A model representing the extracted details of a job description."""
    job_title: Optional[str] = Field(None, description="The title of the job.")
    company: Optional[str] = Field(None, description="The name of the company.")
    location: Optional[str] = Field(None, description="The location of the job.")
    required_skills: Optional[List[str]] = Field(None, description="A list of required skills mentioned in the job description.")
    experience_level: Optional[str] = Field(None, description="The required experience level (e.g., 'Entry-level', 'Mid-level', 'Senior').")
    full_text: Optional[str] = Field(None, description="The full, cleaned text of the job description.") 