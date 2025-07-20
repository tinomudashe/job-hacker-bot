import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables before any application imports
load_dotenv()

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import the necessary parts of your application
from app.models_db import User
from app.clerk import get_primary_email_address

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set in your .env file.")

engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# --- Main Logic ---
async def fix_user_emails():
    """
    Iterates through users in the database and corrects placeholder emails
    by fetching the primary email from the Clerk API.
    """
    logger.info("--- Starting script to fix existing user emails ---")
    
    async with async_session_maker() as session:
        # Find all users with known placeholder email patterns
        result = await session.execute(
            select(User).where(
                (User.email.like('%@example.com')) |
                (User.email.like('%@placeholder.jobhacker.com')) |
                (User.email.like('%@auth0-client.com'))
            )
        )
        users_to_fix = result.scalars().all()

        if not users_to_fix:
            logger.info("✅ No users with placeholder emails found. Your database is clean.")
            return

        logger.info(f"Found {len(users_to_fix)} users with placeholder emails. Starting update process...")
        
        fixed_count = 0
        failed_count = 0

        for user in users_to_fix:
            logger.info(f"Processing user ID: {user.external_id} with current email: {user.email}")
            
            try:
                correct_email = await get_primary_email_address(user.external_id)
                
                if correct_email and correct_email.lower() != user.email.lower():
                    # Update the user's email in the database
                    await session.execute(
                        update(User)
                        .where(User.id == user.id)
                        .values(email=correct_email)
                    )
                    logger.info(f"  -> SUCCESS: Updated email to {correct_email}")
                    fixed_count += 1
                elif correct_email:
                    logger.info(f"  -> SKIPPED: Email {correct_email} is already correct.")
                else:
                    logger.warning(f"  -> FAILED: Could not find a primary email in Clerk for user {user.external_id}.")
                    failed_count += 1
            except Exception as e:
                logger.error(f"  -> ERROR: An unexpected error occurred for user {user.external_id}: {e}")
                failed_count += 1
        
        if fixed_count > 0:
            await session.commit()
            logger.info("Database changes have been committed.")
        else:
            await session.rollback() # No changes needed, rollback
        
        logger.info("--- Script finished ---")
        logger.info(f"Summary: {fixed_count} users updated, {failed_count} users failed or had no valid email.")

if __name__ == "__main__":
    asyncio.run(fix_user_emails()) 