import asyncio
import os
import logging
from dotenv import load_dotenv

# --- CRITICAL: Load environment variables BEFORE importing app modules ---
# This ensures that when app.clerk is imported, it can see the variables.
load_dotenv()

# --- Now, we can safely import our application's function ---
from app.clerk import get_primary_email_address

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Main Test Function ---
async def check_user_email(user_id: str):
    """
    Tests the get_primary_email_address function for a specific user ID.
    """
    logger.info(f"--- Testing email retrieval for User ID: {user_id} ---")

    # The check inside the function will now work correctly.
    try:
        email = await get_primary_email_address(user_id)

        if email:
            logger.info(f"✅ SUCCESS: Found primary email: {email}")
        else:
            logger.warning(f"⚠️  INFO: No primary email address was found for this user in Clerk.")
            logger.warning("   This is expected for some user types (e.g., service accounts).")

    except Exception as e:
        logger.error(f"❌ FAILED: An unexpected error occurred during the test.", exc_info=True)


if __name__ == "__main__":
    # --- USER ID TO TEST ---
    test_user_id = "user_2yatG4oMgcQCAyYNFrenIxicV1A"
    
    # Run the asynchronous test
    asyncio.run(check_user_email(test_user_id)) 