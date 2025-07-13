from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User, GeneratedCoverLetter

router = APIRouter(prefix="/documents", tags=["Documents"])

class DocumentOut(BaseModel):
    id: str
    user_id: str
    type: str
    name: str
    content: str
    date_created: datetime
    date_updated: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


@router.get("/cover-letters/latest", response_model=DocumentOut)
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

    # Adapt the result to the DocumentOut schema, which the frontend expects
    return DocumentOut(
        id=document.id,
        user_id=document.user_id,
        type="cover_letter",
        name="Latest Cover Letter",
        content=document.content,
        date_created=document.created_at,
        date_updated=document.created_at, # Assuming updated=created for this case
        metadata={}
    )


class CoverLetterUpdateRequest(BaseModel):
    content: str


@router.put("/cover-letters/latest", status_code=status.HTTP_200_OK)
async def update_latest_cover_letter(
    request: CoverLetterUpdateRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Finds and updates the content of the most recent cover letter.
    """
    # 1. Find the latest document for the user
    result = await db.execute(
        select(GeneratedCoverLetter)
        .where(GeneratedCoverLetter.user_id == user.id)
        .order_by(desc(GeneratedCoverLetter.created_at))
        .limit(1)
    )
    latest_document = result.scalar_one_or_none()

    if not latest_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cover letter found to update.",
        )

    # 2. Update its content and save to the database
    latest_document.content = request.content
    db.add(latest_document)
    await db.commit()

    return {"message": "Latest cover letter updated successfully."}


@router.put("/cover-letters/{document_id}", status_code=status.HTTP_200_OK)
async def update_cover_letter(
    document_id: str,
    request: CoverLetterUpdateRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the content of a specific cover letter.
    """
    result = await db.execute(
        select(GeneratedCoverLetter).where(
            GeneratedCoverLetter.id == document_id,
            GeneratedCoverLetter.user_id == user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you do not have permission to edit it.",
        )

    document.content = request.content
    db.add(document)
    await db.commit()

    return {"message": "Cover letter updated successfully."}