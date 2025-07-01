import logging
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr, HttpUrl
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db import get_db
from app.models_db import User, Resume
from app.dependencies import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Helper Functions ---

def fix_resume_data_structure(data: Dict) -> Dict:
    """
    Ensures resume data has proper structure with required ID fields.
    Adds missing IDs to experience and education entries.
    """
    if not isinstance(data, dict):
        return data
    
    # Fix experience entries
    if 'experience' in data and isinstance(data['experience'], list):
        for exp in data['experience']:
            if isinstance(exp, dict) and 'id' not in exp:
                exp['id'] = str(uuid.uuid4())
    
    # Fix education entries  
    if 'education' in data and isinstance(data['education'], list):
        for edu in data['education']:
            if isinstance(edu, dict) and 'id' not in edu:
                edu['id'] = str(uuid.uuid4())
    
    return data

# --- Pydantic Models to match Frontend ---

class PersonalInfo(BaseModel):
    name: str = ""
    email: Optional[EmailStr] = None
    phone: str = ""
    linkedin: Optional[str] = None
    location: str = ""
    summary: str = ""

class Experience(BaseModel):
    id: str
    jobTitle: str = ""
    company: str = ""
    dates: str = ""
    description: str = ""

class Education(BaseModel):
    id: str
    degree: str = ""
    institution: str = ""
    dates: str = ""

class ResumeData(BaseModel):
    personalInfo: PersonalInfo
    experience: List[Experience]
    education: List[Education]
    skills: List[str]
    projects: List[Dict] = []
    certifications: List[Dict] = []
    languages: List[Dict] = []
    interests: List[Dict] = []

# --- API Endpoints ---

@router.get("/resume", response_model=ResumeData)
async def get_resume_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetches the user's resume data from the database.
    If no resume is found, it returns a default, empty structure.
    """
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
    )
    resume = result.scalars().first()

    if resume:
        # Fix data structure to ensure required IDs exist
        fixed_data = fix_resume_data_structure(resume.data)
        return ResumeData(**fixed_data)
        
    # Return a default empty structure if no resume data is found
    return ResumeData(
        personalInfo=PersonalInfo(),
        experience=[],
        education=[],
        skills=[],
        projects=[],
        certifications=[],
        languages=[],
        interests=[]
    )

@router.put("/resume", response_model=ResumeData)
async def update_resume_data(
    resume_data: ResumeData,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Creates or updates the user's resume data in the database.
    """
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
    )
    db_resume = result.scalars().first()

    # Convert to dict and ensure proper structure
    resume_dict = resume_data.dict()
    fixed_data = fix_resume_data_structure(resume_dict)

    if db_resume:
        db_resume.data = fixed_data
    else:
        db_resume = Resume(
            user_id=current_user.id,
            data=fixed_data
        )
        db.add(db_resume)
    
    await db.commit()
    await db.refresh(db_resume)
    
    return ResumeData(**db_resume.data) 