from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
import uuid

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User, GeneratedCoverLetter

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("/cover-letters/latest")
async def get_latest_cover_letter(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches the most recently created cover letter for the current user.
    """
    result = await db.execute(
        select(GeneratedCoverLetter)
        .where(GeneratedCoverLetter.user_id == user.id)
        .order_by(desc(GeneratedCoverLetter.created_at))
        .limit(1)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cover letters found for this user.",
        )

    return document