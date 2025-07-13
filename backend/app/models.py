from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

class Dates(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class Experience(BaseModel):
    id: str
    jobTitle: str
    company: str
    dates: Optional[Dates] = None
    description: str

class Education(BaseModel):
    id: str
    degree: str
    institution: str
    dates: Optional[Dates] = None
    description: Optional[str] = None

class Settings(BaseModel):
    emailNotifications: bool = True
    marketingEmails: bool = False
    dataCollection: bool = True

class UserPreferences(BaseModel):
    job_titles: List[str] = []
    locations: List[str] = []
    settings: Settings = Field(default_factory=Settings)


class User(BaseModel):
    id: str
    external_id: Optional[str] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    preferred_language: Optional[str] = None
    date_of_birth: Optional[str] = None
    profile_headline: Optional[str] = None
    skills: Optional[str] = None
    profile_picture_url: Optional[str] = None
    email: Optional[EmailStr] = None
    picture: Optional[str] = None
    active: bool = True
    preferences: Optional[UserPreferences] = None
    faiss_index_path: Optional[str] = None
    experiences: List[Experience] = []
    education: List[Education] = []

    @field_validator('preferences', mode='before')
    @classmethod
    def parse_preferences(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None  # Return None for invalid JSON
        return v

    class Config:
        from_attributes = True

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    link: str
    date_posted: datetime
    source: str
    status: str = "new"

class Application(BaseModel):
    id: str
    user_id: str
    job_id: str
    date_applied: datetime
    status: str
    resume_id: str
    cover_letter_id: str
    notes: Optional[str] = None
    success: Optional[bool] = True

class Document(BaseModel):
    id: str
    user_id: str
    type: str  # 'resume' or 'cover_letter'
    name: str
    content: Optional[str] = None
    vector_store_path: Optional[str] = None
    date_created: datetime
    date_updated: datetime

class Notification(BaseModel):
    id: str
    user_id: str
    type: str
    content: str
    date: datetime
    read: bool = False 