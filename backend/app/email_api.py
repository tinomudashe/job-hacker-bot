"""
API endpoints for email generation and management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.email_tools import EmailGenerator, EmailContext, EmailTemplate, EmailTracker
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/email", tags=["email"])

# Initialize email generator and tracker with Claude
email_generator = EmailGenerator(
    llm=ChatAnthropic(
        model="claude-3-7-sonnet-20250219",
        temperature=0.7,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
)
email_tracker = EmailTracker()


class EmailGenerationRequest(BaseModel):
    """Request model for email generation"""
    context: EmailContext
    template_type: Optional[str] = "custom"


class EmailFollowUpRequest(BaseModel):
    """Request model for follow-up generation"""
    original_context: EmailContext
    days_since: int
    previous_response: Optional[str] = None


class EmailImprovementRequest(BaseModel):
    """Request model for email improvement"""
    email_draft: str


class URLExtractionRequest(BaseModel):
    """Request to extract job info from URL"""
    url: str


class EmailSequenceRequest(BaseModel):
    """Request for email sequence generation"""
    context: EmailContext
    sequence_type: str = "job_application"


@router.post("/generate")
async def generate_email(request: EmailGenerationRequest) -> Dict[str, Any]:
    """Generate an email based on provided context"""
    try:
        email = await email_generator.generate_email(
            context=request.context,
            template_type=request.template_type
        )
        
        # Track the email
        email_id = email_tracker.track_email(email, request.context)
        
        return {
            "success": True,
            "email": email.dict(),
            "email_id": email_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/follow-up")
async def generate_follow_up(request: EmailFollowUpRequest) -> Dict[str, Any]:
    """Generate a follow-up email"""
    try:
        email = await email_generator.generate_follow_up(
            original_context=request.original_context,
            days_since=request.days_since,
            previous_response=request.previous_response
        )
        
        # Track the follow-up
        email_id = email_tracker.track_email(email, request.original_context)
        
        return {
            "success": True,
            "email": email.dict(),
            "email_id": email_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improve")
async def improve_email(request: EmailImprovementRequest) -> Dict[str, Any]:
    """Suggest improvements for an email draft"""
    try:
        improvements = await email_generator.suggest_improvements(
            email_draft=request.email_draft
        )
        
        return {
            "success": True,
            "improvements": improvements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-from-url")
async def extract_from_url(request: URLExtractionRequest) -> Dict[str, Any]:
    """Extract job information from a URL"""
    try:
        job_info = await email_generator.extract_job_info_from_url(request.url)
        
        # Create context from extracted info
        context = {
            "company_name": job_info.get("company_name", ""),
            "job_title": job_info.get("job_title", ""),
            "job_url": job_info.get("url", ""),
            "additional_context": job_info.get("description", "")
        }
        
        return {
            "success": True,
            "job_info": job_info,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sequence")
async def create_email_sequence(request: EmailSequenceRequest) -> Dict[str, Any]:
    """Create a sequence of follow-up emails"""
    try:
        emails = await email_generator.create_email_sequence(
            context=request.context,
            sequence_type=request.sequence_type
        )
        
        # Schedule the follow-ups
        for email in emails:
            if email.follow_up_schedule:
                send_date = datetime.fromisoformat(
                    email.follow_up_schedule["send_date"]
                )
                email_tracker.schedule_follow_up(
                    email, request.context, send_date
                )
        
        return {
            "success": True,
            "emails": [email.dict() for email in emails],
            "total": len(emails)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracker/sent")
async def get_sent_emails() -> Dict[str, Any]:
    """Get list of sent emails"""
    return {
        "success": True,
        "emails": email_tracker.sent_emails,
        "total": len(email_tracker.sent_emails)
    }


@router.get("/tracker/scheduled")
async def get_scheduled_emails() -> Dict[str, Any]:
    """Get list of scheduled emails"""
    return {
        "success": True,
        "emails": email_tracker.scheduled_emails,
        "total": len(email_tracker.scheduled_emails)
    }


@router.get("/tracker/pending")
async def get_pending_follow_ups() -> Dict[str, Any]:
    """Get emails that need to be sent"""
    pending = email_tracker.get_pending_follow_ups()
    return {
        "success": True,
        "pending": pending,
        "total": len(pending)
    }


@router.get("/templates")
async def get_email_templates() -> Dict[str, Any]:
    """Get available email templates"""
    return {
        "success": True,
        "templates": [
            {
                "key": "initial_application",
                "name": "Job Application",
                "description": "Initial job application email"
            },
            {
                "key": "follow_up_after_application",
                "name": "Application Follow-up",
                "description": "Follow up after submitting an application"
            },
            {
                "key": "thank_you_after_interview",
                "name": "Thank You Note",
                "description": "Thank you email after an interview"
            },
            {
                "key": "networking",
                "name": "Networking Outreach",
                "description": "Professional networking email"
            },
            {
                "key": "informational_interview",
                "name": "Informational Interview",
                "description": "Request for informational interview"
            }
        ]
    }


@router.post("/tracker/mark-replied/{email_id}")
async def mark_email_replied(email_id: str) -> Dict[str, Any]:
    """Mark an email as replied"""
    for email in email_tracker.sent_emails:
        if email["id"] == email_id:
            email["status"] = "replied"
            return {"success": True, "message": "Email marked as replied"}
    
    raise HTTPException(status_code=404, detail="Email not found")