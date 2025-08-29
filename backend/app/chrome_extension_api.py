"""
Chrome Extension API Endpoints
Handles form filling requests from the Job Hacker Bot Chrome Extension
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from app.dependencies import get_current_user, get_db
from app.models_db import User, Resume, Document
from app.extension_tokens import ExtensionToken, hash_token
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import logging
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chrome-extension", tags=["chrome-extension"])

async def get_user_from_token_or_clerk(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get user from either extension token or Clerk token.
    This allows the Chrome extension to authenticate with either method.
    """
    authorization = request.headers.get("Authorization", "")
    
    # Check if it's an extension token
    if authorization.startswith("Bearer jhb_"):
        plain_token = authorization.replace("Bearer ", "")
        token_hash_value = hash_token(plain_token)
        
        # Find the token
        result = await db.execute(
            select(ExtensionToken)
            .filter(
                ExtensionToken.token_hash == token_hash_value,
                ExtensionToken.is_active == True
            )
        )
        token = result.scalar_one_or_none()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired extension token"
            )
        
        # Check expiration
        if token.expires_at and token.expires_at < datetime.utcnow():
            token.is_active = False
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Extension token has expired"
            )
        
        # Update last used
        token.last_used = datetime.utcnow()
        await db.commit()
        
        # Get the user by external_id
        user_result = await db.execute(
            select(User).where(User.external_id == token.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    else:
        # Fall back to regular Clerk authentication
        return await get_current_user(request, authorization, db)

# Request/Response Models
class FormField(BaseModel):
    id: str
    name: str
    type: str
    category: str
    label: str
    placeholder: Optional[str] = ""
    required: bool = False
    value: Optional[str] = ""
    attributes: Dict[str, Any] = {}
    options: Optional[List[Dict[str, str]]] = None

class JobContext(BaseModel):
    title: Optional[str] = ""
    company: Optional[str] = ""
    location: Optional[str] = ""
    description: Optional[str] = ""

class FormStructure(BaseModel):
    fields: List[FormField]
    metadata: Dict[str, Any]
    jobContext: Optional[JobContext] = None

class AutofillRequest(BaseModel):
    formStructure: FormStructure
    includeConfidence: bool = True

class AutofillResponse(BaseModel):
    fieldValues: Dict[str, str]
    confidence: Dict[str, float]
    missingInfo: Dict[str, str]

class ExtensionSettings(BaseModel):
    enabled: bool = True
    autoDetect: bool = True
    typingSpeed: int = 100

class SaveInputRequest(BaseModel):
    field: Dict[str, str]
    value: str
    context: Dict[str, Any]

class ExtensionStatus(BaseModel):
    extensionEnabled: bool
    hasResume: bool
    resumeUpdated: Optional[datetime]
    profileComplete: bool

# Helper class for form filling
class FormFillerService:
    def __init__(self, user: User, db: AsyncSession, job_context: Optional[JobContext] = None):
        self.user = user
        self.db = db
        self.resume_data = None
        self.job_context = job_context
        self.llm = None  # Initialize lazily when needed
        
    async def load_resume(self):
        """Load user's latest resume"""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == self.user.id)
            .order_by(desc(Resume.updated_at))
            .limit(1)
        )
        resume = result.scalar_one_or_none()
        
        if resume:
            if isinstance(resume.data, str):
                self.resume_data = json.loads(resume.data)
            else:
                self.resume_data = resume.data
            return True
        return False
    
    async def get_field_value(self, field: FormField) -> tuple[str, float]:
        """
        Get value for a field from resume data or saved responses
        Returns: (value, confidence)
        """
        # First, check for saved responses
        saved_value = await self._get_saved_response(field.category)
        if saved_value:
            return saved_value, 1.0  # High confidence for saved responses
        
        # Try to get from resume data
        value, confidence = self._get_from_resume(field)
        
        # If we couldn't find it in resume, try LLM for certain field types
        if value == "[MISSING]" and self._should_use_llm(field):
            value, confidence = await self._get_llm_suggestion(field)
        
        return value, confidence
    
    def _get_from_resume(self, field: FormField) -> tuple[str, float]:
        """Get field value from resume data"""
        if not self.resume_data:
            return "[MISSING]", 0.0
        
        category_parts = field.category.split('.')
        main_category = category_parts[0] if category_parts else ''
        sub_category = category_parts[1] if len(category_parts) > 1 else ''
        
        # Personal Information
        if main_category == 'personal':
            return self._get_personal_field(sub_category)
        
        # Professional Information
        elif main_category == 'professional':
            return self._get_professional_field(sub_category)
        
        # Education
        elif main_category == 'education':
            return self._get_education_field(sub_category)
        
        # Skills
        elif main_category == 'skills':
            return self._get_skills_field(sub_category)
        
        # Custom questions - will try LLM
        elif main_category == 'questions':
            return "[MISSING]", 0.0
        
        # Legal/compliance
        elif main_category == 'legal':
            return self._get_legal_field(sub_category)
        
        return "[MISSING]", 0.0
    
    def _should_use_llm(self, field: FormField) -> bool:
        """Determine if we should use LLM for this field"""
        # Use LLM for almost everything to ensure intelligent responses
        # The LLM is smart enough to understand what's being asked
        
        # Only skip LLM for these exact direct mappings that we have
        direct_mappings = ['email', 'phone']
        field_lower = (field.name or '').lower()
        label_lower = (field.label or '').lower()
        
        # If it's a direct mapping field AND we have the value, don't use LLM
        for mapping in direct_mappings:
            if mapping in field_lower or mapping in label_lower:
                # Check if we actually have this value
                personal_info = self.resume_data.get('personalInfo', {}) if self.resume_data else {}
                if personal_info.get(mapping):
                    return False
        
        # For EVERYTHING else, use the LLM - it's smart enough to figure out what's needed
        # This includes linkedin, website, and all other fields that might need intelligent parsing
        return True
    
    async def _get_saved_response(self, category: str) -> Optional[str]:
        """Get the default saved response for a category"""
        from app.models_db import SavedApplicationResponse
        
        result = await self.db.execute(
            select(SavedApplicationResponse)
            .where(
                SavedApplicationResponse.user_id == self.user.id,
                SavedApplicationResponse.field_category == category,
                SavedApplicationResponse.is_default == True
            )
        )
        response = result.scalar_one_or_none()
        
        if response:
            # Update usage count and last used
            response.usage_count += 1
            response.last_used = datetime.now()
            await self.db.commit()
            return response.field_value
        
        return None
    
    def _get_personal_field(self, field_type: str) -> tuple[str, float]:
        """Get personal information fields - basic fields only, complex ones use LLM"""
        personal_info = self.resume_data.get('personalInfo', {})
        
        # For complex fields that need reasoning, return MISSING to trigger LLM
        # This includes address parsing, name splitting, etc.
        
        # Direct mappings only - no parsing
        if field_type == 'email':
            return personal_info.get('email', '[MISSING]'), 1.0
        elif field_type == 'phone':
            return personal_info.get('phone', '[MISSING]'), 1.0
        elif field_type == 'linkedin':
            return personal_info.get('linkedin', '[MISSING]'), 0.9
        elif field_type == 'website':
            return personal_info.get('website', '[MISSING]'), 0.9
        
        # For everything else that needs intelligent parsing, return MISSING
        # This will trigger the LLM to handle it intelligently
        return "[MISSING]", 0.0
    
    def _get_professional_field(self, field_type: str) -> tuple[str, float]:
        """Get professional information fields"""
        experience = self.resume_data.get('experience', [])
        
        if field_type == 'currentTitle' and experience:
            return experience[0].get('position', ''), 0.9
        elif field_type == 'currentCompany' and experience:
            return experience[0].get('company', ''), 0.9
        elif field_type == 'yearsExperience':
            # Calculate based on experience entries
            years = len(experience) * 2  # Rough estimate
            return str(years), 0.7
        elif field_type == 'salary':
            # Don't auto-fill salary expectations
            return "[MISSING]", 0.0
        
        return "[MISSING]", 0.0
    
    def _get_education_field(self, field_type: str) -> tuple[str, float]:
        """Get education fields"""
        education = self.resume_data.get('education', [])
        
        if not education:
            return "[MISSING]", 0.0
        
        latest_edu = education[0]
        
        field_map = {
            'school': (latest_edu.get('school', ''), 0.9),
            'degree': (latest_edu.get('degree', ''), 0.9),
            'major': (latest_edu.get('field', ''), 0.8),
            'gpa': (latest_edu.get('gpa', ''), 1.0),
            'graduationDate': (latest_edu.get('graduationDate', ''), 0.9)
        }
        
        return field_map.get(field_type, ("[MISSING]", 0.0))
    
    def _get_skills_field(self, field_type: str) -> tuple[str, float]:
        """Get skills fields"""
        skills = self.resume_data.get('skills', [])
        
        if field_type == 'list' and skills:
            # Format skills as comma-separated string
            if isinstance(skills[0], dict):
                skills_text = ", ".join([s.get('name', '') for s in skills])
            else:
                skills_text = ", ".join(skills)
            return skills_text, 0.9
        
        return "[MISSING]", 0.0
    
    def _get_legal_field(self, field_type: str) -> tuple[str, float]:
        """Get legal/compliance fields"""
        # These typically need user input
        preferences = self.user.preferences or {}
        
        # Handle preferences as either string (JSON) or dict
        if isinstance(preferences, str):
            try:
                preferences = json.loads(preferences)
            except json.JSONDecodeError:
                preferences = {}
        
        if field_type == 'workAuth':
            return preferences.get('work_authorization', "[MISSING]"), 0.5
        elif field_type == 'sponsorship':
            return preferences.get('requires_sponsorship', "[MISSING]"), 0.5
        
        return "[MISSING]", 0.0
    
    def _init_llm(self):
        """Initialize Claude LLM if not already done"""
        if not self.llm:
            self.llm = ChatAnthropic(
                model="claude-3-7-sonnet-20250219",
                temperature=0.3,
                max_tokens=500,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
            )
    
    async def _get_llm_suggestion(self, field: FormField) -> tuple[str, float]:
        """Get LLM-generated suggestion for a field"""
        try:
            self._init_llm()
            
            # Build context about the user
            user_context = self._build_user_context()
            
            # Build job context if available
            job_info = ""
            if self.job_context:
                job_info = f"""
                Job Details:
                - Title: {self.job_context.title or 'Not specified'}
                - Company: {self.job_context.company or 'Not specified'}
                - Location: {self.job_context.location or 'Not specified'}
                - Description: {self.job_context.description[:500] if self.job_context.description else 'Not provided'}
                """
            
            # Create prompt based on field category
            prompt = self._create_field_prompt(field, user_context, job_info)
            
            # Get response from Claude
            messages = [
                SystemMessage(content="""You are an intelligent form-filling assistant helping someone apply for jobs. Your primary goal is to FILL IN AS MANY FIELDS AS POSSIBLE using the user's data.

CRITICAL RULES:
1. ALWAYS try to provide an answer if you have relevant information
2. Analyze what the question is REALLY asking for - look beyond exact wording
3. If you have partial information that could answer the question, USE IT
4. Only return empty if you truly have NO relevant information
5. Return ONLY the answer text, no explanations or meta-commentary
6. NEVER return error messages like "I don't have" or "I cannot" - return empty string instead
7. For skill/experience questions: The user HAS a resume - find relevant content and use it
8. Character limits are STRICT - if specified, stay within the exact limit

LOCATION PARSING:
- Extract location components from the user's Location field in their CV
- Parse intelligently: "City, State/Province, Country" format
- Remove descriptors like "Area", "Bay Area", "Greater", etc.
- For country dropdowns, use full names: "United States", "United Kingdom", "Germany"
- Use the ACTUAL location from the CV, not placeholder values

NAME PARSING:
- Extract from the 'Full Name:' field in the user context
- First Name = FIRST word/part of the full name (e.g., 'John' from 'John Smith')
- Last Name = EVERYTHING AFTER the first name (e.g., 'Smith' from 'John Smith')
- NEVER swap first and last names - order matters!

UNDERSTANDING QUESTIONS:
- Questions can be phrased in countless ways - understand the INTENT
- For name fields: "First Name" means FIRST part of full name, "Last Name" means EVERYTHING AFTER first name
- "Do you have experience with X?" -> Check if X appears ANYWHERE in resume (skills, experience, projects)
- "Are you familiar with Y?" -> Look for Y in ALL sections - even partial matches count
- "How many years..." -> Calculate from the experience dates in resume
- "Describe your experience..." -> Summarize relevant parts from their actual background
- "List any..." -> Search comprehensively through skills, experience, education, projects
- "Have you worked with..." -> Check experience descriptions, skills, and projects
- "What is your level in..." -> Provide proficiency if mentioned anywhere
- "Tell me about..." -> Find and summarize relevant information
- "Please provide..." -> Look for the requested information in all sections
- Open text fields -> Use relevant experience and skills to craft a response

PROACTIVE ANSWERING:
- If asked about a skill/technology and it appears ANYWHERE in the user's profile, mention it
- If asked about experience and you see related work, describe it
- If asked for examples and you have any relevant experience, provide them
- For location fields, ALWAYS use the actual location from the CV
- When in doubt, if you have ANY relevant information, provide it

FORMAT MATCHING:
- Yes/No questions: Answer "Yes" or "No" based on the data
- Number questions: Return just the number
- List questions: Comma-separated or line-separated as appropriate
- Descriptive questions: Brief, relevant response from the data
- Dropdown fields: Return the exact text that would match an option

Remember: It's better to provide relevant information than to leave fields empty. The user can always edit if needed."""),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Extract the response text
            suggestion = response.content.strip()
            
            # Check for error responses from the LLM
            # Be more selective - only reject clear error messages, not valid responses
            error_indicators = [
                "Chatbot:", "ChatGPT:", "Assistant:", "I apologize",
                "I'm an AI", "As an AI", "I am an AI"
            ]
            
            # Check if it's JUST an error message (short response with error indicator)
            if len(suggestion) < 50:
                short_error_indicators = ["I don't have", "I cannot", "I'm sorry", "Unable to", "I need"]
                if any(indicator in suggestion for indicator in short_error_indicators):
                    return "", 0.0
            
            # Always reject if it starts with bot identifiers
            if any(suggestion.startswith(indicator) for indicator in error_indicators):
                return "", 0.0
            
            # Don't return [MISSING] from LLM, return empty if we can't generate
            if "[MISSING]" in suggestion or not suggestion:
                return "", 0.0
            
            # Clean up the response - remove any meta commentary
            if ":" in suggestion and suggestion.startswith(("Chatbot", "ChatGPT", "Assistant")):
                suggestion = suggestion.split(":", 1)[1].strip()
            
            # Return with confidence of 0.7 for LLM-generated content
            return suggestion, 0.7
            
        except Exception as e:
            log.error(f"Error getting LLM suggestion: {e}")
            return "[MISSING]", 0.0
    
    def _build_user_context(self) -> str:
        """Build context about the user from their resume"""
        if not self.resume_data:
            # If no resume data, try to use user object data
            context_parts = []
            if self.user:
                if self.user.name:
                    context_parts.append(f"Full Name: {self.user.name}")
                elif self.user.first_name and self.user.last_name:
                    context_parts.append(f"Full Name: {self.user.first_name} {self.user.last_name}")
                if self.user.email:
                    context_parts.append(f"Email: {self.user.email}")
                if self.user.phone:
                    context_parts.append(f"Phone: {self.user.phone}")
                if self.user.address:
                    context_parts.append(f"Location: {self.user.address}")
            return "\n".join(context_parts) if context_parts else "No user data available."
        
        context_parts = []
        
        # Personal info from resume
        personal = self.resume_data.get('personalInfo', {})
        if personal:
            # Try different name field combinations
            name = ""
            if personal.get('name'):
                name = personal.get('name')
            elif personal.get('fullName'):
                name = personal.get('fullName')
            elif personal.get('firstName') or personal.get('lastName'):
                first = personal.get('firstName', '')
                last = personal.get('lastName', '')
                name = f"{first} {last}".strip()
            
            # Fallback to user object if no name in resume
            if not name and self.user:
                if self.user.name:
                    name = self.user.name
                elif hasattr(self.user, 'first_name') and hasattr(self.user, 'last_name'):
                    if self.user.first_name and self.user.last_name:
                        name = f"{self.user.first_name} {self.user.last_name}"
            
            if name:
                context_parts.append(f"Full Name: {name}")
                # Also add explicit first/last name hints for better parsing
                name_parts = name.split(maxsplit=1)
                if len(name_parts) == 2:
                    context_parts.append(f"(First: {name_parts[0]}, Last: {name_parts[1]})")
            
            if personal.get('email'):
                context_parts.append(f"Email: {personal.get('email')}")
            if personal.get('phone'):
                context_parts.append(f"Phone: {personal.get('phone')}")
            # Get location with more detail
            location = personal.get('location', '')
            if not location and self.user and self.user.address:
                location = self.user.address
            
            if location:
                context_parts.append(f"Location: {location}")
                # Parse location components for better context
                location_parts = location.split(',')
                if len(location_parts) >= 2:
                    city = location_parts[0].strip().replace(' Area', '')
                    country = location_parts[-1].strip()
                    context_parts.append(f"City: {city}")
                    context_parts.append(f"Country: {country}")
        
        # Professional summary
        if self.resume_data.get('professionalSummary'):
            context_parts.append(f"Summary: {self.resume_data['professionalSummary'][:200]}...")
        
        # Experience - Include more detail for better responses
        experience = self.resume_data.get('experience', [])
        if experience:
            context_parts.append(f"Years of experience: {self._calculate_years_of_experience()}")
            # Include details from recent roles
            for i, job in enumerate(experience[:3]):  # Top 3 recent roles
                role_info = f"Role {i+1}: {job.get('jobTitle', '')} at {job.get('company', '')}"
                if job.get('description'):
                    # Include first 200 chars of description
                    role_info += f" - {job.get('description', '')[:200]}"
                context_parts.append(role_info)
        
        # Education
        education = self.resume_data.get('education', [])
        if education:
            recent_edu = education[0]
            context_parts.append(f"Education: {recent_edu.get('degree', '')} from {recent_edu.get('institution', '')}")
        
        # Skills - Include ALL skills for comprehensive matching
        skills = self.resume_data.get('skills', [])
        if skills:
            if isinstance(skills[0], dict):
                skills_list = [s.get('name', '') for s in skills if s.get('name')]
            else:
                skills_list = skills
            # Group skills for better readability
            if len(skills_list) > 15:
                context_parts.append(f"Technical skills ({len(skills_list)} total): {', '.join(skills_list[:15])}...")
                context_parts.append(f"Additional skills: {', '.join(skills_list[15:])}")
            else:
                context_parts.append(f"Key skills: {', '.join(skills_list)}")
        
        return "\n".join(context_parts)
    
    def _calculate_years_of_experience(self) -> int:
        """Calculate total years of experience from resume"""
        try:
            experience = self.resume_data.get('experience', [])
            if not experience:
                return 0
            
            # Simple calculation: from first job start to now
            first_job = experience[-1]  # Assuming chronological order
            if first_job.get('dates', {}).get('start'):
                start_date = first_job['dates']['start']
                # Parse year from date string (assuming format like "2020" or "2020-01")
                start_year = int(start_date[:4])
                current_year = datetime.now().year
                return current_year - start_year
        except:
            return 0
        return 0
    
    def _create_field_prompt(self, field: FormField, user_context: str, job_info: str) -> str:
        """Create a specific prompt based on field type"""
        category_parts = field.category.split('.')
        main_category = category_parts[0] if category_parts else ''
        sub_category = category_parts[1] if len(category_parts) > 1 else ''
        
        base_prompt = f"""
        User Information:
        {user_context}
        
        {job_info}
        
        Field to fill:
        - Label: {field.label}
        - Name: {field.name}
        - Category: {field.category}
        - Placeholder: {field.placeholder or 'None'}
        """
        
        # Address and location parsing with improved CV location usage
        if main_category == 'personal':
            if sub_category in ['firstName', 'first_name'] or 'first' in field.label.lower():
                base_prompt += """\nExtract ONLY the FIRST name from the 'Full Name' field in the user information above.
                
                IMPORTANT: The first name is the FIRST WORD in the full name.
                Examples:
                - 'John Smith' -> 'John' (NOT 'Smith')
                - 'Mary Jane Doe' -> 'Mary' (NOT 'Jane' or 'Doe')
                - 'Jean-Pierre Martin' -> 'Jean-Pierre' (hyphenated names stay together)
                - 'Robert James Wilson' -> 'Robert' (NOT 'James' or 'Wilson')
                
                Look for 'Full Name:' in the context above and extract the FIRST part only.
                Return ONLY the first name, nothing else. Do NOT return the last name."""
            elif sub_category in ['lastName', 'last_name'] or 'last' in field.label.lower():
                base_prompt += """\nExtract ONLY the LAST name(s) from the 'Full Name' field in the user information above.
                
                IMPORTANT: The last name is everything AFTER the first name.
                Examples:
                - 'John Smith' -> 'Smith' (NOT 'John')
                - 'Mary Jane Doe' -> 'Jane Doe' (everything after 'Mary')
                - 'Jean-Pierre Martin' -> 'Martin' (the last word/surname)
                - 'Robert James Wilson' -> 'James Wilson' (everything after 'Robert')
                - 'Ana Garcia Lopez' -> 'Garcia Lopez' (compound last names stay together)
                
                Look for 'Full Name:' in the context above and extract everything AFTER the first name.
                Return ONLY the last name(s), nothing else. Do NOT return the first name."""
            elif sub_category in ['city', 'town'] or 'city' in field.label.lower():
                base_prompt += """\nExtract ONLY the city name from the Location/City field in the user's information above.
                Examples:
                - 'New York, NY, USA' -> 'New York'
                - 'San Francisco Bay Area' -> 'San Francisco'
                - 'London, United Kingdom' -> 'London'
                - 'Berlin, Germany' -> 'Berlin'
                Look for the City field or parse it from the Location field.
                Return ONLY the city name without 'Area' or other descriptors."""
            elif sub_category in ['state', 'province'] or 'state' in field.label.lower():
                base_prompt += """\nExtract the state/province if applicable from the user's location.
                For countries without states/provinces, return empty.
                For US locations, return the state abbreviation (e.g., 'CA', 'NY').
                Examples:
                - 'San Francisco, CA, USA' -> 'CA'
                - 'Berlin, Germany' -> empty
                - 'Toronto, Ontario, Canada' -> 'Ontario'"""
            elif sub_category in ['country'] or 'country' in field.label.lower():
                base_prompt += """\nExtract the country from the user's Location or Country field.
                Return the FULL country name suitable for dropdown selection.
                Examples:
                - 'New York, NY, USA' -> 'United States'
                - 'London, UK' -> 'United Kingdom'
                - 'Berlin, Germany' -> 'Germany'
                - 'Toronto, Canada' -> 'Canada'
                Look for the Country field or extract it from the Location field.
                Return standard country names (not abbreviations)."""
            elif sub_category in ['zip', 'zipCode', 'postalCode'] or 'zip' in field.label.lower() or 'postal' in field.label.lower():
                base_prompt += "\nIf you have a zip/postal code in the user's data, return it. Otherwise return empty. Do not make up postal codes."
            elif sub_category in ['address', 'street', 'streetAddress'] or 'address' in field.label.lower():
                base_prompt += """\nFor street address fields:
                - If you have a specific street address with number and street name, return it
                - If you only have city/country information, return empty
                - Do NOT use city name as street address
                - Only fill if you have an actual street address"""
            elif sub_category == 'nationality' or 'nationality' in field.label.lower():
                base_prompt += """\nInfer nationality from the location or country in the user's data.
                Examples:
                - United States/US location -> 'American'
                - United Kingdom/UK location -> 'British'
                - Germany/German location -> 'German'
                - Canada/Canadian location -> 'Canadian'
                - France/French location -> 'French'
                Return the nationality adjective based on the country."""
        
        # Custom questions and skills
        elif main_category == 'questions' or main_category == 'skills':
            label_lower = field.label.lower() if field.label else ''
            name_lower = field.name.lower() if field.name else ''
            combined_text = f"{label_lower} {name_lower}"
            
            # Skills and experience questions - expanded list
            skill_indicators = ['skill', 'technology', 'technologies', 'programming', 'language', 
                              'framework', 'tool', 'expertise', 'proficient', 'experience with',
                              'familiar with', 'knowledge', 'competenc', 'technical', 'stack',
                              'platform', 'database', 'software', 'certification', 'qualified',
                              'relevant experience', 'describe your', 'experience for this',
                              'worked with', 'used', 'background', 'qualification', 'abilities',
                              'capabilities', 'strengths', 'achievements', 'accomplishments',
                              'projects', 'responsibilities', 'duties', 'tasks']
            
            if any(indicator in combined_text for indicator in skill_indicators):
                # Check if there's a character limit mentioned in label, placeholder, or nearby text
                char_limit_match = None
                
                # Look for character limits in various places
                import re
                full_text = f"{field.label or ''} {field.placeholder or ''} {field.name or ''}".lower()
                
                # Look for patterns like "200 characters" or "200 char" or "(200)"
                if 'character' in full_text or 'char' in full_text:
                    # Extract all numbers from the text
                    numbers = re.findall(r'\d+', full_text)
                    if numbers:
                        # Take the first reasonable character limit (usually 100-1000)
                        for num in numbers:
                            num_int = int(num)
                            if 50 <= num_int <= 5000:  # Reasonable character limit range
                                char_limit_match = num_int
                                break
                
                if char_limit_match:
                    base_prompt += f"""\nDescribe the user's relevant skills and experience for this position.
                    IMPORTANT: Response must be EXACTLY {char_limit_match} characters or less (not words, characters).
                    Focus on the most relevant skills and experience from their profile.
                    Be concise and specific. Use their actual skills and experience.
                    Make every character count - provide maximum value within the limit."""
                else:
                    base_prompt += f"""\nThis is asking about skills/experience. 
                    Analyze the exact question: '{field.label}'
                    
                    IMPORTANT: The user HAS a resume with skills and experience. Find and use it!
                    - Look through their work experience and describe relevant parts
                    - Include specific technologies, tools, and skills from their profile
                    - If asking to describe experience, provide a compelling summary
                    - Focus on accomplishments and technical skills
                    - Be specific - mention actual projects, technologies, and achievements
                    
                    The user's profile contains their full work history - USE IT.
                    Don't leave this empty - provide a strong response based on their actual background."""
            
            elif 'why' in combined_text or 'interest' in combined_text or 'motivat' in combined_text:
                base_prompt += "\nGenerate a brief, professional response about why the candidate is interested in this role/company based on their background and the job context."
            
            elif 'salary' in combined_text or 'compensation' in combined_text or 'pay' in combined_text:
                base_prompt += "\nProvide a professional salary expectation response. If unclear, respond with 'Competitive with market rates for this role and location'."
            
            elif 'start' in combined_text or 'available' in combined_text or 'begin' in combined_text:
                base_prompt += "\nProvide a reasonable start date (e.g., '2 weeks from offer acceptance' or 'Immediately')."
            
            elif 'notice' in combined_text:
                base_prompt += "\nProvide a standard notice period (e.g., '2 weeks', '1 month', '30 days')."
            
            elif 'year' in combined_text and 'experience' in combined_text:
                base_prompt += "\nCalculate years of experience from the user's work history. Return just the number."
            
            # Additional question patterns
            elif 'degree' in combined_text or 'education' in combined_text or 'university' in combined_text or 'college' in combined_text:
                base_prompt += """\nProvide information about the user's education from their resume.
                Include degree, institution, and graduation year if available.
                If asking for highest degree, provide the most advanced degree."""
            
            elif 'authorization' in combined_text or 'authorized to work' in combined_text or 'work permit' in combined_text or 'visa' in combined_text:
                base_prompt += """\nCheck if the user has mentioned work authorization in their profile.
                Common responses: 'Yes', 'Authorized to work in [country]', or check their profile for visa/work status."""
            
            elif 'citizenship' in combined_text or 'citizen' in combined_text:
                base_prompt += """\nIf citizenship information is available in the profile, provide it.
                Otherwise, you may infer from location if appropriate, or leave empty."""
            
            elif 'language' in combined_text and ('speak' in combined_text or 'fluent' in combined_text or 'proficiency' in combined_text):
                base_prompt += """\nList languages the user speaks if mentioned in their profile.
                Include proficiency levels if available (native, fluent, professional, basic)."""
            
            elif 'relocate' in combined_text or 'relocation' in combined_text or 'willing to move' in combined_text:
                base_prompt += """\nProvide a professional response about relocation willingness.
                Default to 'Open to relocation for the right opportunity' if not specified."""
            
            elif 'remote' in combined_text or 'hybrid' in combined_text or 'onsite' in combined_text or 'in-office' in combined_text:
                base_prompt += """\nProvide a response about work arrangement preferences.
                Common responses: 'Open to remote/hybrid/onsite', 'Prefer remote', etc."""
            
            elif 'reference' in combined_text:
                base_prompt += """\nProvide a standard response about references.
                Common response: 'Available upon request' or 'Yes' if it's a yes/no question."""
            
            elif 'portfolio' in combined_text or 'github' in combined_text or 'website' in combined_text:
                base_prompt += """\nProvide links to portfolio, GitHub, or personal website if available in the user's profile.
                Check for website, linkedin, github fields."""
            
            elif 'hear about' in combined_text or 'how did you' in combined_text or 'where did you find' in combined_text:
                base_prompt += """\nProvide a professional response about how they found the position.
                Common responses: 'Company website', 'LinkedIn', 'Job board', 'Professional network'."""
            
            elif any(word in combined_text for word in ['gap', 'unemployed', 'break', 'time off']):
                base_prompt += """\nIf there are employment gaps in the resume, provide a brief professional explanation.
                Otherwise, respond 'No significant gaps in employment'."""
            
            elif 'travel' in combined_text and 'willing' in combined_text:
                base_prompt += """\nProvide a response about travel willingness.
                Common responses: 'Yes', 'Up to 25%', 'As needed for the role'."""
            
            elif 'certif' in combined_text or 'license' in combined_text:
                base_prompt += """\nList any certifications or licenses mentioned in the user's profile.
                Include certification names and dates if available."""
            
            elif 'clearance' in combined_text or 'security' in combined_text:
                base_prompt += """\nIf security clearance is mentioned in profile, provide it.
                Otherwise: 'Eligible to obtain clearance' or 'No current clearance'."""
            
            else:
                base_prompt += f"""\nAnalyze this question carefully: '{field.label}'
                
                IMPORTANT: This is a question that needs answering. Look for:
                1. What type of information is being requested?
                2. Is there relevant data in the user's profile that could answer this?
                3. Can you infer a reasonable answer from their background?
                4. Is this asking for a yes/no, a description, a list, or a specific value?
                
                Search through ALL sections of the resume for relevant information:
                - Personal info for contact/location questions
                - Experience for work-related questions
                - Education for academic questions
                - Skills for technical questions
                - Summary for overall background questions
                
                Provide the most appropriate response from the user's data.
                If you have ANY relevant information that could help answer this question, provide it.
                Remember: questions can be phrased many different ways but ask for the same information."""
        
        elif main_category == 'professional':
            if sub_category == 'yearsOfExperience':
                base_prompt += "\nCalculate and return just the number of years of experience."
            elif sub_category == 'currentTitle':
                base_prompt += "\nReturn the user's current or most recent job title."
            elif sub_category == 'desiredSalary':
                base_prompt += "\nProvide a salary range based on the role and location."
        
        return base_prompt

# API Endpoints

@router.get("/status")
async def get_extension_status(
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
) -> ExtensionStatus:
    """Get extension status and user readiness"""
    
    # Check if extension is enabled
    preferences = current_user.preferences or {}
    
    # Handle preferences as either string (JSON) or dict
    if isinstance(preferences, str):
        try:
            preferences = json.loads(preferences) if preferences else {}
        except json.JSONDecodeError:
            preferences = {}
    
    extension_settings = preferences.get('chrome_extension', {})
    
    # Check for resume
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(desc(Resume.updated_at))
        .limit(1)
    )
    resume = result.scalar_one_or_none()
    
    # Check profile completeness
    profile_complete = all([
        current_user.name,
        current_user.email,
        resume is not None
    ])
    
    return ExtensionStatus(
        extensionEnabled=extension_settings.get('enabled', True),
        hasResume=resume is not None,
        resumeUpdated=resume.updated_at if resume else None,
        profileComplete=profile_complete
    )

