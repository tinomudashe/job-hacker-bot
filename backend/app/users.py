from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models_db import User, Document, Application, Resume
# FIX: Import Experience and Education models for validation, but keep User as UserSchema
from app.models import User as UserSchema, Experience, Education
# FIX: Import pydantic's ValidationError in addition to BaseModel
from pydantic import BaseModel, ValidationError
from app.dependencies import get_current_active_user
from typing import List, Optional, Dict, Any
from datetime import datetime
# NOTE: The import below is unused in this file but is kept to maintain file integrity
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from pathlib import Path
import json
# ADDITION: Import the 're' module for regular expression-based date parsing
import re


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic Models ---
# NOTE: No changes made to your Pydantic models below
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    preferred_language: Optional[str] = None
    date_of_birth: Optional[str] = None
    profile_headline: Optional[str] = None
    skills: Optional[str] = None



class DocumentResponse(BaseModel):
    id: str
    type: str
    name: str
    date_created: datetime
    date_updated: datetime

    class Config:
        from_attributes = True

class ApplicationResponse(BaseModel):
    id: str
    job_title: str
    company_name: str
    job_url: str
    status: str
    notes: Optional[str] = None
    date_applied: Optional[datetime] = None
    success: bool

    class Config:
        from_attributes = True
        
# This model will now be used for updating the 'settings' part of preferences
class SettingsUpdate(BaseModel):
    emailNotifications: Optional[bool] = None
    marketingEmails: Optional[bool] = None
    dataCollection: Optional[bool] = None

# ADDITION: This new helper function safely processes resume sections
# before they are validated by Pydantic models. This is the core fix.
def _process_resume_section(items: List[Dict[str, Any]], model, section_name: str, user_id: str) -> List[Any]:
    """
    Validates and transforms a list of items (experiences or educations)
    from a resume, handling date parsing and validation errors gracefully.
    """
    processed_items = []
    if not isinstance(items, list):
        logger.warning(f"'{section_name}' section for user {user_id} is not a list, skipping.")
        return []
        
    for item_data in items:
        try:
            # This logic now intelligently handles both string dates and structured date objects.
            if 'dates' in item_data and isinstance(item_data['dates'], str):
                # Use regex to safely extract start and end dates from a string
                date_match = re.match(r'^\s*(.*?)\s*–\s*(.*)\s*$', item_data['dates'])
                if date_match:
                    start_date, end_date = date_match.groups()
                    item_data['dates'] = {'start': start_date.strip(), 'end': end_date.strip()}
                else:
                    # Handle cases with only a start date or an un-parseable format
                    item_data['dates'] = {'start': item_data['dates'].strip(), 'end': None}
            
            # Ensure an 'id' field exists, as it is required by the Pydantic model.
            # This prevents validation errors for older data that may not have an ID.
            if 'id' not in item_data:
                item_data['id'] = str(datetime.utcnow().timestamp()) # Generate a temporary ID

            processed_items.append(model(**item_data))
        except ValidationError as e:
            # This is the original logic that logs a warning for malformed items.
            logger.warning(f"Skipping malformed {section_name} item for user {user_id}: {item_data}. Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing {section_name} item for user {user_id}: {e}")
            
    return processed_items


@router.get("/me", response_model=UserSchema)
async def get_me(db_user: User = Depends(get_current_active_user)):
    """Get current user's profile"""
    logger.info(f"Getting user data for: {db_user.id}")
    return db_user

