from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models_db import User, MarketingEmailTemplate
from pydantic import BaseModel
from app.dependencies import get_current_active_user # Assuming you have a dependency for admin users
from typing import List
import logging
from app.email_service import send_email, fm as mail_client # Import the configured mail client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/marketing", tags=["marketing"])

# --- Pydantic Models for Marketing ---

class MarketingTemplateBase(BaseModel):
    name: str
    subject: str
    content: str # Expecting HTML content

class MarketingTemplateCreate(MarketingTemplateBase):
    pass

class MarketingTemplateResponse(MarketingTemplateBase):
    id: str

    class Config:
        from_attributes = True

class SendMarketingEmailRequest(BaseModel):
    template_id: str
    # target_all_users: bool = False # Optional: to target all users, not just subscribed ones

# --- Admin Dependency (Placeholder) ---

async def get_admin_user(current_user: User = Depends(get_current_active_user)):
    # NOTE: You should replace this with your actual admin role check
    # For now, we'll just check if the user is active.
    # In a real app, you might have `if not current_user.is_admin:`
    if not current_user.active: # Replace with a real admin check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    return current_user

# --- API Endpoints for Marketing Management ---

@router.post("/templates", response_model=MarketingTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_marketing_template(
    template_create: MarketingTemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Create a new marketing email template. (Admin only)
    """
    logger.info(f"Admin {admin_user.id} creating marketing template: {template_create.name}")
    
    new_template = MarketingEmailTemplate(**template_create.dict())
    
    db.add(new_template)
    try:
        await db.commit()
        await db.refresh(new_template)
        return new_template
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating marketing template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template.")

@router.get("/templates", response_model=List[MarketingTemplateResponse])
async def list_marketing_templates(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    List all marketing email templates. (Admin only)
    """
    logger.info(f"Admin {admin_user.id} listing marketing templates")
    result = await db.execute(select(MarketingEmailTemplate).order_by(MarketingEmailTemplate.name))
    return result.scalars().all()


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_marketing_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Deletes a marketing email template by its ID. (Admin only)
    """
    logger.info(f"Admin {admin_user.id} requesting to delete template {template_id}")
    
    template = await db.get(MarketingEmailTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")

    try:
        await db.delete(template)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting template {template_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete template.")


async def send_bulk_emails_background(users: List[User], template: MarketingEmailTemplate):
    """
    Background task to send emails to a list of users.
    """
    logger.info(f"BACKGROUND TASK STARTED: Preparing to send '{template.subject}' to {len(users)} users.")
    if not users:
        logger.warning("Background email task started, but no users were provided.")
        return

    sent_count = 0
    failed_count = 0
    for user in users:
        if user.email and user.subscribed_to_marketing:
            try:
                # Personalize the email content. You can add more placeholders.
                personalized_content = template.content.replace("{{first_name}}", user.first_name or "there")
                personalized_content = personalized_content.replace("{{email}}", user.email)
                
                await send_email(
                    fm_instance=mail_client,
                    to=[user.email],
                    subject=template.subject,
                    html_content=personalized_content
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending email to {user.email} in background task: {e}", exc_info=True)
                failed_count += 1
    
    logger.info(f"BACKGROUND TASK FINISHED: Sent {sent_count} emails, {failed_count} failed.")

@router.post("/send-email", status_code=status.HTTP_202_ACCEPTED)
async def send_marketing_email(
    request: SendMarketingEmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Send a marketing email to all subscribed users using a template. (Admin only)
    This process runs in the background.
    """
    logger.info(f"Admin {admin_user.id} requesting to send email with template {request.template_id}")

    # 1. Get the template
    template = await db.get(MarketingEmailTemplate, request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Marketing template not found.")

    # 2. Get all subscribed users
    result = await db.execute(
        select(User).where(User.subscribed_to_marketing == True)
    )
    subscribed_users = result.scalars().all()
    
    logger.info(f"Found {len(subscribed_users)} subscribed users to email.")

    if not subscribed_users:
        return {"message": "No subscribed users to send email to."}

    # 3. Add the email sending job to background tasks
    background_tasks.add_task(send_bulk_emails_background, subscribed_users, template)
    
    return {"message": f"Email campaign scheduled. {len(subscribed_users)} emails will be sent in the background."} 