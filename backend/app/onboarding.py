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
        logger.info(f"Starting onboarding completion for user {current_user.id}")
        
        # Parse existing preferences or create new dict
        import json
        if current_user.preferences:
            if isinstance(current_user.preferences, str):
                preferences = json.loads(current_user.preferences)
            else:
                preferences = current_user.preferences
        else:
            preferences = {}
        
        # Update preferences
        preferences["onboarding_completed"] = request.completed
        preferences["cv_uploaded_at"] = datetime.utcnow().isoformat()
        preferences["onboarding_completed_at"] = datetime.utcnow().isoformat()
        
        if request.additional_data:
            preferences.update(request.additional_data)
        
        # Save to database - ensure preferences is JSON serialized
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(preferences=json.dumps(preferences))
        )
        await db.commit()
        
        logger.info(f"Database updated successfully for user {current_user.id}")
        
        # Try to update Clerk metadata, but don't fail if it doesn't work
        clerk_metadata_updated = False
        try:
            # Use external_id (Clerk user ID) instead of internal database ID
            clerk_metadata_updated = await update_user_metadata(
                current_user.external_id,
                {
                    "onboardingCompleted": request.completed,
                    "cvUploaded": request.cv_uploaded
                }
            )
            if clerk_metadata_updated:
                logger.info(f"Clerk metadata updated successfully for user {current_user.id}")
            else:
                logger.warning(f"Clerk metadata update returned false for user {current_user.id}")
        except Exception as clerk_error:
            logger.warning(f"Failed to update Clerk metadata for user {current_user.id}: {clerk_error}. Continuing anyway.")
        
        logger.info(f"Onboarding completed for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "onboarding_completed": request.completed,
            "cv_uploaded": request.cv_uploaded,
            "clerk_updated": clerk_metadata_updated
        }
        
    except Exception as e:
        logger.error(f"Error completing onboarding for user {current_user.id}: {str(e)}", exc_info=True)
        await db.rollback()  # Rollback any changes
        raise HTTPException(status_code=500, detail=f"Failed to complete onboarding: {str(e)}")

@router.get("/users/onboarding/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current onboarding status for a user
    """
    try:
        import json
        # Parse preferences if it's a string
        if current_user.preferences:
            if isinstance(current_user.preferences, str):
                preferences = json.loads(current_user.preferences)
            else:
                preferences = current_user.preferences
        else:
            preferences = {}
        
        onboarding_completed = preferences.get("onboarding_completed", False)
        cv_uploaded = preferences.get("cv_uploaded_at") is not None
        
        return {
            "onboarding_completed": onboarding_completed,
            "cv_uploaded": cv_uploaded,
            "user_id": current_user.id,
            "completed_at": preferences.get("onboarding_completed_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting onboarding status for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get onboarding status")