#!/usr/bin/env python3
"""
Script to clean up empty messages from the chat_messages table.
Empty messages can cause errors with the Anthropic API.

Usage:
    python cleanup_empty_messages.py                    # Clean all empty messages
    python cleanup_empty_messages.py --user-id USER_ID  # Clean for specific user
    python cleanup_empty_messages.py --dry-run          # Show what would be cleaned
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, and_
from app.db import get_db_context
from app.models_db import ChatMessage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_empty_messages(db: AsyncSession, user_id: str = None):
    """Find messages with empty or whitespace-only content"""
    query = select(ChatMessage).where(
        or_(
            ChatMessage.message == None,
            ChatMessage.message == "",
            ChatMessage.message == " ",
            ChatMessage.message == "  ",
            ChatMessage.message == "   ",
            ChatMessage.message == "\n",
            ChatMessage.message == "\n\n",
            ChatMessage.message == "\r\n",
        )
    )
    
    if user_id:
        query = query.where(ChatMessage.user_id == user_id)
    
    result = await db.execute(query)
    return result.scalars().all()


async def clean_empty_messages(db: AsyncSession, user_id: str = None, dry_run: bool = False):
    """Remove empty messages from the database"""
    empty_messages = await find_empty_messages(db, user_id)
    
    if not empty_messages:
        logger.info("No empty messages found")
        return 0
    
    logger.info(f"Found {len(empty_messages)} empty messages")
    
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        for msg in empty_messages[:10]:  # Show first 10 as examples
            logger.info(f"  Would delete: Message ID {msg.id}, User {msg.user_id}, "
                       f"Page {msg.page_id}, Content: '{msg.message}'")
        if len(empty_messages) > 10:
            logger.info(f"  ... and {len(empty_messages) - 10} more")
        return len(empty_messages)
    
    # Delete empty messages
    deleted_count = 0
    for msg in empty_messages:
        await db.delete(msg)
        deleted_count += 1
        if deleted_count % 10 == 0:
            logger.info(f"  Deleted {deleted_count}/{len(empty_messages)} messages...")
    
    await db.commit()
    logger.info(f"Successfully deleted {deleted_count} empty messages")
    return deleted_count


async def main():
    parser = argparse.ArgumentParser(description='Clean up empty messages from chat_messages table')
    parser.add_argument('--user-id', type=str, help='Clean messages for specific user only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without making changes')
    
    args = parser.parse_args()
    
    async with get_db_context() as db:
        logger.info("Starting empty message cleanup...")
        
        if args.user_id:
            logger.info(f"Cleaning messages for user: {args.user_id}")
        else:
            logger.info("Cleaning messages for all users")
        
        count = await clean_empty_messages(db, args.user_id, args.dry_run)
        
        if args.dry_run:
            logger.info(f"\nDry run complete. {count} messages would be deleted.")
        else:
            logger.info(f"\nCleanup complete. {count} messages deleted.")


if __name__ == "__main__":
    asyncio.run(main())