@router.post("/autofill")
async def autofill_form(
    request: AutofillRequest,
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
) -> AutofillResponse:
    """Process autofill request from extension"""
    
    # Check if extension is enabled
    preferences = current_user.preferences or {}
    
    # Handle preferences as either string (JSON) or dict
    if isinstance(preferences, str):
        try:
            preferences = json.loads(preferences) if preferences else {}
        except json.JSONDecodeError:
            preferences = {}
    
    extension_settings = preferences.get('chrome_extension', {})
    
    if not extension_settings.get('enabled', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Extension is disabled in settings"
        )
    
    # Initialize form filler with job context
    filler = FormFillerService(current_user, db, request.formStructure.jobContext)
    
    # Load resume
    if not await filler.load_resume():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found. Please create a resume first."
        )
    
    # Process each field
    field_values = {}
    confidence_scores = {}
    missing_info = {}
    
    for field in request.formStructure.fields:
        # Skip password fields
        if (field.type == 'password' or 
            'password' in field.name.lower() or 
            'password' in field.category.lower() or
            (field.label and 'password' in field.label.lower())):
            continue
            
        value, confidence = await filler.get_field_value(field)
        
        if value == "[MISSING]":
            missing_info[field.id] = f"Please provide {field.label or field.name}"
        else:
            field_values[field.id] = value
            confidence_scores[field.id] = confidence
    
    return AutofillResponse(
        fieldValues=field_values,
        confidence=confidence_scores,
        missingInfo=missing_info
    )

