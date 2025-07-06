from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models_db import User, Document, Application
from app.models import User as UserSchema
from pydantic import BaseModel
from app.dependencies import get_current_active_user
from typing import List, Optional
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic Models ---
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
    date_applied: datetime
    success: bool

    class Config:
        from_attributes = True

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
    
    # Summarize documents (simplified for now)
    summaries = []
    for doc in docs:
        summary = f"{doc.type.title()} ({doc.name})"
        if doc.content:
            # Add first 100 characters of content as preview
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
        "last_applied": max([a.date_applied for a in apps], default=None) if apps else None,
        "statuses": {s: len([a for a in apps if a.status == s]) for s in set(a.status for a in apps)}
    }
    
    # Last active
    last_doc_creation = max([doc.date_created for doc in docs], default=None) if docs else None
    last_app_date = stats["last_applied"]

    if last_doc_creation and last_app_date:
        last_active = max(last_doc_creation, last_app_date)
    else:
        last_active = last_doc_creation or last_app_date
    
    # Convert database model to Pydantic model
    user_data = {
        "id": db_user.id,
        "external_id": db_user.external_id,
        "name": db_user.name,
        "first_name": getattr(db_user, "first_name", None),
        "last_name": getattr(db_user, "last_name", None),
        "phone": getattr(db_user, "phone", None),
        "address": getattr(db_user, "address", None),
        "linkedin": getattr(db_user, "linkedin", None),
        "preferred_language": getattr(db_user, "preferred_language", None),
        "date_of_birth": getattr(db_user, "date_of_birth", None),
        "profile_headline": getattr(db_user, "profile_headline", None),
        "skills": getattr(db_user, "skills", None),
        "profile_picture_url": getattr(db_user, "profile_picture_url", None),
        "email": db_user.email or f"{db_user.id[:8]}@noemail.com",  # Provide unique default if None
        "picture": db_user.picture,
        "active": db_user.active,
        "preferences": db_user.preferences,
        "faiss_index_path": db_user.faiss_index_path,
        "document_summaries": summaries,
        "application_stats": stats,
        "last_active": last_active
    }
    
    logger.info(f"User data before validation: {user_data}")
    
    # Return profile using Pydantic model
    return UserProfileOut(**user_data) 