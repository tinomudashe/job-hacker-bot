from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List
from pydantic import BaseModel

from app.db import get_db
from app.models_db import Page, User, ChatMessage
from app.dependencies import get_current_user

router = APIRouter()

class PageResponse(BaseModel):
    id: str
    title: str
    created_at: str

class CreatePageRequest(BaseModel):
    first_message: str

@router.post("/pages", response_model=PageResponse)
async def create_page(
    request: CreatePageRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
):
    token = authorization.split(" ")[1]
    user = await get_current_user(token=token, db=db)
    
    title = request.first_message.split('\n')[0]
    title = title.split('. ')[0]
    title = title.split('? ')[0]
    title = title.split('! ')[0]
    title = title[:50] + '...' if len(title) > 50 else title

    new_page = Page(user_id=user.id, title=title)
    db.add(new_page)
    await db.commit()
    await db.refresh(new_page)
    
    return PageResponse(
        id=new_page.id, 
        title=new_page.title,
        created_at=new_page.created_at.isoformat()
    )

@router.get("/pages", response_model=List[PageResponse])
async def get_pages(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
):
    token = authorization.split(" ")[1]
    user = await get_current_user(token=token, db=db)
    
    result = await db.execute(
        select(Page).where(Page.user_id == user.id).order_by(Page.created_at.desc())
    )
    pages = result.scalars().all()
    return [
        PageResponse(
            id=page.id, 
            title=page.title,
            created_at=page.created_at.isoformat()
        ) for page in pages
    ]

@router.get("/pages/recent", response_model=PageResponse)
async def get_most_recent_page(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
):
    """Get the most recent page/conversation for the user"""
    token = authorization.split(" ")[1]
    user = await get_current_user(token=token, db=db)
    
    result = await db.execute(
        select(Page).where(Page.user_id == user.id).order_by(Page.created_at.desc()).limit(1)
    )
    page = result.scalars().first()
    
    if not page:
        raise HTTPException(status_code=404, detail="No conversations found")
    
    return PageResponse(
        id=page.id, 
        title=page.title,
        created_at=page.created_at.isoformat()
    )

@router.delete("/pages/{page_id}")
async def delete_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
):
    token = authorization.split(" ")[1]
    user = await get_current_user(token=token, db=db)
    
    # Check if page exists and belongs to user
    result = await db.execute(
        select(Page).where(Page.id == page_id, Page.user_id == user.id)
    )
    page = result.scalars().first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Delete associated chat messages first
    await db.execute(
        delete(ChatMessage).where(ChatMessage.page_id == page_id)
    )
    
    # Delete the page
    await db.execute(
        delete(Page).where(Page.id == page_id)
    )
    
    await db.commit()
    return {"message": "Page deleted successfully"} 