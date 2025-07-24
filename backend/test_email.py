import asyncio
import os
import sys
from dotenv import load_dotenv

# --- STEP 1: Set up the environment FIRST ---

# Get the absolute path to the 'backend' directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root (one level up from 'backend') and add it to the path
project_root = os.path.dirname(backend_dir)
sys.path.append(project_root)

# CORRECTED: The .env file is in the 'backend' directory.
dotenv_path = os.path.join(backend_dir, '.env')

print(f"--- Loading environment variables from: {dotenv_path} ---")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"\n❌ ERROR: .env file not found at '{dotenv_path}'.")
    print("Please ensure your .env file is in the backend/ directory.")
    sys.exit(1) # Exit if .env is not found

# --- STEP 2: Now that the environment is loaded, import the app code ---

# This import must happen AFTER load_dotenv()
from app.email_service import send_welcome_email

async def send_test_email():
    """
    Sends a single test email using the loaded environment variables.
    """
    # We can now be confident the environment variables are loaded
    if not os.getenv("MAIL_USERNAME") or not os.getenv("MAIL_PASSWORD"):
        print("\n❌ ERROR: Email service credentials not found even after loading .env file.")
        print("Please double-check your backend/.env file for correct MAIL_USERNAME and MAIL_PASSWORD.")
        return

    test_recipient = "jnrhapson@yahoo.com"
    print(f"\n🚀 Attempting to send a test welcome email to: {test_recipient}")
    
    try:
        await send_welcome_email(recipient=test_recipient, name="Test User")
        print(f"\n✅ Success! The test email has been sent to {test_recipient}.")
        print("Please check your inbox (and spam folder).")
    except Exception as e:
        print(f"\n❌ An error occurred while sending the email: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_email()) 