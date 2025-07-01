"""
Internal API functions for authenticated WebSocket access.

This module provides internal versions of HTTP endpoints that can be called
directly from WebSocket connections using already authenticated User objects,
bypassing the need for HTTP authentication headers.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models_db import User, Resume, Document, Application
from app.models import User as UserSchema
from app.resume import ResumeData, PersonalInfo, Experience, Education, fix_resume_data_structure

logger = logging.getLogger(__name__)

# --- Internal User API Functions ---

async def get_user_data_internal(user: User, db: AsyncSession) -> Dict[str, Any]:
    """
    Internal version of GET /api/users/me
    Returns user data for an authenticated user object.
    """
    try:
        # Convert User model to dictionary format matching the API response
        return {
            "id": user.id,
            "external_id": user.external_id,
            "name": user.name,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "address": user.address,
            "linkedin": user.linkedin,
            "preferred_language": user.preferred_language,
            "date_of_birth": user.date_of_birth,
            "profile_headline": user.profile_headline,
            "skills": user.skills,
            "picture": user.picture,
            "profile_picture_url": user.profile_picture_url,
            "active": user.active,
            "preferences": user.preferences,
            "faiss_index_path": user.faiss_index_path
        }
    except Exception as e:
        logger.error(f"Error getting user data for user {user.id}: {e}")
        raise

async def get_resume_data_internal(user: User, db: AsyncSession) -> Dict[str, Any]:
    """
    Internal version of GET /api/resume
    Returns resume data for an authenticated user object.
    """
    try:
        result = await db.execute(
            select(Resume).where(Resume.user_id == user.id)
        )
        resume = result.scalars().first()

        if resume and resume.data:
            # Fix data structure to ensure required IDs exist
            fixed_data = fix_resume_data_structure(resume.data)
            return fixed_data
        
        # Return a default empty structure if no resume data is found
        return {
            "personalInfo": {
                "name": user.name or "",
                "email": user.email or "",
                "phone": user.phone or "",
                "linkedin": user.linkedin or "",
                "location": user.address or "",
                "summary": user.profile_headline or ""
            },
            "experience": [],
            "education": [],
            "skills": user.skills.split(", ") if user.skills else [],
            "projects": [],
            "certifications": [],
            "languages": [],
            "interests": []
        }
    except Exception as e:
        logger.error(f"Error getting resume data for user {user.id}: {e}")
        raise

async def update_resume_data_internal(user: User, resume_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """
    Internal version of PUT /api/resume
    Updates resume data for an authenticated user object.
    """
    try:
        result = await db.execute(
            select(Resume).where(Resume.user_id == user.id)
        )
        db_resume = result.scalars().first()

        # Ensure proper structure
        fixed_data = fix_resume_data_structure(resume_data)

        if db_resume:
            db_resume.data = fixed_data
        else:
            db_resume = Resume(
                user_id=user.id,
                data=fixed_data
            )
            db.add(db_resume)
        
        await db.commit()
        await db.refresh(db_resume)
        
        return db_resume.data
    except Exception as e:
        logger.error(f"Error updating resume data for user {user.id}: {e}")
        await db.rollback()
        raise

async def get_user_documents_internal(user: User, db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Internal version of GET /api/users/me/documents
    Returns user's documents for an authenticated user object.
    """
    try:
        result = await db.execute(
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.date_created.desc())
        )
        documents = result.scalars().all()
        
        return [
            {
                "id": doc.id,
                "type": doc.type,
                "name": doc.name,
                "date_created": doc.date_created.isoformat() if doc.date_created else None,
                "date_updated": doc.date_updated.isoformat() if doc.date_updated else None
            }
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error getting documents for user {user.id}: {e}")
        raise

async def get_user_applications_internal(user: User, db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Internal version of GET /api/users/me/applications
    Returns user's job applications for an authenticated user object.
    """
    try:
        result = await db.execute(
            select(Application)
            .where(Application.user_id == user.id)
            .order_by(Application.date_applied.desc())
        )
        applications = result.scalars().all()
        
        return [
            {
                "id": app.id,
                "job_title": app.job_title,
                "company_name": app.company_name,
                "job_url": app.job_url,
                "status": app.status,
                "notes": app.notes,
                "date_applied": app.date_applied.isoformat() if app.date_applied else None,
                "success": app.success
            }
            for app in applications
        ]
    except Exception as e:
        logger.error(f"Error getting applications for user {user.id}: {e}")
        raise

async def get_user_profile_internal(user: User, db: AsyncSession) -> Dict[str, Any]:
    """
    Internal version of GET /api/users/profile
    Returns complete user profile with documents and application stats.
    """
    try:
        # Get documents
        documents = await get_user_documents_internal(user, db)
        
        # Get applications  
        applications = await get_user_applications_internal(user, db)
        
        # Create summaries
        summaries = []
        for doc in documents:
            summary = f"{doc['type'].title()} ({doc['name']})"
            summaries.append(summary)

        # Application stats
        stats = {
            "total_applications": len(applications),
            "last_applied": applications[0]["date_applied"] if applications else None,
            "statuses": {}
        }
        
        # Count statuses
        for app in applications:
            status = app["status"]
            stats["statuses"][status] = stats["statuses"].get(status, 0) + 1

        # User data
        user_data = await get_user_data_internal(user, db)
        
        # Add profile-specific fields
        user_data.update({
            "document_summaries": summaries,
            "application_stats": stats,
            "last_active": documents[0]["date_created"] if documents else applications[0]["date_applied"] if applications else None
        })
        
        return user_data
    except Exception as e:
        logger.error(f"Error getting profile for user {user.id}: {e}")
        raise

# --- Public API for WebSocket Integration ---

class InternalAPI:
    """
    Public interface for internal API functions.
    Used by WebSocket connections that already have authenticated User objects.
    """
    
    @staticmethod
    async def get_user_data(user: User, db: AsyncSession) -> Dict[str, Any]:
        """Get user data (equivalent to GET /api/users/me)"""
        return await get_user_data_internal(user, db)
    
    @staticmethod
    async def get_resume_data(user: User, db: AsyncSession) -> Dict[str, Any]:
        """Get resume data (equivalent to GET /api/resume)"""
        return await get_resume_data_internal(user, db)
    
    @staticmethod
    async def update_resume_data(user: User, resume_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Update resume data (equivalent to PUT /api/resume)"""
        return await update_resume_data_internal(user, resume_data, db)
    
    @staticmethod
    async def get_user_documents(user: User, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get user documents (equivalent to GET /api/users/me/documents)"""
        return await get_user_documents_internal(user, db)
    
    @staticmethod
    async def get_user_applications(user: User, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get user applications (equivalent to GET /api/users/me/applications)"""
        return await get_user_applications_internal(user, db)
    
    @staticmethod
    async def get_user_profile(user: User, db: AsyncSession) -> Dict[str, Any]:
        """Get complete user profile (equivalent to GET /api/users/profile)"""
        return await get_user_profile_internal(user, db)


# --- Utility function for WebSocket tools ---

async def make_internal_api_call(
    endpoint: str, 
    user: User, 
    db: AsyncSession,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    General purpose function to make internal API calls from WebSocket tools.
    
    Args:
        endpoint: The endpoint to call (e.g., '/api/users/me', '/api/resume')
        user: Authenticated user object
        db: Database session
        data: Optional data for PUT/POST requests
        
    Returns:
        Response data as dictionary
    """
    try:
        if endpoint == "/api/users/me":
            return await InternalAPI.get_user_data(user, db)
        elif endpoint == "/api/resume":
            if data:  # PUT request
                return await InternalAPI.update_resume_data(user, data, db)
            else:  # GET request
                return await InternalAPI.get_resume_data(user, db)
        elif endpoint == "/api/users/me/documents":
            return await InternalAPI.get_user_documents(user, db)
        elif endpoint == "/api/users/me/applications":
            return await InternalAPI.get_user_applications(user, db)
        elif endpoint == "/api/users/profile":
            return await InternalAPI.get_user_profile(user, db)
        else:
            raise ValueError(f"Unsupported internal API endpoint: {endpoint}")
            
    except Exception as e:
        logger.error(f"Error in internal API call to {endpoint}: {e}")
        raise 