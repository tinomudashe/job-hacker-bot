import os
import logging
from typing import List

# Optional import for email service - graceful fallback if not available
try:
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
    from pydantic import EmailStr
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    # Define placeholder types when email service is not available
    FastMail = None
    MessageSchema = None
    ConnectionConfig = None
    MessageType = None
    EmailStr = str  # Fallback to regular string
    EMAIL_SERVICE_AVAILABLE = False
    print("⚠️  FastAPI-Mail module not available. Email notifications will be disabled.")

# Configure logging
logger = logging.getLogger(__name__)

# --- Email Configuration ---
if EMAIL_SERVICE_AVAILABLE:
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    # Instantiate the mail-sending client
    fm = FastMail(conf)
else:
    conf = None
    fm = None

# --- Generic Email Sending Function ---

async def send_email(fm_instance: FastMail, to: List[EmailStr], subject: str, html_content: str):
    """
    Sends an email to one or more recipients using a provided FastMail instance.

    Args:
        fm_instance: The configured FastMail instance.
        to: A list of recipient email addresses.
        subject: The subject of the email.
        html_content: The HTML body of the email.
    """
    if not fm_instance or not fm_instance.config.MAIL_USERNAME:
        logger.error("FastMail instance is not configured. Cannot send email.")
        return

    message = MessageSchema(
        subject=subject,
        recipients=to,
        body=html_content,
        subtype="html"
    )
    
    try:
        logger.info(f"Attempting to send email to: {to} with subject: '{subject}'")
        await fm_instance.send_message(message)
        logger.info(f"Email sent successfully to: {to}")
    except Exception as e:
        logger.error(f"FAILED to send email to {to}. Error: {e}", exc_info=True)
        # In a production scenario, you might want to add more robust error handling
        # or a retry mechanism here.

# --- Specific Email Template Functions ---

async def send_payment_failed_email(recipient: EmailStr):
    """
    Sends a pre-defined email for payment failures.
    """
    if not EMAIL_SERVICE_AVAILABLE:
        logger.warning(f"Email service unavailable. Would have sent payment failed email to {recipient}")
        return
    
    subject = "Action Required: Your Subscription Payment Failed"
    body = """
    <html>
        <body>
            <h2>Payment Issue for Your Account</h2>
            <p>Hello,</p>
            <p>We're writing to let you know that we were unable to process the recent payment for your subscription.</p>
            <p>To avoid any interruption in your premium service, please update your payment information in your account settings as soon as possible.</p>
            <p>If you have any questions, please contact our support team.</p>
            <p>Thank you,<br>The Team</p>
        </body>
    </html>
    """
    await send_email(fm, [recipient], subject, body)


async def send_subscription_canceled_email(recipient: EmailStr):
    """
    Sends a pre-defined email confirming subscription cancellation.
    """
    if not EMAIL_SERVICE_AVAILABLE:
        logger.warning(f"Email service unavailable. Would have sent subscription canceled email to {recipient}")
        return
    
    subject = "Your Subscription Has Been Canceled"
    body = """
    <html>
        <body>
            <h2>Subscription Canceled</h2>
            <p>Hello,</p>
            <p>This email confirms that your premium subscription has been successfully canceled. You will no longer be billed.</p>
            <p>You will retain access to premium features until the end of your current billing period.</p>
            <p>We're sorry to see you go! If you change your mind, you can re-subscribe at any time from your account page.</p>
            <p>Thank you,<br>The Team</p>
        </body>
    </html>
    """
    await send_email(fm, [recipient], subject, body) 