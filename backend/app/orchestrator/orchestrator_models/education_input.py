from pydantic import BaseModel
from typing import Optional

class EducationInput(BaseModel):
    """Schema for adding an education entry."""
    degree: str
    institution: str
    dates: str
    description: str