@router.post("/save-response")
async def save_application_response(
    request: dict,
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Save an application field response for future reuse"""
    from app.models_db import SavedApplicationResponse
    
    field_category = request.get('category')
    field_label = request.get('label')
    field_value = request.get('value')
    set_as_default = request.get('setAsDefault', False)
    
    if not all([field_category, field_label, field_value]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Check if this response already exists
    result = await db.execute(
        select(SavedApplicationResponse)
        .where(
            SavedApplicationResponse.user_id == current_user.id,
            SavedApplicationResponse.field_category == field_category,
            SavedApplicationResponse.field_value == field_value
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing response
        existing.usage_count += 1
        existing.last_used = datetime.now()
        if set_as_default:
            # Reset other defaults for this category
            await db.execute(
                update(SavedApplicationResponse)
                .where(
                    SavedApplicationResponse.user_id == current_user.id,
                    SavedApplicationResponse.field_category == field_category,
                    SavedApplicationResponse.id != existing.id
                )
                .values(is_default=False)
            )
            existing.is_default = True
    else:
        # Create new response
        if set_as_default:
            # Reset other defaults for this category
            await db.execute(
                update(SavedApplicationResponse)
                .where(
                    SavedApplicationResponse.user_id == current_user.id,
                    SavedApplicationResponse.field_category == field_category
                )
                .values(is_default=False)
            )
        
        new_response = SavedApplicationResponse(
            user_id=current_user.id,
            field_category=field_category,
            field_label=field_label,
            field_value=field_value,
            is_default=set_as_default,
            usage_count=1,
            last_used=datetime.now()
        )
        db.add(new_response)
    
    await db.commit()
    return {"success": True, "message": "Response saved successfully"}

@router.get("/saved-responses/{category}")
async def get_saved_responses(
    category: str,
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
) -> list:
    """Get saved responses for a specific field category"""
    from app.models_db import SavedApplicationResponse
    
    result = await db.execute(
        select(SavedApplicationResponse)
        .where(
            SavedApplicationResponse.user_id == current_user.id,
            SavedApplicationResponse.field_category == category
        )
        .order_by(
            desc(SavedApplicationResponse.is_default),
            desc(SavedApplicationResponse.usage_count),
            desc(SavedApplicationResponse.last_used)
        )
    )
    responses = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "value": r.field_value,
            "label": r.field_label,
            "isDefault": r.is_default,
            "usageCount": r.usage_count,
            "lastUsed": r.last_used.isoformat() if r.last_used else None
        }
        for r in responses
    ]

@router.delete("/saved-response/{response_id}")
async def delete_saved_response(
    response_id: str,
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a saved response"""
    from app.models_db import SavedApplicationResponse
    
    result = await db.execute(
        select(SavedApplicationResponse)
        .where(
            SavedApplicationResponse.id == response_id,
            SavedApplicationResponse.user_id == current_user.id
        )
    )
    response = result.scalar_one_or_none()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    await db.delete(response)
    await db.commit()
    
    return {"success": True, "message": "Response deleted successfully"}

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
) -> ExtensionSettings:
    """Get extension settings"""
    
    preferences = current_user.preferences or {}
    
    # Handle preferences as either string (JSON) or dict
    if isinstance(preferences, str):
        try:
            preferences = json.loads(preferences) if preferences else {}
        except json.JSONDecodeError:
            preferences = {}
    
    extension_settings = preferences.get('chrome_extension', {})
    
    return ExtensionSettings(
        enabled=extension_settings.get('enabled', True),
        autoDetect=extension_settings.get('autoDetect', True),
        typingSpeed=extension_settings.get('typingSpeed', 100)
    )