@router.put("/me", response_model=UserSchema)
async def update_me(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """Update current user's profile"""
    logger.info(f"Updating user data for: {db_user.id}")
    
    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        if db.is_active:
            await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@router.post("/me/preferences", response_model=UserSchema)
async def update_user_preferences(
    new_settings: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user),
):
    """Update user's nested settings within their preferences."""
    logger.info(f"Updating preferences for user: {db_user.id}")

    # Load existing preferences, defaulting to a valid structure
    # The validator on the Pydantic model will handle string parsing on read
    current_prefs = db_user.preferences if isinstance(db_user.preferences, dict) else {}

    # Get the existing 'settings' sub-dictionary
    existing_settings = current_prefs.get("settings", {})
    if not isinstance(existing_settings, dict):
        existing_settings = {}

    # Merge the new settings
    update_data = new_settings.dict(exclude_unset=True)
    existing_settings.update(update_data)

    # Reconstruct the full preferences object
    final_prefs = {
        "job_titles": current_prefs.get("job_titles", []),
        "locations": current_prefs.get("locations", []),
        "settings": existing_settings,
    }

    # Manually serialize to a JSON string to match the database's expectation
    db_user.preferences = json.dumps(final_prefs)
    
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        if db.is_active:
            await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.get("/me/documents", response_model=List[DocumentResponse])
async def get_my_documents(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """Get current user's documents"""
    logger.info(f"Getting documents for user: {db_user.id}")
    result = await db.execute(
        select(Document)
        .where(Document.user_id == db_user.id)
        .order_by(Document.date_created.desc())
    )
    return result.scalars().all()

@router.get("/me/applications", response_model=List[ApplicationResponse])
async def get_my_applications(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """Get current user's job applications"""
    logger.info(f"Getting applications for user: {db_user.id}")
    result = await db.execute(
        select(Application)
        .where(Application.user_id == db_user.id)
        .order_by(Application.date_applied.desc())
    )
    return result.scalars().all()

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """Delete current user's account"""
    logger.info(f"Deleting user account: {db_user.id}")
    try:
        await db.delete(db_user)
        await db.commit()
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        if db.is_active:
            await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user account")

class UserProfileOut(UserSchema):
    document_summaries: List[str] = []
    application_stats: dict = {}
    last_active: Optional[datetime] = None

@router.get("/profile", response_model=UserProfileOut)
async def get_profile(
    db: AsyncSession = Depends(get_db), 
    db_user: User = Depends(get_current_active_user)
):
    logger.info(f"Getting profile for user: {db_user.id}")
    
    # Get documents
    docs_result = await db.execute(select(Document).where(Document.user_id == db_user.id))
    docs = docs_result.scalars().all()
    
    # Summarize documents
    summaries = []
    for doc in docs:
        summary = f"{doc.type.title()} ({doc.name})"
        if doc.content:
            preview = doc.content[:100].replace('\n', ' ').strip()
            if len(doc.content) > 100:
                preview += "..."
            summary += f": {preview}"
        summaries.append(summary)

    # Get application stats
    apps_result = await db.execute(select(Application).where(Application.user_id == db_user.id))
    apps = apps_result.scalars().all()
    stats = {
        "total_applications": len(apps),
        "last_applied": max([a.date_applied for a in apps if a.date_applied], default=None) if apps else None,
        "statuses": {s: len([a for a in apps if a.status == s]) for s in set(a.status for a in apps)}
    }
    
    # Get Resume data for experience and education
    resume_result = await db.execute(select(Resume).where(Resume.user_id == db_user.id))
    resume = resume_result.scalar_one_or_none()
    
    experiences = []
    education = []
    if resume and isinstance(resume.data, dict):
        # FIX: Use the new helper function to safely process both sections.
        # This prevents crashes from malformed data (e.g., incorrect date formats)
        # and ensures all valid entries are included in the profile.
        raw_experiences = resume.data.get("experience", [])
        experiences = _process_resume_section(raw_experiences, Experience, "experience", db_user.id)

        raw_education = resume.data.get("education", [])
        education = _process_resume_section(raw_education, Education, "education", db_user.id)

        
    # Last active
    last_doc_creation = max([doc.date_created for doc in docs], default=None) if docs else None
    last_app_date = stats["last_applied"]

    if last_doc_creation and last_app_date:
        last_active = max(last_doc_creation, last_app_date)
    else:
        last_active = last_doc_creation or last_app_date
    
    # Convert database model to Pydantic model
    user_data = db_user.__dict__
    user_data.update({
        "document_summaries": summaries,
        "application_stats": stats,
        "last_active": last_active,
        "experiences": experiences,
        "education": education
    })
    
    # Return profile using Pydantic model
    return UserProfileOut(**user_data)