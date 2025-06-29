from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
import uuid

from app.db import get_db
from app.models_db import Application, User
from app.dependencies import get_current_active_user

router = APIRouter()

class ApplicationBase(BaseModel):
    job_title: str
    company_name: str
    job_url: HttpUrl
    status: str = "applied"
    notes: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationOut(ApplicationBase):
    id: str
    user_id: str
    date_applied: datetime

    class Config:
        from_attributes = True

@router.post("/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    application: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Create a new job application record.
    """
    new_application = Application(
        id=str(uuid.uuid4()),
        user_id=db_user.id,
        job_title=application.job_title,
        company_name=application.company_name,
        job_url=str(application.job_url),
        status=application.status,
        notes=application.notes,
        date_applied=datetime.utcnow()
    )
    db.add(new_application)
    await db.commit()
    await db.refresh(new_application)
    return new_application

@router.get("/applications", response_model=List[ApplicationOut])
async def list_applications(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    List all job applications for the current user.
    """
    result = await db.execute(
        select(Application).where(Application.user_id == db_user.id)
    )
    applications = result.scalars().all()
    return applications

@router.get("/applications/{application_id}", response_model=ApplicationOut)
async def get_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Get a single job application by its ID.
    """
    result = await db.execute(
        select(Application).where(Application.id == application_id, Application.user_id == db_user.id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

class ApplicationUpdate(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_url: Optional[HttpUrl] = None
    status: Optional[str] = None
    notes: Optional[str] = None

@router.put("/applications/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    application_update: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Update a job application.
    """
    result = await db.execute(
        select(Application).where(Application.id == application_id, Application.user_id == db_user.id)
    )
    db_application = result.scalar_one_or_none()

    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    update_data = application_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "job_url":
             setattr(db_application, key, str(value))
        else:
             setattr(db_application, key, value)

    await db.commit()
    await db.refresh(db_application)
    return db_application

@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Delete a job application.
    """
    result = await db.execute(
        select(Application).where(Application.id == application_id, Application.user_id == db_user.id)
    )
    db_application = result.scalar_one_or_none()

    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    await db.delete(db_application)
    await db.commit()
    return 