@router.put("/settings")
async def update_settings(
    settings: ExtensionSettings,
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
):
    """Update extension settings"""
    
    # Get current preferences
    preferences = current_user.preferences or {}
    
    # Handle preferences as either string (JSON) or dict
    if isinstance(preferences, str):
        try:
            preferences = json.loads(preferences) if preferences else {}
        except json.JSONDecodeError:
            preferences = {}
    
    # Update chrome extension settings
    preferences['chrome_extension'] = settings.dict()
    
    # Store back as dict (SQLAlchemy will handle JSON serialization)
    current_user.preferences = preferences
    
    await db.commit()
    
    return {"message": "Settings updated successfully"}

@router.post("/save-input")
async def save_user_input(
    request: SaveInputRequest,
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
):
    """Save user input for future use"""
    
    # Get current preferences
    preferences = current_user.preferences or {}
    
    # Handle preferences as either string (JSON) or dict
    if isinstance(preferences, str):
        try:
            preferences = json.loads(preferences) if preferences else {}
        except json.JSONDecodeError:
            preferences = {}
    
    # Initialize saved_fields if not exists
    if 'saved_fields' not in preferences:
        preferences['saved_fields'] = {}
    
    # Save field value
    field_key = f"{request.field['category']}_{request.field['name']}"
    preferences['saved_fields'][field_key] = {
        'value': request.value,
        'updated_at': datetime.now().isoformat(),
        'context': request.context
    }
    
    # Store back as dict
    current_user.preferences = preferences
    
    await db.commit()
    
    return {"message": "Input saved successfully"}

