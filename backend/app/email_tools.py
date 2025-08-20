"""
Email generation and follow-up tools for job applications
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
import os


class EmailContext(BaseModel):
    """Context for email generation"""
    recipient_name: Optional[str] = Field(None, description="Name of the recipient")
    recipient_title: Optional[str] = Field(None, description="Title/position of recipient")
    company_name: Optional[str] = Field(None, description="Company name")
    job_title: Optional[str] = Field(None, description="Job position title")
    job_url: Optional[str] = Field(None, description="Job posting URL")
    previous_interaction: Optional[str] = Field(None, description="Previous email or interaction")
    user_name: str = Field(..., description="Name of the sender")
    user_background: Optional[str] = Field(None, description="User's background/resume summary")
    purpose: str = Field(..., description="Purpose of the email")
    tone: str = Field(default="professional", description="Tone of the email")
    additional_context: Optional[str] = Field(None, description="Any additional context")


class EmailTemplate(BaseModel):
    """Email template structure"""
    subject: str
    body: str
    signature: Optional[str] = None
    attachments: List[str] = []
    follow_up_schedule: Optional[Dict[str, Any]] = None


class EmailGenerator:
    """Main email generation class"""
    
    def __init__(self, llm=None):
        # Use Claude instead of OpenAI
        self.llm = llm or ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0.7,
            max_tokens=1000,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        self.email_templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load email templates"""
        return {
            "initial_application": """
Subject: {job_title} Position - {user_name}

Dear {recipient_name},

I am writing to express my strong interest in the {job_title} position at {company_name}. 
{opening_hook}

{body_paragraph_1}

{body_paragraph_2}

{closing_paragraph}

Best regards,
{user_name}
{signature}
""",
            "follow_up_after_application": """
Subject: Following Up - {job_title} Application - {user_name}

Dear {recipient_name},

I hope this email finds you well. I wanted to follow up on my application for the {job_title} 
position submitted on {application_date}.

{follow_up_body}

Thank you for considering my application. I look forward to the opportunity to discuss how 
I can contribute to {company_name}.

Best regards,
{user_name}
""",
            "thank_you_after_interview": """
Subject: Thank You - {job_title} Interview - {user_name}

Dear {recipient_name},

Thank you for taking the time to meet with me {interview_date} to discuss the {job_title} 
position at {company_name}.

{thank_you_body}

{reiteration_of_interest}

Best regards,
{user_name}
""",
            "networking": """
Subject: {networking_subject}

Dear {recipient_name},

{networking_opening}

{networking_body}

{networking_closing}

Best regards,
{user_name}
""",
            "informational_interview": """
Subject: Request for Informational Interview - {field_of_interest}

Dear {recipient_name},

{informational_opening}

{informational_body}

{informational_closing}

Best regards,
{user_name}
"""
        }
    
    async def extract_job_info_from_url(self, url: str) -> Dict[str, Any]:
        """Extract job information from a URL"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            title = soup.find('title').text if soup.find('title') else ''
            
            # Try to find job-specific information
            job_info = {
                'url': url,
                'title': title,
                'company_name': self._extract_company_name(soup, url),
                'job_title': self._extract_job_title(soup),
                'description': self._extract_description(soup),
                'requirements': self._extract_requirements(soup),
            }
            
            return job_info
            
        except Exception as e:
            print(f"Error extracting job info: {e}")
            return {'url': url, 'error': str(e)}
    
    def _extract_company_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract company name from page"""
        # Common patterns for company names
        patterns = [
            {'class': re.compile('company', re.I)},
            {'id': re.compile('company', re.I)},
            {'itemprop': 'hiringOrganization'},
        ]
        
        for pattern in patterns:
            element = soup.find(attrs=pattern)
            if element:
                return element.get_text(strip=True)
        
        # Fallback to domain name
        domain = urlparse(url).netloc
        return domain.replace('www.', '').split('.')[0].title()
    
    def _extract_job_title(self, soup: BeautifulSoup) -> str:
        """Extract job title from page"""
        patterns = [
            {'class': re.compile('job.*title', re.I)},
            {'id': re.compile('job.*title', re.I)},
            {'itemprop': 'title'},
            'h1',
        ]
        
        for pattern in patterns:
            if isinstance(pattern, str):
                element = soup.find(pattern)
            else:
                element = soup.find(attrs=pattern)
            if element:
                return element.get_text(strip=True)
        
        return "Position"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description"""
        patterns = [
            {'class': re.compile('description', re.I)},
            {'id': re.compile('description', re.I)},
            {'itemprop': 'description'},
        ]
        
        for pattern in patterns:
            element = soup.find(attrs=pattern)
            if element:
                return element.get_text(strip=True)[:500]  # Limit length
        
        return ""
    
    def _extract_requirements(self, soup: BeautifulSoup) -> List[str]:
        """Extract job requirements"""
        requirements = []
        
        patterns = [
            {'class': re.compile('requirement', re.I)},
            {'id': re.compile('requirement', re.I)},
            {'class': re.compile('qualification', re.I)},
        ]
        
        for pattern in patterns:
            elements = soup.find_all(attrs=pattern)
            for element in elements:
                requirements.append(element.get_text(strip=True))
        
        return requirements[:5]  # Limit to top 5
    
    async def generate_email(self, context: EmailContext, template_type: str = "custom") -> EmailTemplate:
        """Generate an email based on context"""
        
        if template_type in self.email_templates:
            # Use predefined template
            template = self.email_templates[template_type]
            # Simple template filling without _fill_template method
            filled_template = template.format(
                job_title=context.job_title or "Position",
                user_name=context.user_name,
                recipient_name=context.recipient_name or "Hiring Manager",
                company_name=context.company_name or "your company",
                opening_hook="I am excited about this opportunity",
                body_paragraph_1="My experience aligns well with your requirements",
                body_paragraph_2="I would be a valuable addition to your team",
                closing_paragraph="I look forward to discussing this opportunity",
                signature=f"Best regards,\n{context.user_name}",
                application_date="recently",
                follow_up_body="I remain very interested in this position",
                interview_date="today",
                thank_you_body="Thank you for the insightful conversation",
                reiteration_of_interest="I am even more excited about this opportunity",
                networking_subject="Professional Connection Request",
                networking_opening="I hope this email finds you well",
                networking_body="I would appreciate connecting with you",
                networking_closing="Thank you for your time",
                field_of_interest="your field",
                informational_opening="I am reaching out to learn more",
                informational_body="Your insights would be invaluable",
                informational_closing="Thank you for considering my request"
            )
            # Extract subject from template if it starts with "Subject:"
            lines = filled_template.strip().split('\n')
            if lines and lines[0].startswith('Subject:'):
                subject = lines[0].replace('Subject:', '').strip()
                body = '\n'.join(lines[1:]).strip()
            else:
                subject = f"{context.job_title or 'Position'} Application - {context.user_name}"
                body = filled_template
            
            # Remove duplicate signatures
            if body.count('Best regards,') > 1:
                # Keep only the first signature
                parts = body.split('Best regards,')
                body = parts[0] + 'Best regards,' + parts[1].split('Best regards,')[0]
            
            return EmailTemplate(
                subject=subject,
                body=body,
                signature=""
            )
        
        # Generate custom email using Claude
        prompt = f"""
        Generate a professional email for the following context:
        
        Purpose: {context.purpose}
        Recipient: {context.recipient_name or 'Hiring Manager'} ({context.recipient_title or 'Recruiter'}) at {context.company_name or 'the company'}
        Job Title: {context.job_title or 'the position'}
        Tone: {context.tone}
        Sender: {context.user_name}
        
        User Background:
        {context.user_background or 'Experienced professional'}
        
        Additional Context:
        {context.additional_context or ''}
        
        Generate a compelling email with:
        1. An attention-grabbing subject line
        2. Professional greeting
        3. Clear and concise body (2-3 paragraphs)
        4. Strong closing with call to action
        5. Professional signature
        
        Format the response as JSON with keys: subject, body, signature
        """
        
        messages = [
            SystemMessage(content="You are a professional email writer helping with job applications."),
            HumanMessage(content=prompt)
        ]
        
        result = await self.llm.ainvoke(messages)
        
        # Parse the response
        try:
            # Extract JSON from the response
            response_text = result.content
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                email_data = json.loads(json_str)
            else:
                email_data = json.loads(response_text)
            
            return EmailTemplate(
                subject=email_data.get('subject', ''),
                body=email_data.get('body', ''),
                signature=email_data.get('signature', '')
            )
        except:
            # Fallback if JSON parsing fails
            return EmailTemplate(
                subject=f"Application for {context.job_title} at {context.company_name}",
                body=result.content,
                signature=f"Best regards,\n{context.user_name}"
            )
    
    async def generate_custom_email(self, context: EmailContext) -> EmailTemplate:
        """Generate a completely custom email based on user's specific requirements"""
        
        prompt = f"""
        Create a professional email based on the following requirements:
        
        User: {context.user_name}
        Recipient: {context.recipient_name or 'Not specified'}
        Company: {context.company_name or 'Not specified'}
        Position: {context.job_title or 'Not specified'}
        Tone: {context.tone}
        
        Specific Requirements:
        {context.additional_context}
        
        User Background:
        {context.user_background or 'Professional with relevant experience'}
        
        Generate an email that:
        1. Addresses the specific requirements mentioned above
        2. Maintains a {context.tone} tone throughout
        3. Is clear, concise, and professional
        4. Includes an appropriate subject line
        5. Has proper greeting and closing
        
        Format the response as JSON with keys: subject, body, signature
        """
        
        messages = [
            SystemMessage(content="You are an expert professional email writer. Create emails that are perfectly tailored to the user's specific needs and context."),
            HumanMessage(content=prompt)
        ]
        
        result = await self.llm.ainvoke(messages)
        
        # Parse the response
        try:
            response_text = result.content
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                email_data = json.loads(json_str)
            else:
                email_data = json.loads(response_text)
            
            return EmailTemplate(
                subject=email_data.get('subject', 'Professional Email'),
                body=email_data.get('body', result.content),
                signature=email_data.get('signature', f"Best regards,\n{context.user_name}")
            )
        except:
            # Fallback if JSON parsing fails - still return a properly formatted email
            # Parse the content for subject line if present
            lines = result.content.split('\n')
            subject = "Professional Email"
            body = result.content
            
            # Try to extract subject if it's in the format "Subject: ..."
            for i, line in enumerate(lines):
                if line.startswith("Subject:"):
                    subject = line.replace("Subject:", "").strip()
                    # Rest is body
                    body = '\n'.join(lines[i+1:]).strip()
                    break
            
            return EmailTemplate(
                subject=subject,
                body=body,
                signature=f"Best regards,\n{context.user_name}"
            )
    
    async def generate_follow_up(self, 
                                 original_context: EmailContext, 
                                 days_since: int,
                                 previous_response: Optional[str] = None) -> EmailTemplate:
        """Generate a follow-up email"""
        
        prompt = f"""
        Generate a follow-up email for a job application.
        
        Original Context:
        - Applied for: {original_context.job_title} at {original_context.company_name}
        - Days since application: {days_since}
        - Previous response: {previous_response or 'No response yet'}
        
        Guidelines:
        - Be polite and professional
        - Reference the original application
        - Show continued interest
        - Add new value or information if possible
        - Keep it brief (2-3 paragraphs)
        - Include a clear call to action
        
        Generate the follow-up email with:
        1. Subject line that references the original application
        2. Brief, professional body
        3. Appropriate closing
        
        Format as JSON with keys: subject, body
        """
        
        messages = [
            SystemMessage(content="You are a professional email writer helping with job application follow-ups."),
            HumanMessage(content=prompt)
        ]
        
        result = await self.llm.ainvoke(messages)
        
        try:
            response_text = result.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                email_data = json.loads(json_str)
            else:
                email_data = json.loads(response_text)
                
            return EmailTemplate(
                subject=email_data.get('subject', ''),
                body=email_data.get('body', ''),
                follow_up_schedule={
                    "next_follow_up": (datetime.now() + timedelta(days=7)).isoformat(),
                    "follow_up_count": 1
                }
            )
        except:
            return EmailTemplate(
                subject=f"Following up - {original_context.job_title} Application",
                body=result.content
            )
    
    async def suggest_improvements(self, email_draft: str) -> Dict[str, Any]:
        """Suggest improvements for an email draft"""
        
        prompt = f"""
        Analyze this email draft and suggest improvements:
        
        {email_draft}
        
        Provide feedback on:
        1. Subject line effectiveness (if present)
        2. Opening impact
        3. Body clarity and persuasiveness
        4. Call to action strength
        5. Overall tone and professionalism
        6. Grammar and spelling
        
        Also provide:
        - An improved version of the email
        - Specific actionable suggestions
        
        Format as JSON with keys: 
        - feedback (object with categories above)
        - improved_version (string)
        - suggestions (list of strings)
        """
        
        messages = [
            SystemMessage(content="You are an expert email editor helping improve professional emails."),
            HumanMessage(content=prompt)
        ]
        
        result = await self.llm.ainvoke(messages)
        
        try:
            response_text = result.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                return json.loads(response_text)
        except:
            return {
                "feedback": {"general": "Please review the email for clarity and professionalism"},
                "improved_version": email_draft,
                "suggestions": ["Consider reviewing the email structure and tone"]
            }
    
    async def create_email_sequence(self, 
                                   context: EmailContext,
                                   sequence_type: str = "job_application") -> List[EmailTemplate]:
        """Create a sequence of follow-up emails"""
        
        sequences = {
            "job_application": [
                {"days": 0, "type": "initial_application"},
                {"days": 3, "type": "follow_up_gentle"},
                {"days": 7, "type": "follow_up_value_add"},
                {"days": 14, "type": "follow_up_final"}
            ],
            "networking": [
                {"days": 0, "type": "initial_outreach"},
                {"days": 5, "type": "follow_up_friendly"},
                {"days": 14, "type": "follow_up_value"}
            ]
        }
        
        sequence = sequences.get(sequence_type, sequences["job_application"])
        emails = []
        
        for step in sequence:
            if step["days"] == 0:
                email = await self.generate_email(context)
            else:
                email = await self.generate_follow_up(context, step["days"])
            
            email.follow_up_schedule = {
                "send_date": (datetime.now() + timedelta(days=step["days"])).isoformat(),
                "sequence_step": step["type"]
            }
            emails.append(email)
        
        return emails


