"""
Onboarding endpoints for new user setup
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from app.dependencies import get_current_active_user
from app.models_db import User
from app.db import get_db
from app.clerk import update_user_metadata

router = APIRouter()
logger = logging.getLogger(__name__)

class OnboardingCompleteRequest(BaseModel):
    completed: bool
    cv_uploaded: bool
    additional_data: Optional[dict] = None

@router.post("/users/onboarding/complete")
async def complete_onboarding(
    request: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark user onboarding as complete after CV upload
    """
    try:
        # Update user preferences to mark onboarding as complete
        if not current_user.preferences:
            current_user.preferences = {}
        
        current_user.preferences["onboarding_completed"] = request.completed
        current_user.preferences["cv_uploaded_at"] = datetime.utcnow().isoformat()
        current_user.preferences["onboarding_completed_at"] = datetime.utcnow().isoformat()
        
        if request.additional_data:
            current_user.preferences.update(request.additional_data)
        
        # Save to database
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(preferences=current_user.preferences)
        )
        await db.commit()
        
        # Update Clerk metadata
        clerk_metadata_updated = await update_user_metadata(
            current_user.id,
            {
                "onboardingCompleted": request.completed,
                "cvUploaded": request.cv_uploaded
            }
        )
        
        if not clerk_metadata_updated:
            logger.warning(f"Failed to update Clerk metadata for user {current_user.id}, but database update succeeded")
        
        logger.info(f"Onboarding completed for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "onboarding_completed": request.completed,
            "cv_uploaded": request.cv_uploaded,
            "clerk_updated": clerk_metadata_updated
        }
        
    except Exception as e:
        logger.error(f"Error completing onboarding for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete onboarding")

@router.get("/users/onboarding/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current onboarding status for a user
    """
    try:
        onboarding_completed = current_user.preferences.get("onboarding_completed", False) if current_user.preferences else False
        cv_uploaded = current_user.preferences.get("cv_uploaded_at") is not None if current_user.preferences else False
        
        return {
            "onboarding_completed": onboarding_completed,
            "cv_uploaded": cv_uploaded,
            "user_id": current_user.id,
            "completed_at": current_user.preferences.get("onboarding_completed_at") if current_user.preferences else None
        }
        
    except Exception as e:
        logger.error(f"Error getting onboarding status for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get onboarding status")