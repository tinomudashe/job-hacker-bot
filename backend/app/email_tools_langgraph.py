"""
Email Tools for LangGraph Orchestrator
Integrates email generation with the existing orchestrator system
"""

import logging
from typing import List, Dict, Any, Optional, Annotated
from datetime import datetime, timedelta
import json
import re

from langchain_core.tools import StructuredTool
from langgraph.prebuilt.tool_node import InjectedState
from pydantic import BaseModel, Field

from app.email_tools import EmailGenerator, EmailContext, EmailTracker
from app.state_types import WebSocketState
from app.models_db import User

log = logging.getLogger(__name__)


class EmailRequestInput(BaseModel):
    """Input schema for email generation"""
    request_type: str = Field(
        default="application",
        description="Type of email: 'application', 'follow_up', 'thank_you', 'networking', 'improve', 'reschedule', 'postpone', 'custom'"
    )
    company_name: Optional[str] = Field(default=None, description="Company name")
    job_title: Optional[str] = Field(default=None, description="Job position title")
    recipient_name: Optional[str] = Field(default=None, description="Recipient's name")
    recipient_email: Optional[str] = Field(default=None, description="Recipient's email address")
    job_url: Optional[str] = Field(default=None, description="Job posting URL")
    tone: str = Field(default="professional", description="Email tone")
    additional_context: Optional[str] = Field(default=None, description="Additional context or requirements")
    email_draft: Optional[str] = Field(default=None, description="Email draft to improve (for 'improve' type)")


class ExtractEmailInput(BaseModel):
    """Input schema for URL extraction and email generation"""
    url: str = Field(..., description="The job posting URL")


