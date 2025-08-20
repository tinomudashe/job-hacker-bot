#!/usr/bin/env python3
"""
Script to clean up duplicate assistant messages in the database.
This identifies and soft-deletes duplicate consecutive assistant messages.
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session_maker
from app.models_db import ChatMessage

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def cleanup_duplicate_messages():
    """
    Find and soft-delete duplicate consecutive assistant messages
    """
    async with async_session_maker() as db:
        try:
            # Get all pages with messages
            pages_query = await db.execute(
                select(ChatMessage.page_id, ChatMessage.user_id)
                .where(ChatMessage.deleted_at.is_(None))
                .group_by(ChatMessage.page_id, ChatMessage.user_id)
            )
            
            pages = pages_query.all()
            total_deleted = 0
            
            for page_id, user_id in pages:
                if not page_id:  # Skip messages without page_id
                    continue
                    
                # Get all messages for this page in order
                messages_query = await db.execute(
                    select(ChatMessage)
                    .where(
                        and_(
                            ChatMessage.user_id == user_id,
                            ChatMessage.page_id == page_id,
                            ChatMessage.deleted_at.is_(None)
                        )
                    )
                    .order_by(ChatMessage.created_at.asc())
                )
                
                messages = messages_query.scalars().all()
                
                # Look for consecutive assistant messages with the same content
                prev_msg = None
                duplicates_found = []
                
                for msg in messages:
                    if prev_msg and not prev_msg.is_user_message and not msg.is_user_message:
                        # Two consecutive assistant messages - check if they're duplicates
                        if prev_msg.message == msg.message:
                            # Mark the older one for deletion
                            duplicates_found.append(prev_msg)
                            log.info(f"Found duplicate assistant message in page {page_id}: {prev_msg.id}")
                    prev_msg = msg
                
                # Soft delete the duplicates
                for dup in duplicates_found:
                    dup.deleted_at = datetime.now()
                    total_deleted += 1
                
                if duplicates_found:
                    await db.commit()
                    log.info(f"Soft-deleted {len(duplicates_found)} duplicate messages in page {page_id}")
            
            log.info(f"Total duplicate messages cleaned up: {total_deleted}")
            
        except Exception as e:
            log.error(f"Error during cleanup: {e}")
            await db.rollback()
            raise


async def main():
    """Run the cleanup"""
    log.info("Starting duplicate message cleanup...")
    await cleanup_duplicate_messages()
    log.info("Cleanup completed!")


if __name__ == "__main__":
    asyncio.run(main())