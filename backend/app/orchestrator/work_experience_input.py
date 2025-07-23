from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class Dates(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class Experience(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    jobTitle: str
    company: str
    dates: Dates
    description: Optional[str] = None