import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models_db import User

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")

engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def delete_orphaned_users():
    """
    Finds and deletes user records that have a placeholder email AND a missing external_id.
    """
    logger.info("--- Starting script to delete orphaned user records ---")

    async with async_session_maker() as session:
        # This query is very specific to find only the broken records.
        stmt = select(User).where(
            (User.external_id == None) &
            (
                (User.email.like('%@example.com')) |
                (User.email.like('%@placeholder.jobhacker.com')) |
                (User.email.like('%@auth0-client.com'))
            )
        )
        result = await session.execute(stmt)
        users_to_delete = result.scalars().all()

        if not users_to_delete:
            logger.info("✅ No orphaned user records found to delete.")
            return

        logger.warning(f"Found {len(users_to_delete)} orphaned records that will be permanently deleted.")
        for user in users_to_delete:
            logger.warning(f"  - Deleting User ID: {user.id}, Email: {user.email}")

        # Perform the deletion
        delete_stmt = delete(User).where(User.id.in_([u.id for u in users_to_delete]))
        delete_result = await session.execute(delete_stmt)
        await session.commit()

        logger.info(f"✅ Successfully deleted {delete_result.rowcount} orphaned user records.")

if __name__ == "__main__":
    print("⚠️  WARNING: This script will permanently delete user records from your database.")
    print("   It targets users that have both a placeholder email AND a missing external_id.")
    
    confirmation = input("   Are you sure you want to continue? (yes/no): ")

    if confirmation.lower() == 'yes':
        asyncio.run(delete_orphaned_users())
    else:
        print("Aborted. No changes were made.") 