class EmailToolsLangGraph:
    """
    Email Tools with LangGraph state injection
    Handles all email-related operations in the orchestrator
    """
    
    def __init__(self, user: User, db_session=None):
        self.user = user
        self.db = db_session
        self.email_generator = EmailGenerator()
        self.email_tracker = EmailTracker()
        self.user_id = user.id
        self.user_name = user.name or user.email.split('@')[0]
    
    async def generate_professional_email(
        self,
        request_type: str = "application",
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        recipient_name: Optional[str] = None,
        recipient_email: Optional[str] = None,
        job_url: Optional[str] = None,
        tone: str = "professional",
        additional_context: Optional[str] = None,
        email_draft: Optional[str] = None,
        state: Annotated[WebSocketState, InjectedState] = None
    ) -> str:
        """
        Generate a professional email based on the request type
        Integrates with LangGraph state for tracking
        """
        try:
            log.info(f"📧 Generating {request_type} email for user {self.user_name}")
            
            # Update state if available
            if state:
                await self._update_state(state, f"Generating {request_type} email...")
            
            # Handle different email types
            if request_type == "improve" and email_draft:
                result = await self._improve_email(email_draft)
            elif request_type == "follow_up":
                result = await self._generate_follow_up(company_name, job_title, recipient_name)
            elif request_type in ["reschedule", "postpone"]:
                result = await self._generate_reschedule_email(
                    company_name, job_title, recipient_name, recipient_email, additional_context
                )
            elif request_type == "custom":
                result = await self._generate_custom_email(
                    company_name, job_title, recipient_name, recipient_email, 
                    tone, additional_context
                )
            else:
                result = await self._generate_new_email(
                    request_type, company_name, job_title, 
                    recipient_name, recipient_email, job_url, tone, additional_context
                )
            
            # Track in state
            if state:
                state["tool_outputs"].append({
                    "tool": "email_generator",
                    "output": f"Email generated successfully",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return result
            
        except Exception as e:
            log.error(f"Error generating email: {e}")
            if state:
                state["errors"].append(str(e))
            return f"❌ Error generating email: {str(e)}"
    
    async def _generate_new_email(
        self, request_type: str, company_name: str, job_title: str,
        recipient_name: str, recipient_email: str, job_url: str, tone: str, additional_context: str
    ) -> str:
        """Generate a new email"""
        
        # Map request type to purpose
        purpose_map = {
            "application": "job_application",
            "thank_you": "thank_you",
            "networking": "networking",
            "introduction": "introduction"
        }
        
        context = EmailContext(
            user_name=self.user_name,
            company_name=company_name or "your company",
            job_title=job_title or "the position",
            recipient_name=recipient_name or "Hiring Manager",
            job_url=job_url,
            purpose=purpose_map.get(request_type, "job_application"),
            tone=tone or "professional",
            additional_context=additional_context,
            user_background=await self._get_user_background()
        )
        
        # Determine template type
        template_type = "custom"
        if request_type == "application":
            template_type = "initial_application"
        elif request_type == "thank_you":
            template_type = "thank_you_after_interview"
        elif request_type == "networking":
            template_type = "networking"
        
        email = await self.email_generator.generate_email(context, template_type)
        
        # Track the email
        self.email_tracker.track_email(email, context)
        
        return self._format_email_response(email, request_type, recipient_email)
    
    async def _generate_follow_up(
        self, company_name: str, job_title: str, recipient_name: str
    ) -> str:
        """Generate a follow-up email"""
        
        context = EmailContext(
            user_name=self.user_name,
            company_name=company_name or "the company",
            job_title=job_title or "the position",
            recipient_name=recipient_name or "Hiring Manager",
            purpose="follow_up",
            tone="professional"
        )
        
        # Calculate days since (default to 5 for follow-up)
        days_since = 5
        
        email = await self.email_generator.generate_follow_up(
            original_context=context,
            days_since=days_since
        )
        
        return self._format_follow_up_response(email, days_since)
    
    async def _improve_email(self, email_draft: str) -> str:
        """Improve an existing email draft"""
        
        improvements = await self.email_generator.suggest_improvements(email_draft)
        
        return self._format_improvement_response(improvements)
    
    async def _generate_reschedule_email(
        self, 
        company_name: str, 
        job_title: str, 
        recipient_name: str,
        recipient_email: str,
        additional_context: str = None
    ) -> str:
        """Generate an email to reschedule/postpone an interview"""
        
        from app.email_tools import EmailTemplate
        
        # Create context for reschedule request
        context = EmailContext(
            user_name=self.user_name,
            company_name=company_name or "your company",
            job_title=job_title or "the position",
            recipient_name=recipient_name or "Hiring Manager",
            purpose="reschedule_interview",
            tone="professional",
            additional_context=additional_context or "I need to reschedule our upcoming interview",
            user_background=await self._get_user_background()
        )
        
        # Generate the reschedule email body
        email_body = f"""Dear {recipient_name or 'Hiring Manager'},

I hope this email finds you well. I am writing regarding our scheduled interview for the {job_title or 'the'} position at {company_name or 'your company'}.

I am very excited about this opportunity and remain highly interested in the position. However, due to {additional_context or 'an unexpected circumstance'}, I would need to reschedule our interview.

I sincerely apologize for any inconvenience this may cause. I am available at your earliest convenience and can be flexible with my schedule to accommodate yours.

Would it be possible to reschedule? I am available:
• Any time next week
• This week after Wednesday
• At your earliest convenience

Thank you very much for your understanding and flexibility. I look forward to speaking with you soon about this exciting opportunity.

Best regards,
{self.user_name}"""
        
        # Create EmailTemplate object
        email = EmailTemplate(
            subject=f"Request to Reschedule Interview - {job_title or 'Position'}",
            body=email_body,
            signature=None
        )
        
        return self._format_email_response(
            email, 
            "reschedule", 
            recipient_email
        )
    
    async def _generate_custom_email(
        self,
        company_name: str = None,
        job_title: str = None,
        recipient_name: str = None,
        recipient_email: str = None,
        tone: str = "professional",
        additional_context: str = None
    ) -> str:
        """Generate a custom email using AI based on user's specific requirements"""
        
        # If no context provided, create a generic professional email request
        if not additional_context:
            additional_context = "Write a professional email"
        
        # Use the EmailGenerator's AI capabilities for custom email
        context = EmailContext(
            user_name=self.user_name,
            company_name=company_name,
            job_title=job_title,
            recipient_name=recipient_name or "Recipient",
            purpose="custom",
            tone=tone,
            additional_context=additional_context,
            user_background=await self._get_user_background()
        )
        
        # Generate custom email using the AI
        email = await self.email_generator.generate_custom_email(context)
        
        # Format the response
        return self._format_email_response(email, "custom", recipient_email)
    
    async def extract_and_generate_from_url(
        self,
        url: str,
        state: Annotated[WebSocketState, InjectedState] = None
    ) -> str:
        """Extract job info from URL and generate email"""
        try:
            log.info(f"🔍 Extracting job info from URL: {url}")
            
            # Extract job information
            job_info = await self.email_generator.extract_job_info_from_url(url)
            
            # Generate email with extracted info
            context = EmailContext(
                user_name=self.user_name,
                company_name=job_info.get('company_name', 'Company'),
                job_title=job_info.get('job_title', 'Position'),
                job_url=url,
                purpose="job_application",
                tone="professional",
                additional_context=job_info.get('description', '')[:500]
            )
            
            email = await self.email_generator.generate_email(context, "initial_application")
            
            # Track the email
            self.email_tracker.track_email(email, context)
            
            response = f"""📧 **Email Generated from Job Posting**

**Job Details Extracted:**
• Company: {job_info.get('company_name', 'Not found')}
• Position: {job_info.get('job_title', 'Not found')}
• URL: {url}

**Generated Email:**

**Subject:** {email.subject}

{email.body}

{email.signature if email.signature else ''}

---
✅ Email saved and ready to send!
💡 **Tip:** Follow up in 3-5 days if you don't hear back."""
            
            return response
            
        except Exception as e:
            log.error(f"Error processing URL: {e}")
            return f"❌ Error extracting job info from URL: {str(e)}"
    
    def _format_email_response(self, email, request_type: str, recipient_email: Optional[str] = None) -> str:
        """Format email response for display"""
        
        emoji_map = {
            "application": "📨",
            "thank_you": "🙏",
            "networking": "🤝",
            "introduction": "👋"
        }
        
        emoji = emoji_map.get(request_type, "📧")
        
        return f"""{emoji} **Email Generated Successfully!**

**Subject:** {email.subject}

**To:** {recipient_email if recipient_email else '[recipient email address]'}

**Email Body:**
{email.body}

{email.signature if email.signature else ''}

---
✅ Email has been saved to your tracker
💡 **Tips for sending:**
• Personalize any [brackets] placeholders
• Double-check the recipient's name and company
• Send during business hours (Tue-Thu, 9-11 AM is best)
• Follow up in 3-5 days if no response

📊 **Success Rate Tips:**
• Emails sent Tuesday-Thursday have 8% higher open rates
• Subject lines under 50 characters perform better
• Including specific company details increases response by 26%"""
    
    def _format_follow_up_response(self, email, days_since: int) -> str:
        """Format follow-up email response"""
        
        return f"""🔄 **Follow-up Email Generated!**

**Subject:** {email.subject}

**Email Body:**
{email.body}

---
📅 **Follow-up Timeline:**
• This is day {days_since} since your application
• Next follow-up recommended: {email.follow_up_schedule.get('next_follow_up', 'In 7 days') if email.follow_up_schedule else 'In 7 days'}

💡 **Follow-up Best Practices:**
• Keep it brief (2-3 paragraphs max)
• Reference your original application
• Add new value or information
• Show continued enthusiasm
• Maximum 3-4 follow-ups total"""
    
    def _format_improvement_response(self, improvements: Dict[str, Any]) -> str:
        """Format email improvement response"""
        
        feedback = improvements.get('feedback', {})
        suggestions = improvements.get('suggestions', [])
        
        response = f"""✏️ **Email Improvement Suggestions**

**Improved Version:**
{improvements.get('improved_version', 'No improvements suggested')}

**Detailed Feedback:**"""
        
        for category, comment in feedback.items():
            if comment:
                response += f"\n• **{category.title()}:** {comment}"
        
        if suggestions:
            response += "\n\n**Action Items:**"
            for suggestion in suggestions:
                response += f"\n✓ {suggestion}"
        
        response += """

---
💡 **Email Writing Tips:**
• Keep subject lines under 50 characters
• Use active voice and strong action verbs
• Quantify achievements when possible
• End with a clear call to action"""
        
        return response
    
    async def _get_user_background(self) -> str:
        """Get user's background from resume/profile"""
        try:
            # Try to get user's resume data
            if self.db:
                from app.models_db import Resume
                from sqlalchemy import select
                
                result = await self.db.execute(
                    select(Resume).where(Resume.user_id == self.user_id).limit(1)
                )
                resume = result.scalar_one_or_none()
                
                if resume and resume.data:
                    # Extract summary or create brief background
                    resume_data = resume.data
                    if isinstance(resume_data, dict):
                        summary = resume_data.get('professionalSummary', '')
                        if not summary:
                            # Build from experience
                            experiences = resume_data.get('experiences', [])
                            if experiences and len(experiences) > 0:
                                latest = experiences[0]
                                summary = f"{latest.get('title', 'Professional')} with experience at {latest.get('company', 'various companies')}"
                        return summary[:500]  # Limit length
            
            return "Experienced professional seeking new opportunities"
            
        except Exception as e:
            log.warning(f"Could not get user background: {e}")
            return "Professional with relevant experience"
    
    async def _update_state(self, state: WebSocketState, message: str):
        """Update LangGraph state with progress"""
        if state and "messages" in state:
            state["messages"].append({
                "role": "system",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def get_tools(self) -> List[StructuredTool]:
        """Return email tools for the orchestrator"""
        
        tools = [
            StructuredTool(
                name="generate_professional_email",
                description="""Generate professional emails for job applications, follow-ups, networking, etc.
                Use this when user asks to 'write an email', 'send email to recruiter', 'email for job', 'prepare email', 'contact', 'reach out'.
                This tool MUST be called when user mentions 'email' in any context related to job applications.
                Examples that trigger this tool:
                - 'I want to send an email'
                - 'prepare email for React Developer position'
                - 'write to recruiter'
                - 'contact hiring manager'
                - 'email about job'
                """,
                func=self.generate_professional_email,
                args_schema=EmailRequestInput,
                return_direct=False
            ),
            StructuredTool(
                name="extract_and_email_from_url",
                description="Extract job information from a URL and generate a tailored email",
                func=self.extract_and_generate_from_url,
                args_schema=ExtractEmailInput
            )
        ]
        
        log.info(f"📧 Created {len(tools)} email tools for orchestrator")
        return tools


# Backwards compatibility
EmailTools = EmailToolsLangGraph