import logging
from typing import List, Optional, Dict, Union
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select
from sqlalchemy.orm import attributes, joinedload
import uuid
import re

from app.db import get_db
from app.models_db import User, Resume, GeneratedCoverLetter
from app.dependencies import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Helper Functions ---

def fix_resume_data_structure(data: Dict) -> Dict:
    """
    Ensures resume data has proper structure and corrects common data inconsistencies.
    - Scrubs personalInfo to remove any fields not defined in the Pydantic model.
    - Adds missing IDs to experience, education, projects, certifications, and languages.
    - Renames 'name' key to 'title' in project entries.
    - Converts string-based certifications into structured objects.
    - Ensures 'skills' and 'interests' are lists of strings, filtering out None values.
    """
    if not isinstance(data, dict):
        return data

    # FIX: Defensively clean the personalInfo object.
    # This removes any keys that are not explicitly part of the PersonalInfo model,
    # preventing validation errors from unexpected fields being added by other tools.
    if 'personalInfo' in data and isinstance(data.get('personalInfo'), dict):
        allowed_keys = PersonalInfo.model_fields.keys()
        info_data = data['personalInfo']
        data['personalInfo'] = {k: v for k, v in info_data.items() if k in allowed_keys}

    # Fix lists of objects: add IDs, fix project titles and technologies
    for section in ['experience', 'education', 'projects', 'languages']:
        if section in data and isinstance(data.get(section), list):
            for item in data[section]:
                if isinstance(item, dict):
                    if 'id' not in item:
                        item['id'] = str(uuid.uuid4())
                    # Rename 'name' to 'title' in projects for compatibility
                    if section == 'projects' and 'name' in item and 'title' not in item:
                        item['title'] = item.pop('name')
                    # Convert technologies string to array if needed
                    if section == 'projects' and 'technologies' in item:
                        tech = item['technologies']
                        if isinstance(tech, str):
                            # Split by comma or semicolon
                            item['technologies'] = [t.strip() for t in tech.replace(';', ',').split(',') if t.strip()]
                        elif not isinstance(tech, list):
                            item['technologies'] = []
                    # Fix language field name mismatch: rename 'name' to 'language'
                    if section == 'languages' and 'name' in item and 'language' not in item:
                        item['language'] = item.pop('name')

    # Convert string-based certifications into structured objects
    if 'certifications' in data and isinstance(data.get('certifications'), list):
        new_certifications = []
        for cert in data['certifications']:
            if isinstance(cert, str):
                name, issuer, date = cert, "", ""
                parts = cert.split('–', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    issuer_date_part = parts[1].strip()
                    date_match = re.search(r'\((.*?)\)$', issuer_date_part)
                    if date_match:
                        date = date_match.group(1).strip()
                        issuer = issuer_date_part[:date_match.start()].strip()
                    else:
                        issuer = issuer_date_part
                
                new_certifications.append({
                    'id': str(uuid.uuid4()),
                    'name': name,
                    'issuer': issuer,
                    'date': date
                })
            elif isinstance(cert, dict):
                if 'id' not in cert:
                    cert['id'] = str(uuid.uuid4())
                new_certifications.append(cert)
        data['certifications'] = new_certifications

    # Clean up simple string lists like 'skills' and 'interests'
    for key in ['skills', 'interests']:
        if key in data and isinstance(data.get(key), list):
            data[key] = [str(item) for item in data[key] if item is not None]
    
    return data

# --- Pydantic Models to match Frontend ---

class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None

class Dates(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class Experience(BaseModel):
    id: Optional[str] = None
    jobTitle: Optional[str] = Field(None, alias="jobTitle")
    company: Optional[str] = None
    dates: Optional[Union[Dates, str]] = None
    description: Optional[str] = None

class Education(BaseModel):
    id: Optional[str] = None
    degree: Optional[str] = None
    institution: Optional[str] = None
    dates: Optional[Union[Dates, str]] = None
    description: Optional[str] = None

class Project(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[Union[List[str], str]] = None  # Can be string or list
    url: Optional[str] = None
    github: Optional[str] = None
    dates: Optional[str] = None

class Certification(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    credentialId: Optional[str] = Field(None, alias="credentialId")

class Language(BaseModel):
    id: Optional[str] = None
    language: Optional[str] = None
    name: Optional[str] = None  # Added for frontend compatibility
    proficiency: Optional[str] = None
    
    def __init__(self, **data):
        # Handle both 'name' and 'language' fields
        if 'name' in data and 'language' not in data:
            data['language'] = data.get('name')
        elif 'language' in data and 'name' not in data:
            data['name'] = data.get('language')
        super().__init__(**data)

class ResumeData(BaseModel):
    # EDIT: Ensure all fields have default values to prevent validation errors.
    # This makes the model more resilient to missing data, especially from older
    # resume records that may not have all the newer fields.
    personalInfo: PersonalInfo = Field(default_factory=PersonalInfo)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    job_title: Optional[str] = None  # Professional title for the resume

# EDIT: This is the new, comprehensive request model for the save endpoint.
class FullResumeUpdateRequest(BaseModel):
    personalInfo: PersonalInfo
    experience: List[Experience]
    education: List[Education]
    skills: List[str]
    projects: Optional[List[Project]] = None
    certifications: Optional[List[Certification]] = None
    languages: Optional[List[Language]] = None
    job_title: Optional[str] = None  # Professional title for the resume

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
    
    logger.info(f"Received resume update request for user {current_user.id}")
    logger.debug(f"Resume data: {resume_data.dict()}")
    
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
    
    try:
        await db.commit()
        logger.info(f"Successfully committed resume update for user {current_user.id}")
    except Exception as commit_error:
        logger.error(f"Commit failed for user {current_user.id}: {commit_error}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(commit_error)}")
    
    await db.refresh(user)
    await db.refresh(db_resume)

    # Transform language field for frontend compatibility: 'language' -> 'name'
    if 'languages' in fixed_data and isinstance(fixed_data['languages'], list):
        for lang_item in fixed_data['languages']:
            if isinstance(lang_item, dict) and 'language' in lang_item:
                lang_item['name'] = lang_item.get('language', '')
                # Keep both fields for compatibility

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

    # Only fill in missing personal info from the User profile
    # This preserves any refined/enhanced data while ensuring completeness
    if not final_data.get("personalInfo"):
        final_data["personalInfo"] = {}
    
    # Only update fields that are missing or empty in the resume data
    if not final_data["personalInfo"].get("name"):
        final_data["personalInfo"]["name"] = current_user.name
    if not final_data["personalInfo"].get("email"):
        final_data["personalInfo"]["email"] = current_user.email
    if not final_data["personalInfo"].get("phone"):
        final_data["personalInfo"]["phone"] = current_user.phone
    if not final_data["personalInfo"].get("linkedin"):
        final_data["personalInfo"]["linkedin"] = current_user.linkedin
    if not final_data["personalInfo"].get("location"):
        final_data["personalInfo"]["location"] = getattr(current_user, 'address', '')
    
    # IMPORTANT: Don't overwrite the summary if it exists (preserves refined summaries)
    if not final_data["personalInfo"].get("summary"):
        final_data["personalInfo"]["summary"] = current_user.profile_headline
    
    # Only use user profile skills if resume has no skills at all
    # This preserves refined/enhanced skills
    if not final_data.get("skills") or len(final_data["skills"]) == 0:
        if current_user.skills:
            final_data["skills"] = [s.strip() for s in current_user.skills.split(',')]
        else:
            final_data["skills"] = []

    # Transform language field for frontend compatibility: 'language' -> 'name'
    if 'languages' in final_data and isinstance(final_data['languages'], list):
        for lang_item in final_data['languages']:
            if isinstance(lang_item, dict) and 'language' in lang_item:
                lang_item['name'] = lang_item.get('language', '')
                # Keep 'language' field for backend compatibility but also provide 'name'
                # This ensures both frontend and backend can work with the data

    # Include job_title from resume data if it exists
    if resume and resume.data and 'job_title' in resume.data:
        final_data['job_title'] = resume.data['job_title']
    
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