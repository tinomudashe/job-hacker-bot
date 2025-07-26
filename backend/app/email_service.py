import os
import logging
from typing import List, Dict, Any
from datetime import datetime

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
    print("WARNING: FastAPI-Mail module not available. Email notifications will be disabled.")

# Configure logging
logger = logging.getLogger(__name__)

# --- Email Configuration ---
if EMAIL_SERVICE_AVAILABLE:
    # For production, ensure your .env file or environment variables are set:
    # MAIL_USERNAME="bot@jobhackerbot.com"
    # MAIL_FROM="bot@jobhackerbot.com"
    # ... and other SMTP credentials
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
    
# --- Reusable Master Email Template ---

def get_master_email_template(context: Dict[str, Any]) -> str:
    """
    Generates a professional, responsive HTML email body with perfect spacing and styling.
    """
    # Use the official production URL. For best practice, this is set via an environment variable.
    production_url = os.getenv("APP_URL", "https://jobhackerbot.com")
    if not production_url:
        logger.error("CRITICAL: APP_URL environment variable is not set. Email links will be broken.")
        production_url = "https://jobhackerbot.com" # Hardcoded fallback

    # --- FIX: Add the logo URL ---
    logo_url = f"{production_url}/jobhackerbot-logo.png"

    current_year = datetime.now().year
    name = context.get("name", "User")
    title = context.get("title", "A message from Job Hacker Bot")
    preheader = context.get("preheader", "Your career co-pilot has an update for you.")
    main_content = context.get("main_content", "<p>This is a default message.</p>")
    cta_text = context.get("cta_text")
    cta_link_path = context.get("cta_link") 

    cta_button_html = ""
    if cta_text and cta_link_path:
        # This correctly uses the APP_URL environment variable via production_url
        full_cta_link = f"{production_url}{cta_link_path}"
        cta_button_html = f"""
        <tr>
            <td align="center" style="padding: 20px 0 30px 0;">
                <table border="0" cellspacing="0" cellpadding="0">
                    <tr>
                        <td align="center" style="border-radius: 8px;" bgcolor="#0069ff">
                            <a href="{full_cta_link}" target="_blank" style="font-size: 16px; font-family: Helvetica, Arial, sans-serif; color: #ffffff; text-decoration: none; border-radius: 8px; padding: 16px 30px; border: 1px solid #0069ff; display: inline-block; font-weight: bold;">{cta_text}</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ margin: 0; padding: 0; width: 100% !important; background-color: #f6f6f6; -webkit-text-size-adjust: none; }}
            a {{ color: #0069ff; text-decoration: none; }}
            table {{ border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
            .main-container {{ width: 100%; max-width: 600px; margin: 0 auto; }}
        </style>
    </head>
    <body style="font-family: Helvetica, Arial, sans-serif; color: #4d5055;">
        <div style="display:none;font-size:1px;color:#ffffff;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">{preheader}</div>
        <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#f6f6f6">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table class="main-container" border="0" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="padding: 30px; background-color: #ffffff; border-radius: 12px; border: 1px solid #ececee;">
                                <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                    <!-- Header -->
                                    <tr>
                                        <td style="padding-bottom: 25px;">
                                            <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td width="52" valign="middle">{logo_url}</td>
                                                    <td style="padding-left: 15px;" valign="middle">
                                                        <h1 style="margin: 0; font-size: 22px; color: #1a1a1a; font-weight: bold;">Job Hacker Bot</h1>
                                                        <p style="margin: 0; font-size: 15px; color: #666666;">Your career co-pilot</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <!-- Content -->
                                    <tr>
                                        <td class="wrapper" style="font-family: sans-serif; font-size: 14px; vertical-align: top; box-sizing: border-box; padding: 20px;" valign="top">
                                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;" width="100%">
                                                <tr>
                                                    <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;" valign="top">
                                                        <!-- START LOGO (REPLACES TITLE) -->
                                                        <div style="text-align: center; margin-bottom: 20px;">
                                                            <a href="{production_url}" target="_blank">
                                                                <img src="{logo_url}" alt="Job Hacker Bot Logo" height="40" style="border: none; -ms-interpolation-mode: bicubic; max-width: 100%; height: 40px;">
                                                            </a>
                                                        </div>
                                                        <!-- END LOGO -->

                                                        <p style="font-family: sans-serif; font-size: 16px; font-weight: normal; margin: 0; margin-bottom: 15px; font-weight: bold;">Hi {name},</p>
                                                        
                                                        <h1 style="font-family: sans-serif; font-size: 24px; font-weight: bold; margin: 0; margin-bottom: 15px;">{title}</h1>
                                                        
                                                        <!-- This is where the main content of the email goes -->
                                                        {main_content}
                                                        
                                                        <table width="100%" border="0" cellspacing="0" cellpadding="0">{cta_button_html}</table>
                                                        <p style="font-size: 16px; line-height: 1.6; color: #4d5055; margin: 0;">Thank you,<br>The Job Hacker Bot Team</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <!-- Footer -->
                                    <tr>
                                        <td style="padding: 30px 20px; text-align: center; font-size: 12px; color: #a8a8a8;">
                                            <p style="margin: 0 0 5px 0;">&copy; {current_year} Job Hacker Bot. All rights reserved.</p>
                                            <p style="margin: 0;">
                                                <a href="mailto:bot@jobhackerbot.com" target="_blank" style="color: #666a73; text-decoration: underline;">Contact Support</a> &bull; 
                                                <a href="{production_url}/settings" target="_blank" style="color: #666a73; text-decoration: underline;">Preferences</a> &bull; 
                                                <a href="#" target="_blank" style="color: #666a73; text-decoration: underline;">Unsubscribe</a>
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

# --- Generic Email Sending Function (Unchanged) ---
async def send_email(fm_instance: FastMail, to: List[EmailStr], subject: str, html_content: str):
    if not fm_instance or not fm_instance.config.MAIL_USERNAME:
        logger.error("FastMail instance is not configured. Cannot send email.")
        return
    message = MessageSchema(subject=subject, recipients=to, body=html_content, subtype="html")
    try:
        logger.info(f"Attempting to send email to: {to} with subject: '{subject}'")
        await fm_instance.send_message(message)
        logger.info(f"Email sent successfully to: {to}")
    except Exception as e:
        logger.error(f"FAILED to send email to {to}. Error: {e}", exc_info=True)

# --- REFACTORED: Specific Email Template Functions ---

async def send_payment_failed_email(recipient: EmailStr):
    if not EMAIL_SERVICE_AVAILABLE: return
    context = {
        "title": "Action Required: Payment Issue",
        "preheader": "Please update your payment information to keep your Pro account active.",
        "main_content": """
            <p>We're writing to let you know that we were unable to process the recent payment for your subscription.</p>
            <p>To avoid any interruption in your premium service, please update your payment information in your account settings as soon as possible.</p>
        """,
        "cta_text": "Update Payment Method",
        "cta_link": "/settings"
    }
    subject = "Action Required: Your Subscription Payment Failed"
    html_body = get_master_email_template(context)
    await send_email(fm, [recipient], subject, html_body)


async def send_subscription_canceled_email(recipient: EmailStr):
    if not EMAIL_SERVICE_AVAILABLE: return
    context = {
        "title": "Subscription Canceled",
        "preheader": "Your subscription has been canceled, and you will no longer be billed.",
        "main_content": """
            <p>This email confirms that your premium subscription has been successfully canceled. You will no longer be billed.</p>
            <p>You will retain access to premium features until the end of your current billing period.</p>
            <p>We're sorry to see you go! If you change your mind, you can re-subscribe at any time from your account page.</p>
        """,
    }
    subject = "Your Subscription Has Been Canceled"
    html_body = get_master_email_template(context)
    await send_email(fm, [recipient], subject, html_body)


async def send_welcome_email(recipient: EmailStr, name: str = "User"):
    if not EMAIL_SERVICE_AVAILABLE: return
    context = {
        "name": name,
        "title": "Welcome to Pro!",
        "preheader": "You've unlocked all premium features. Let's get started.",
        "main_content": """
            <p>Your account is now active, and you have full access to all premium features, including unlimited resume generation, advanced AI interview coaching, and priority support.</p>
            <p>Happy job hunting!</p>
        """,
        "cta_text": "Go to My Account",
        "cta_link": "/"
    }
    subject = "Welcome to Job Hacker Bot Pro"
    html_body = get_master_email_template(context)
    await send_email(fm, [recipient], subject, html_body) 