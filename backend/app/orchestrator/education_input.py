from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class Dates(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class Education(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    degree: str
    institution: str
    dates: Dates
    description: Optional[str] = None

class Certification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    issuing_organization: str
    issue_date: str
    expiration_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    
class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    technologies_used: list[str] = []
    url: Optional[str] = None
    repo_url: Optional[str] = None

class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None

class ResumeData(BaseModel):
    personalInfo: PersonalInfo
    experience: List[dict] = [] # Using dict for now to match old structure
    education: List[Education] = []
    skills: List[str] = []
    projects: List[Project] = []
    certifications: List[Certification] = []
    languages: List[str] = []
    interests: List[str] = []