@router.get("/verify")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """Verify auth token is valid"""
    return {"valid": True, "user_id": str(current_user.id)}

@router.post("/extract-from-screenshot")
async def extract_from_screenshot(
    request: Request,
    current_user: User = Depends(get_user_from_token_or_clerk),
    db: AsyncSession = Depends(get_db)
):
    """Extract job information from a screenshot using AI vision"""
    try:
        # Get the form data
        form_data = await request.form()
        
        # Get the screenshot file
        screenshot_file = form_data.get("screenshot")
        if not screenshot_file:
            raise HTTPException(status_code=400, detail="No screenshot provided")
        
        # Get the URL
        url = form_data.get("url", "")
        
        # Read the screenshot content
        screenshot_content = await screenshot_file.read()
        
        # Initialize the AI model
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=1024
        )
        
        # Create the vision message
        import base64
        screenshot_b64 = base64.b64encode(screenshot_content).decode()
        
        messages = [
            SystemMessage(content="""You are an AI assistant that extracts job information from screenshots of job posting pages.

Extract the following information from the job posting screenshot and return it as JSON:
- title: The job title/position name
- company: The company name
- location: The job location (city, state, remote status, etc.)
- description: The full job description text
- salary: Any salary/compensation information if visible
- type: Employment type (full-time, part-time, contract, remote, etc.)
- requirements: Any key requirements or qualifications listed

Return ONLY a valid JSON object with these fields. If any field is not found, use an empty string.
Example format:
{
  "title": "Software Engineer",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "description": "We are looking for...",
  "salary": "$80K - $120K",
  "type": "Full-time",
  "requirements": ["Bachelor's degree", "3+ years experience"]
}"""),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": f"Extract job information from this screenshot of a job posting page. URL: {url}"
                },
                {
                    "type": "image",
                    "image": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot_b64
                    }
                }
            ])
        ]
        
        # Get the AI response
        response = await llm.ainvoke(messages)
        
        # Parse the JSON response
        try:
            job_data = json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response if it has extra text
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                job_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse AI response as JSON")
        
        # Validate that we have at least a title
        if not job_data.get("title"):
            raise ValueError("No job title found in the screenshot")
        
        log.info(f"Successfully extracted job data from screenshot for user {current_user.id}")
        
        return job_data
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error extracting job data from screenshot: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to extract job information: {str(e)}"
        )