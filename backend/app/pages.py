from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db
from app.models_db import Page, User, ChatMessage
from app.dependencies import get_current_active_user

router = APIRouter()

class PageResponse(BaseModel):
    id: str
    title: str
    created_at: str
    last_opened_at: Optional[str] = None

class CreatePageRequest(BaseModel):
    first_message: str

@router.post("/pages", response_model=PageResponse)
async def create_page(
    request: CreatePageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new page/conversation for the current user.
    """
    title = request.first_message.split('\n')[0]
    title = title.split('. ')[0]
    title = title.split('? ')[0]
    title = title.split('! ')[0]
    title = title[:50] + '...' if len(title) > 50 else title

    new_page = Page(user_id=current_user.id, title=title)
    db.add(new_page)
    await db.commit()
    await db.refresh(new_page)
    
    return PageResponse(
        id=new_page.id, 
        title=new_page.title,
        created_at=new_page.created_at.isoformat(),
        last_opened_at=new_page.last_opened_at.isoformat() if new_page.last_opened_at else None
    )

@router.get("/pages/recent", response_model=PageResponse)
async def get_most_recent_page(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the most recent page/conversation for the user"""
    result = await db.execute(
        select(Page).where(Page.user_id == current_user.id).order_by(Page.created_at.desc()).limit(1)
    )
    page = result.scalars().first()
    
    if not page:
        raise HTTPException(status_code=404, detail="No conversations found")
    
    return PageResponse(
        id=page.id, 
        title=page.title,
        created_at=page.created_at.isoformat(),
        last_opened_at=page.last_opened_at.isoformat() if page.last_opened_at else None
    )

@router.get("/pages/{page_id}", response_model=PageResponse)
async def get_single_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Get a single page by its ID."""
    result = await db.execute(
        select(Page).where(Page.id == page_id, Page.user_id == user.id)
    )
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return PageResponse(
        id=page.id,
        title=page.title,
        created_at=page.created_at.isoformat(),
        last_opened_at=page.last_opened_at.isoformat() if page.last_opened_at else None
    )

@router.get("/pages", response_model=List[PageResponse])
async def get_pages(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pages/conversations for the current user.
    """
    result = await db.execute(
        select(Page).where(Page.user_id == current_user.id).order_by(Page.created_at.desc())
    )
    pages = result.scalars().all()
    return [
        PageResponse(
            id=page.id, 
            title=page.title,
            created_at=page.created_at.isoformat(),
            last_opened_at=page.last_opened_at.isoformat() if page.last_opened_at else None
        ) for page in pages
    ]



@router.delete("/pages/{page_id}")
async def delete_page(
    page_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a page/conversation and all associated messages.
    """
    # Verify the page exists and belongs to the current user before deleting
    page_to_delete = await db.execute(
        select(Page).where(Page.id == page_id, Page.user_id == current_user.id)
    )
    page = page_to_delete.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found or you don't have permission to delete it.")
    
    # First, delete all chat messages associated with this page
    await db.execute(
        delete(ChatMessage).where(ChatMessage.page_id == page_id)
    )
    
    # Then, delete the page itself
    await db.execute(
        delete(Page).where(Page.id == page_id, Page.user_id == current_user.id)
    )
    
    await db.commit()
    return {"message": "Page deleted successfully"}