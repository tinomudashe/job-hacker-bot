"""
Email tools integrated with the orchestrator system
"""

from typing import Dict, Any, Optional
from langchain.tools import Tool
from app.email_tools import EmailGenerator, EmailContext, EmailTracker
import json
import asyncio


class EmailOrchestratorTool:
    """Email tool for the orchestrator"""
    
    def __init__(self, llm=None):
        self.email_generator = EmailGenerator(llm=llm)
        self.email_tracker = EmailTracker()
    
    async def process_email_request(self, request: str, user_context: Dict[str, Any]) -> str:
        """Process email generation requests from the orchestrator"""
        
        request_lower = request.lower()
        
        # Determine the type of email request
        if "follow" in request_lower and "up" in request_lower:
            return await self._handle_follow_up(request, user_context)
        elif "improve" in request_lower or "edit" in request_lower:
            return await self._handle_improvement(request, user_context)
        elif "extract" in request_lower and "url" in request_lower:
            return await self._handle_url_extraction(request)
        else:
            return await self._handle_email_generation(request, user_context)
    
    async def _handle_email_generation(self, request: str, user_context: Dict[str, Any]) -> str:
        """Generate a new email"""
        
        # Extract context from request
        context = self._extract_context_from_request(request, user_context)
        
        try:
            email = await self.email_generator.generate_email(context)
            
            # Track the email
            self.email_tracker.track_email(email, context)
            
            # Format response
            response = f"""📧 **Email Generated Successfully!**

**Subject:** {email.subject}

**Body:**
{email.body}

{email.signature if email.signature else ''}

---
✅ Email has been tracked in your follow-up system.
💡 **Tips:** 
- First follow-up after 3-5 days increases reply rate by 49%
- Keep follow-ups brief and add new value
- Limit to 3-4 total follow-ups
"""
            return response
            
        except Exception as e:
            return f"❌ Error generating email: {str(e)}"
    
    async def _handle_follow_up(self, request: str, user_context: Dict[str, Any]) -> str:
        """Generate a follow-up email"""
        
        # Extract original context
        context = self._extract_context_from_request(request, user_context)
        
        # Determine days since application
        days_since = 3  # Default
        if "week" in request.lower():
            days_since = 7
        elif "two week" in request.lower():
            days_since = 14
        
        try:
            email = await self.email_generator.generate_follow_up(
                original_context=context,
                days_since=days_since
            )
            
            response = f"""📧 **Follow-up Email Generated!**

**Subject:** {email.subject}

**Body:**
{email.body}

---
📅 **Follow-up Schedule:**
- This is follow-up #{days_since // 3}
- Next recommended follow-up: {email.follow_up_schedule.get('next_follow_up', 'In 7 days') if email.follow_up_schedule else 'In 7 days'}

💡 **Best Practices:**
- Reference your original application
- Add new value or information
- Keep it brief and professional
"""
            return response
            
        except Exception as e:
            return f"❌ Error generating follow-up: {str(e)}"
    
    async def _handle_improvement(self, request: str, user_context: Dict[str, Any]) -> str:
        """Improve an existing email draft"""
        
        # Extract the email draft from the request
        # Look for the email content after keywords like "improve this:" or "edit:"
        draft_start = max(
            request.lower().find("improve this:"),
            request.lower().find("edit this:"),
            request.lower().find("email:"),
            request.lower().find("draft:")
        )
        
        if draft_start == -1:
            return "❌ Please provide the email draft you want to improve. Format: 'Improve this email: [your draft]'"
        
        email_draft = request[draft_start:].split(":", 1)[-1].strip()
        
        try:
            improvements = await self.email_generator.suggest_improvements(email_draft)
            
            response = f"""📝 **Email Improvement Suggestions**

**Improved Version:**
{improvements.get('improved_version', email_draft)}

**Feedback:**
{json.dumps(improvements.get('feedback', {}), indent=2)}

**Suggestions:**
"""
            for suggestion in improvements.get('suggestions', []):
                response += f"• {suggestion}\n"
            
            return response
            
        except Exception as e:
            return f"❌ Error improving email: {str(e)}"
    
    async def _handle_url_extraction(self, request: str) -> str:
        """Extract job information from URL"""
        
        # Extract URL from request
        import re
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, request)
        
        if not urls:
            return "❌ No URL found in your request. Please provide a valid job posting URL."
        
        url = urls[0]
        
        try:
            job_info = await self.email_generator.extract_job_info_from_url(url)
            
            response = f"""🔍 **Job Information Extracted from URL**

**Company:** {job_info.get('company_name', 'Not found')}
**Position:** {job_info.get('job_title', 'Not found')}
**URL:** {job_info.get('url', url)}

**Description:**
{job_info.get('description', 'Not available')[:500]}...

**Requirements:**
"""
            for req in job_info.get('requirements', [])[:5]:
                response += f"• {req}\n"
            
            response += "\n✅ You can now generate a tailored email for this position!"
            
            return response
            
        except Exception as e:
            return f"❌ Error extracting job information: {str(e)}"
    
    def _extract_context_from_request(self, request: str, user_context: Dict[str, Any]) -> EmailContext:
        """Extract email context from request and user context"""
        
        # Basic extraction logic - can be enhanced
        context = EmailContext(
            user_name=user_context.get('name', 'User'),
            purpose="job_application",
            tone="professional"
        )
        
        # Extract company name if mentioned
        if "at " in request:
            parts = request.split("at ")
            if len(parts) > 1:
                company = parts[1].split()[0].strip(".,!?")
                context.company_name = company
        
        # Extract job title if mentioned
        if "for " in request:
            parts = request.split("for ")
            if len(parts) > 1:
                job_title = parts[1].split(" at ")[0].strip(".,!?")
                context.job_title = job_title
        
        # Determine tone
        if "casual" in request.lower():
            context.tone = "casual"
        elif "friendly" in request.lower():
            context.tone = "friendly"
        elif "formal" in request.lower():
            context.tone = "formal"
        
        # Determine purpose
        if "network" in request.lower():
            context.purpose = "networking"
        elif "thank" in request.lower():
            context.purpose = "thank_you"
        elif "follow" in request.lower():
            context.purpose = "follow_up"
        
        return context


def create_email_tools():
    """Create email tools for the orchestrator"""
    
    email_tool = EmailOrchestratorTool()
    
    tools = [
        Tool(
            name="generate_email",
            description="Generate professional emails for job applications, follow-ups, networking, etc.",
            func=lambda x: asyncio.run(email_tool.process_email_request(x, {}))
        ),
        Tool(
            name="track_email",
            description="Track sent emails and schedule follow-ups",
            func=lambda x: json.dumps(email_tool.email_tracker.sent_emails)
        ),
        Tool(
            name="get_pending_followups",
            description="Get list of pending follow-up emails",
            func=lambda x: json.dumps(email_tool.email_tracker.get_pending_follow_ups())
        )
    ]
    
    return tools