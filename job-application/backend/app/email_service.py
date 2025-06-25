import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List
import logging

# Configure logging
logger = logging.getLogger(__name__)

# --- Email Configuration ---
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

fm = FastMail(conf)

# --- Generic Email Sending Function ---

async def send_email(recipients: List[EmailStr], subject: str, body: str):
    """
    Sends an email to a list of recipients.
    """
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html
    )
    try:
        await fm.send_message(message)
        logger.info(f"Email sent to {recipients} with subject: '{subject}'")
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}. Error: {e}")

# --- Specific Email Template Functions ---

async def send_payment_failed_email(recipient: EmailStr):
    """
    Sends a pre-defined email for payment failures.
    """
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
    await send_email([recipient], subject, body)


async def send_subscription_canceled_email(recipient: EmailStr):
    """
    Sends a pre-defined email confirming subscription cancellation.
    """
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
    await send_email([recipient], subject, body) 