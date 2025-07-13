import logging
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select
from sqlalchemy.orm import attributes, joinedload
import uuid

from app.db import get_db
from app.models_db import User, Resume, GeneratedCoverLetter
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

class Dates(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class Experience(BaseModel):
    id: str
    jobTitle: str = ""
    company: str = ""
    dates: Optional[Dates] = None
    description: str = ""

class Education(BaseModel):
    id: str
    degree: str = ""
    institution: str = ""
    dates: Optional[Dates] = None
    description: Optional[str] = ""

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    url: Optional[HttpUrl] = None

class Certificate(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    date_issued: Optional[str] = None

class Language(BaseModel):
    name: str
    proficiency: Optional[str] = None

class ResumeData(BaseModel):
    personalInfo: PersonalInfo
    experience: List[Experience]
    education: List[Education]
    skills: List[str]
    projects: List[Project] = []
    certifications: List[Certificate] = []
    languages: List[Language] = []
    interests: List[Dict] = []

# EDIT: This is the new, comprehensive request model for the save endpoint.
class FullResumeUpdateRequest(BaseModel):
    personalInfo: PersonalInfo
    experience: List[Experience]
    education: List[Education]
    skills: List[str]
    projects: Optional[List[Project]] = None
    certifications: Optional[List[Certificate]] = None
    languages: Optional[List[Language]] = None

# --- API Endpoints ---

@router.get("/resume/latest", response_model=dict, summary="Get the latest generated resume")
async def get_latest_resume(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves the most recently generated resume for the authenticated user.
    """
    logger.info(f"Fetching latest generated resume for user {current_user.id}")
    
    result = await db.execute(
        select(GeneratedCoverLetter)
        .where(GeneratedCoverLetter.user_id == current_user.id)
        # A simple way to distinguish resumes from cover letters in the same table
        .where(GeneratedCoverLetter.content.contains("[DOWNLOADABLE_RESUME]"))
        .order_by(desc(GeneratedCoverLetter.created_at))
        .limit(1)
    )
    
    latest_resume = result.scalars().first()
    
    if not latest_resume:
        raise HTTPException(status_code=404, detail="No generated resume found.")
        
    return {
        "id": latest_resume.id,
        "user_id": latest_resume.user_id,
        "content": latest_resume.content,
        "created_at": latest_resume.created_at
    }


# EDIT: This new PUT endpoint replaces the old one for a safer, transactional update.
@router.put("/resume/full", response_model=ResumeData)
async def update_full_resume(
    resume_data: FullResumeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Creates or updates the user's full resume data, including profile info,
    in a single transaction handled by the get_db dependency.
    """
    # The get_db dependency wraps this entire function in a transaction.
    
    # --- 1. Update the User model with personal info and skills ---
    user = await db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if resume_data.personalInfo:
        user.name = resume_data.personalInfo.name
        user.email = str(resume_data.personalInfo.email) if resume_data.personalInfo.email else user.email
        user.phone = resume_data.personalInfo.phone
        user.linkedin = resume_data.personalInfo.linkedin
        user.profile_headline = resume_data.personalInfo.summary

    if resume_data.skills:
        user.skills = ", ".join(resume_data.skills)
    
    # --- 2. Update the structured Resume record ---
    result = await db.execute(select(Resume).filter_by(user_id=user.id))
    db_resume = result.scalar_one_or_none()

    resume_dict = resume_data.dict()
    fixed_data = fix_resume_data_structure(resume_dict)

    if db_resume:
        db_resume.data = fixed_data
        attributes.flag_modified(db_resume, "data")
    else:
        db_resume = Resume(user_id=user.id, data=fixed_data)
        db.add(db_resume)
    
    await db.commit()
    await db.refresh(user)
    await db.refresh(db_resume)

    # Construct the final response model from the updated data
    return ResumeData(**fixed_data)


# EDIT: This endpoint is now rewritten to be the single source of truth,
# correctly merging data from both User and Resume tables.
@router.get("/resume", response_model=ResumeData)
async def get_resume_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetches the user's resume data, intelligently merging profile info
    with the structured resume record to provide a complete picture.
    """
    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
    )
    resume = resume_result.scalars().first()

    # Start with data from the structured resume record, if it exists
    if resume and resume.data:
        final_data = resume.data
    else:
        # If no resume record, create a default structure
        final_data = {
            "personalInfo": {}, "experience": [], "education": [], "skills": [],
            "projects": [], "certifications": [], "languages": [], "interests": []
        }

    # Always overwrite personal info and skills with the latest from the User profile
    # to ensure consistency.
    final_data["personalInfo"]["name"] = current_user.name
    final_data["personalInfo"]["email"] = current_user.email
    final_data["personalInfo"]["phone"] = current_user.phone
    final_data["personalInfo"]["linkedin"] = current_user.linkedin
    final_data["personalInfo"]["summary"] = current_user.profile_headline
    final_data["personalInfo"]["location"] = getattr(current_user, 'address', '') # Use address for location

    if current_user.skills:
        final_data["skills"] = [s.strip() for s in current_user.skills.split(',')]
    else:
        final_data["skills"] = []

    # Ensure the final object matches the ResumeData model structure
    return ResumeData(**final_data)


# EDIT: Marked the old endpoint as deprecated.
@router.put("/resume", response_model=ResumeData, deprecated=True)
async def update_resume_data(
    resume_data: ResumeData,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    DEPRECATED: Use PUT /api/resume/full instead.
    This endpoint only updates the structured data blob and can lead to inconsistencies.
    """
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
    )
    db_resume = result.scalars().first()

    resume_dict = resume_data.dict()
    fixed_data = fix_resume_data_structure(resume_dict)

    if db_resume:
        db_resume.data = fixed_data
        attributes.flag_modified(db_resume, "data")
    else:
        db_resume = Resume(
            user_id=current_user.id,
            data=fixed_data
        )
        db.add(db_resume)
    
    try:
        await db.commit()
        await db.refresh(db_resume)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating resume for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save resume data.")
    
    return ResumeData(**db_resume.data)