class EmailTracker:
    """Track email sending and responses"""
    
    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []
        self.scheduled_emails: List[Dict[str, Any]] = []
    
    def track_email(self, email: EmailTemplate, context: EmailContext) -> str:
        """Track a sent email"""
        email_id = f"email_{datetime.now().timestamp()}"
        
        self.sent_emails.append({
            "id": email_id,
            "sent_at": datetime.now().isoformat(),
            "subject": email.subject,
            "recipient": context.recipient_name,
            "company": context.company_name,
            "job_title": context.job_title,
            "status": "sent"
        })
        
        return email_id
    
    def schedule_follow_up(self, email: EmailTemplate, context: EmailContext, send_date: datetime):
        """Schedule a follow-up email"""
        self.scheduled_emails.append({
            "scheduled_for": send_date.isoformat(),
            "email": email.dict(),
            "context": context.dict(),
            "status": "scheduled"
        })
    
    def get_pending_follow_ups(self) -> List[Dict[str, Any]]:
        """Get emails that need to be sent"""
        now = datetime.now()
        pending = []
        
        for email in self.scheduled_emails:
            scheduled_time = datetime.fromisoformat(email["scheduled_for"])
            if scheduled_time <= now and email["status"] == "scheduled":
                pending.append(email)
        
        return pending