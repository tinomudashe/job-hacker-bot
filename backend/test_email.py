import asyncio
import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import logging

# --- Basic Configuration ---
# Configure logging to see detailed output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from your .env file
load_dotenv()

# --- Main Test Function ---
async def send_test_email():
    """
    Initializes FastAPI-Mail and attempts to send a single test email.
    """
    logger.info("--- Starting Email Service Test ---")
    
    # 1. Load configuration from environment variables
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    mail_from = os.getenv("MAIL_FROM")
    mail_port = int(os.getenv("MAIL_PORT", 587))
    mail_server = os.getenv("MAIL_SERVER")
    mail_starttls = str(os.getenv("MAIL_STARTTLS", "True")).lower() == 'true'
    mail_ssl_tls = str(os.getenv("MAIL_SSL_TLS", "False")).lower() == 'true'

    # Log the loaded configuration to verify it's correct
    logger.info(f"Loaded configuration:")
    logger.info(f"  - MAIL_USERNAME: {mail_username}")
    logger.info(f"  - MAIL_FROM: {mail_from}")
    logger.info(f"  - MAIL_SERVER: {mail_server}:{mail_port}")
    logger.info(f"  - MAIL_STARTTLS: {mail_starttls}")
    logger.info(f"  - MAIL_SSL_TLS: {mail_ssl_tls}")

    if not all([mail_username, mail_password, mail_from, mail_server]):
        logger.error("One or more required environment variables are missing.")
        return

    # 2. Create the ConnectionConfig
    conf = ConnectionConfig(
        MAIL_USERNAME=mail_username,
        MAIL_PASSWORD=mail_password,
        MAIL_FROM=mail_from,
        MAIL_PORT=mail_port,
        MAIL_SERVER=mail_server,
        MAIL_STARTTLS=mail_starttls,
        MAIL_SSL_TLS=mail_ssl_tls,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TIMEOUT=60  # Increased timeout for debugging
    )

    # 3. Create the email message
    recipient_email = "jnrhapson@yahoo.com"
    
    message = MessageSchema(
        subject="FastAPI-Mail Test",
        recipients=[recipient_email],
        body="This is a test email sent from the FastAPI-Mail test script.",
        subtype="html"
    )

    # 4. Send the email
    fm = FastMail(conf)
    try:
        logger.info(f"Attempting to send a test email to {recipient_email}...")
        await fm.send_message(message)
        logger.info("✅ --- Test SUCCEEDED: Email sent successfully! ---")
        logger.info("Please check your inbox (and spam folder) to confirm.")
    except Exception as e:
        logger.error(f"❌ --- Test FAILED: An error occurred ---")
        logger.error(f"Error details: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(send_test_email()) 