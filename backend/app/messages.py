from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import json
import logging

from app.db import get_db
from app.models_db import ChatMessage, User,Page
from app.dependencies import get_current_active_user
from pydantic import BaseModel, Field
from datetime import datetime

import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessageResponse(BaseModel):
    id: str
    content: str | dict
    is_user_message: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, orm_model: ChatMessage):
        try:
            # First, try to load the message as JSON
            content = json.loads(orm_model.message)
        except (json.JSONDecodeError, TypeError):
            # If it fails, it's a plain string
            content = orm_model.message
        
        return cls(
            id=orm_model.id,
            content=content,
            is_user_message=orm_model.is_user_message,
            created_at=orm_model.created_at
        )

class UpdateMessageRequest(BaseModel):
    content: str

class Chat(BaseModel):
    id: str
    title: str

@router.get("/chats", response_model=List[Chat])
async def get_chats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all chats for the current user.
    """
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .where(ChatMessage.deleted_at.is_(None))  # Filter out soft-deleted messages
        .order_by(ChatMessage.created_at.desc())
    )
    messages = result.scalars().all()

    chats = []
    if messages:
        # For simplicity, we'll treat each day as a new chat
        # A more robust solution would involve grouping by conversation ID
        chats = []
        current_chat_date = None
        for msg in messages:
            if current_chat_date != msg.created_at.date():
                chats.append(Chat(id=msg.id, title=f"Chat from {msg.created_at.strftime('%Y-%m-%d')}"))
                current_chat_date = msg.created_at.date()

    return chats

@router.get("/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    page_id: Optional[str] = Query(None, description="Filter messages by page ID"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve chat messages for the current user, optionally filtered by page.
    Supports pagination for better performance with large conversations.
    """
    query = select(ChatMessage).where(
        ChatMessage.user_id == current_user.id
    ).where(
        ChatMessage.deleted_at.is_(None)  # Filter out soft-deleted messages
    )
    
    if page_id:
        query = query.where(ChatMessage.page_id == page_id)
    else:
        # If no page_id specified, get messages without a page (legacy behavior)
        query = query.where(ChatMessage.page_id.is_(None))
    
    # Add pagination and ordering
    query = query.order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    return [ChatMessageResponse.from_orm_model(msg) for msg in messages]

@router.delete("/clear-history", status_code=204)
async def clear_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all chat messages for the current user.
    """
    await db.execute(
        ChatMessage.__table__.delete().where(ChatMessage.user_id == current_user.id)
    )
    await db.execute(
        Page.__table__.delete().where(Page.user_id == current_user.id)
    )
    await db.commit()
    return

@router.delete("/chat/clear-history", status_code=204)
async def clear_chat_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all chat messages for the current user (alternate endpoint for frontend compatibility).
    """
    await db.execute(
        ChatMessage.__table__.delete().where(ChatMessage.user_id == current_user.id)
    )
    await db.execute(
        Page.__table__.delete().where(Page.user_id == current_user.id)
    )
    await db.commit()
    return

