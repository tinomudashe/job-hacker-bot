"""
Tailored Resumes API
Handles job-specific resume versions that don't modify the master resume
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User, Resume, TailoredResume
from app.resume import ResumeData, fix_resume_data_structure
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class CreateTailoredResumeRequest(BaseModel):
    job_title: str
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    tailored_data: Dict[str, Any]

class TailoredResumeResponse(BaseModel):
    id: str
    job_title: str
    company_name: Optional[str]
    job_description: Optional[str]
    tailored_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class TailoredResumeListResponse(BaseModel):
    id: str
    job_title: str
    company_name: Optional[str]
    created_at: datetime

@router.post("/resume/tailor", response_model=TailoredResumeResponse)
async def create_tailored_resume(
    request: CreateTailoredResumeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new tailored resume version without modifying the master resume
    """
    try:
        # Get user's master resume
        result = await db.execute(
            select(Resume).where(Resume.user_id == current_user.id)
        )
        master_resume = result.scalars().first()
        
        if not master_resume:
            raise HTTPException(
                status_code=404, 
                detail="Master resume not found. Please complete onboarding first."
            )
        
        # Fix data structure before saving
        fixed_data = fix_resume_data_structure(request.tailored_data)
        
        # Create tailored resume entry
        tailored_resume = TailoredResume(
            user_id=current_user.id,
            base_resume_id=master_resume.id,
            job_title=request.job_title,
            company_name=request.company_name,
            job_description=request.job_description,
            tailored_data=fixed_data
        )
        
        db.add(tailored_resume)
        await db.commit()
        await db.refresh(tailored_resume)
        
        logger.info(f"Created tailored resume {tailored_resume.id} for {request.job_title} at {request.company_name}")
        
        return TailoredResumeResponse(
            id=tailored_resume.id,
            job_title=tailored_resume.job_title,
            company_name=tailored_resume.company_name,
            job_description=tailored_resume.job_description,
            tailored_data=tailored_resume.tailored_data,
            created_at=tailored_resume.created_at,
            updated_at=tailored_resume.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating tailored resume: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create tailored resume")

@router.get("/resume/tailored", response_model=List[TailoredResumeListResponse])
async def list_tailored_resumes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all tailored resume versions for the user
    """
    try:
        result = await db.execute(
            select(TailoredResume)
            .where(TailoredResume.user_id == current_user.id)
            .order_by(TailoredResume.created_at.desc())
        )
        tailored_resumes = result.scalars().all()
        
        return [
            TailoredResumeListResponse(
                id=resume.id,
                job_title=resume.job_title,
                company_name=resume.company_name,
                created_at=resume.created_at
            )
            for resume in tailored_resumes
        ]
        
    except Exception as e:
        logger.error(f"Error listing tailored resumes: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tailored resumes")

@router.get("/resume/tailored/{tailored_id}", response_model=TailoredResumeResponse)
async def get_tailored_resume(
    tailored_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific tailored resume version
    """
    try:
        result = await db.execute(
            select(TailoredResume)
            .where(
                TailoredResume.id == tailored_id,
                TailoredResume.user_id == current_user.id
            )
        )
        tailored_resume = result.scalars().first()
        
        if not tailored_resume:
            raise HTTPException(status_code=404, detail="Tailored resume not found")
        
        return TailoredResumeResponse(
            id=tailored_resume.id,
            job_title=tailored_resume.job_title,
            company_name=tailored_resume.company_name,
            job_description=tailored_resume.job_description,
            tailored_data=tailored_resume.tailored_data,
            created_at=tailored_resume.created_at,
            updated_at=tailored_resume.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error getting tailored resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tailored resume")

@router.delete("/resume/tailored/{tailored_id}", status_code=204)
async def delete_tailored_resume(
    tailored_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a specific tailored resume version
    """
    try:
        result = await db.execute(
            select(TailoredResume)
            .where(
                TailoredResume.id == tailored_id,
                TailoredResume.user_id == current_user.id
            )
        )
        tailored_resume = result.scalars().first()
        
        if not tailored_resume:
            raise HTTPException(status_code=404, detail="Tailored resume not found")
        
        await db.delete(tailored_resume)
        await db.commit()
        
        logger.info(f"Deleted tailored resume {tailored_id}")
        
    except Exception as e:
        logger.error(f"Error deleting tailored resume: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete tailored resume")

@router.get("/resume/master", response_model=ResumeData)
async def get_master_resume(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the master/onboarding resume (unchanged by tailoring)
    """
    try:
        result = await db.execute(
            select(Resume).where(Resume.user_id == current_user.id)
        )
        master_resume = result.scalars().first()
        
        if not master_resume:
            raise HTTPException(status_code=404, detail="Master resume not found")
        
        # Convert to ResumeData format
        resume_data = ResumeData(**master_resume.data)
        return resume_data
        
    except Exception as e:
        logger.error(f"Error getting master resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to get master resume")