@router.delete("/messages/{message_id}", status_code=204)
async def delete_message(
    message_id: str,
    cascade: bool = False,
    above: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific message.
    If cascade is true, also deletes all subsequent messages in the conversation.
    If above is true, only deletes messages after the specified message.
    """
    logger.info(f"Delete message request: message_id={message_id}, cascade={cascade}, above={above}, user={current_user.id}")
    
    # Validate UUID format
    try:
        uuid.UUID(message_id)
    except ValueError:
        logger.warning(f"Invalid message ID format: {message_id}")
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if message is None:
        # Check if the message might have already been soft-deleted
        deleted_result = await db.execute(
            select(ChatMessage).where(
                ChatMessage.id == message_id,
                ChatMessage.deleted_at.isnot(None)
            )
        )
        deleted_message = deleted_result.scalar_one_or_none()
        
        if deleted_message:
            # Message was already deleted, return success
            logger.info(f"Message {message_id} was already soft-deleted, returning success")
            return
        
        # Message doesn't exist at all
        logger.warning(f"Message {message_id} not found in database for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Message not found")
        
    if message.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to delete message {message_id} owned by user {message.user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    
    logger.info(f"Processing delete: message_id={message_id}, page_id={message.page_id}, cascade={cascade}, above={above}")
    
    if cascade:
        # Get all messages after the one to be deleted
        if above:
            # Delete messages after the specified message (for regeneration)
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.user_id == current_user.id)
                .where(ChatMessage.page_id == message.page_id)
                .where(ChatMessage.created_at > message.created_at)
                .order_by(ChatMessage.created_at)
            )
        else:
            # Delete the message and all subsequent messages
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.user_id == current_user.id)
                .where(ChatMessage.page_id == message.page_id)
                .where(ChatMessage.created_at >= message.created_at)
                .order_by(ChatMessage.created_at)
            )
        messages_to_delete = result.scalars().all()
        logger.info(f"Soft deleting {len(messages_to_delete)} messages (cascade={cascade}, above={above})")
        from datetime import datetime
        for msg in messages_to_delete:
            logger.debug(f"  - Soft deleting message {msg.id}: {msg.message[:50] if msg.message else 'empty'}...")
            msg.deleted_at = datetime.utcnow()
    else:
        from datetime import datetime
        message.deleted_at = datetime.utcnow()
        logger.info(f"Soft deleting single message {message.id}")
    
    try:
        await db.commit()
        logger.info(f"Successfully deleted message(s) for message_id={message_id}")
    except Exception as e:
        logger.error(f"Failed to commit message deletion: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete message")
    
    return

@router.put("/messages/{message_id}", response_model=ChatMessageResponse)
async def update_message(
    message_id: str,
    request: UpdateMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a specific message.
    """
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.id == message_id,
            ChatMessage.deleted_at.is_(None)
        )
    )
    message = result.scalar_one_or_none()
    
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
        
    if message.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this message")
        
    message.content = request.content
    await db.commit()
    await db.refresh(message)
    
    return ChatMessageResponse.from_orm_model(message)



@router.get("/messages/debug/orphaned", response_model=List[ChatMessageResponse])
async def get_orphaned_messages(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Debug endpoint: Get messages that have no page association (page_id is NULL).
    These might be orphaned messages from before the page system was implemented
    or due to bugs in message regeneration.
    """
    query = select(ChatMessage).where(
        ChatMessage.user_id == current_user.id,
        ChatMessage.page_id.is_(None),
        ChatMessage.deleted_at.is_(None)  # Filter out soft-deleted messages
    ).order_by(ChatMessage.created_at.desc())
    
    result = await db.execute(query)
    messages = result.scalars().all()
    return [ChatMessageResponse.from_orm_model(msg) for msg in messages]

@router.get("/messages/debug/by-page")
async def get_messages_by_page(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Debug endpoint: Get all messages grouped by page_id to understand message distribution.
    """
    from sqlalchemy import func
    
    # Get count of messages per page
    query = select(
        ChatMessage.page_id,
        func.count(ChatMessage.id).label('message_count'),
        func.min(ChatMessage.created_at).label('first_message'),
        func.max(ChatMessage.created_at).label('last_message')
    ).where(
        ChatMessage.user_id == current_user.id
    ).group_by(ChatMessage.page_id).order_by(ChatMessage.page_id)
    
    result = await db.execute(query)
    page_stats = result.all()
    
    return {
        "total_pages": len([p for p in page_stats if p.page_id is not None]),
        "orphaned_messages": next((p.message_count for p in page_stats if p.page_id is None), 0),
        "page_stats": [
            {
                "page_id": p.page_id,
                "message_count": p.message_count,
                "first_message": p.first_message.isoformat() if p.first_message else None,
                "last_message": p.last_message.isoformat() if p.last_message else None,
            } for p in page_stats
        ]
    } 