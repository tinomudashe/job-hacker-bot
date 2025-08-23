import logging
import re
from typing import Dict, Optional, List, Any
from langchain_anthropic import ChatAnthropic
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, EmailStr, Field, validator
import json
from pathlib import Path
import io
import docx
from PIL import Image
from pdf2image import convert_from_path
from pypdf import PdfReader

from app.resume import ResumeData, PersonalInfo, Experience, Education, Dates

logger = logging.getLogger(__name__)

class ExtractedPersonalInfo(BaseModel):
    """Personal information extracted from CV. Only extract information that is explicitly present."""
    full_name: Optional[str] = Field(None, description="Full name as it appears in the CV")
    first_name: Optional[str] = Field(None, description="First name only")
    last_name: Optional[str] = Field(None, description="Last name only")
    email: Optional[str] = Field(None, description="Email address if present")
    phone: Optional[str] = Field(None, description="Phone number exactly as shown")
    address: Optional[str] = Field(None, description="Location, city, or full address")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL if present")
    website: Optional[str] = Field(None, description="Personal website or portfolio URL")
    profile_summary: Optional[str] = Field(None, description="Professional summary or objective statement")
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format to prevent hallucination"""
        if v and '@' not in v:
            return None
        return v
    
    @validator('linkedin')
    def validate_linkedin(cls, v):
        """Ensure LinkedIn URL is valid"""
        if v and 'linkedin.com' not in v.lower():
            return None
        return v

class ExtractedExperience(BaseModel):
    """Work experience entry. Extract only information explicitly stated in the CV."""
    job_title: Optional[str] = Field(None, description="Job title or position exactly as written")
    company: Optional[str] = Field(None, description="Company or organization name")
    duration: Optional[str] = Field(None, description="Employment period (e.g., 'Jan 2020 - Dec 2023')")
    description: Optional[str] = Field(None, description="Job responsibilities and achievements, preserving bullet points")

class ExtractedEducation(BaseModel):
    """Education entry. Only include information that is explicitly present."""
    degree: Optional[str] = Field(None, description="Degree or qualification name exactly as written")
    institution: Optional[str] = Field(None, description="School/university name")
    graduation_year: Optional[str] = Field(None, description="Graduation year or dates")
    gpa: Optional[str] = Field(None, description="GPA if explicitly mentioned")

class ExtractedSkills(BaseModel):
    """Skills extracted from CV. Only include skills explicitly mentioned."""
    technical_skills: List[str] = Field(default_factory=list, description="Programming languages, tools, frameworks")
    soft_skills: List[str] = Field(default_factory=list, description="Communication, leadership, teamwork skills")
    languages: List[str] = Field(default_factory=list, description="Spoken/written languages")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications")

class ExtractedProject(BaseModel):
    """Project information. Extract only what is explicitly stated."""
    title: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description and achievements")
    technologies: Optional[str] = Field(None, description="Technologies used")
    url: Optional[str] = Field(None, description="Project URL if provided")
    github: Optional[str] = Field(None, description="GitHub repository URL if provided")
    duration: Optional[str] = Field(None, description="Project duration or dates")

class CVExtractionResult(BaseModel):
    """Complete CV extraction result with all sections. Only extract information that is explicitly present in the CV text."""
    personal_info: ExtractedPersonalInfo = Field(..., description="Personal contact information")
    experience: List[ExtractedExperience] = Field(default_factory=list, description="Work experience entries")
    education: List[ExtractedEducation] = Field(default_factory=list, description="Education entries")
    projects: List[ExtractedProject] = Field(default_factory=list, description="Project entries")
    skills: ExtractedSkills = Field(default_factory=ExtractedSkills, description="Skills section")
    confidence_score: float = Field(0.95, description="Confidence in extraction accuracy (0-1)")
    
    @validator('experience', 'education', 'projects')
    def limit_list_size(cls, v):
        """Limit lists to prevent hallucinated entries"""
        return v[:20] if v else []  # Maximum 20 entries per section

class CVProcessor:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0.1,
            max_tokens=4096
        )
    
    def extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from PDF, DOCX, or TXT files"""
        try:
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension == '.docx':
                return self._extract_from_docx(file_path)
            elif file_extension in ['.txt', '.md']:
                return self._extract_from_text(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(str(file_path))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            raise
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(str(file_path))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            raise
    
    def _extract_from_text(self, file_path: Path) -> str:
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            raise
    
    async def extract_cv_information(self, file_path: Path) -> CVExtractionResult:
        """Extract structured information from CV using LLM with structured output"""
        try:
            # Extract raw text
            raw_text = self.extract_text_from_file(file_path)
            
            if not raw_text.strip():
                raise ValueError("No text could be extracted from the file")
            
            # Create parser for structured output
            parser = PydanticOutputParser(pydantic_object=CVExtractionResult)
            
            # Create prompt with format instructions
            prompt = PromptTemplate(
                template="""You are an expert CV/Resume parser. Extract information from the CV text below.

CRITICAL INSTRUCTIONS:
1. ONLY extract information that is EXPLICITLY stated in the CV
2. Do NOT invent, assume, or hallucinate any information
3. If information is not present, leave the field as null or empty
4. Preserve exact text for names, titles, and dates
5. Keep all bullet points and descriptions in their original form
6. Do not add information that seems logical but is not in the text

{format_instructions}

CV TEXT:
{cv_text}

IMPORTANT: Only extract what you can directly quote or reference from the CV text above. If you cannot find specific information, do not make it up.""",
                input_variables=["cv_text"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # Use structured output with the LLM
            structured_llm = self.llm.with_structured_output(CVExtractionResult)
            
            try:
                # Try structured output first (most reliable)
                extracted_data = await structured_llm.ainvoke(
                    prompt.format(cv_text=raw_text[:8000])  # Limit text to avoid token limits
                )
                
                # Add raw_text to the result for reference
                if isinstance(extracted_data, CVExtractionResult):
                    # Create a new instance with raw_text
                    return CVExtractionResult(
                        personal_info=extracted_data.personal_info,
                        experience=extracted_data.experience,
                        education=extracted_data.education,
                        projects=extracted_data.projects,
                        skills=extracted_data.skills,
                        confidence_score=extracted_data.confidence_score
                    )
                    
            except Exception as e:
                logger.warning(f"Structured output failed, falling back to parsing: {e}")
                # Fallback to traditional parsing
                response = await self.llm.ainvoke(prompt.format(cv_text=raw_text[:8000]))
                extracted_data = self._parse_llm_response(response.content, raw_text)
                
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting CV information: {e}")
            raise
    
    
    def _parse_llm_response(self, response: str, raw_text: str) -> CVExtractionResult:
        """Parse the LLM response and create a structured result"""
        try:
            # Clean the response to extract JSON - handle multiple formats
            response_clean = response.strip()
            
            # Remove code block markers
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            elif response_clean.startswith('```'):
                response_clean = response_clean[3:]
            
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            # Remove any trailing/leading whitespace and newlines
            response_clean = response_clean.strip()
            
            # Try to find JSON object if there's extra text
            json_start = response_clean.find('{')
            json_end = response_clean.rfind('}')
            if json_start != -1 and json_end != -1:
                response_clean = response_clean[json_start:json_end+1]
            
            # Parse JSON
            data = json.loads(response_clean)
            
            # Create structured objects
            personal_info = ExtractedPersonalInfo(**data.get('personal_info', {}))
            
            # FIX: More robust experience parsing with field variations
            experience = []
            experience_list = data.get('experience', [])
            
            # Handle case where experience is a JSON string that needs parsing
            if isinstance(experience_list, str):
                try:
                    experience_list = json.loads(experience_list)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse experience string as JSON: {experience_list[:100]}...")
                    experience_list = []
            
            if isinstance(experience_list, list):
                for exp_item in experience_list:
                    if isinstance(exp_item, dict):
                        experience.append(ExtractedExperience(
                            job_title=exp_item.get("job_title") or exp_item.get("title") or exp_item.get("position"),
                            company=exp_item.get("company") or exp_item.get("organization") or exp_item.get("employer"),
                            duration=exp_item.get("duration") or exp_item.get("dates") or exp_item.get("period"),
                            description=exp_item.get("description") or exp_item.get("responsibilities") or exp_item.get("duties")
                        ))
            
            # FIX: Replace the strict education parsing with a more robust and forgiving loop
            # that handles variations in the LLM's output.
            education = []
            education_list = data.get('education', [])
            
            # Handle case where education is a JSON string that needs parsing
            if isinstance(education_list, str):
                try:
                    education_list = json.loads(education_list)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse education string as JSON: {education_list[:100]}...")
                    education_list = []
            if isinstance(education_list, list):
                for edu_item in education_list:
                    if isinstance(edu_item, dict):
                        education.append(ExtractedEducation(
                            degree=edu_item.get("degree"),
                            # It now accepts 'institution', 'university', or 'school'
                            institution=edu_item.get("institution") or edu_item.get("university") or edu_item.get("school"),
                            # It now accepts 'graduation_year' or 'year'
                            graduation_year=edu_item.get("graduation_year") or edu_item.get("year"),
                            gpa=edu_item.get("gpa")
                        ))
            
            # Parse projects with more field variations
            projects = []
            projects_list = data.get('projects', [])
            
            # Handle case where projects is a JSON string that needs parsing
            if isinstance(projects_list, str):
                try:
                    projects_list = json.loads(projects_list)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse projects string as JSON: {projects_list[:100]}...")
                    projects_list = []
            
            if isinstance(projects_list, list):
                for proj_item in projects_list:
                    if isinstance(proj_item, dict):
                        projects.append(ExtractedProject(
                            title=proj_item.get("title") or proj_item.get("name") or proj_item.get("project_name"),
                            description=proj_item.get("description") or proj_item.get("details") or proj_item.get("summary"),
                            technologies=proj_item.get("technologies") or proj_item.get("tech_stack") or proj_item.get("tools") or proj_item.get("stack"),
                            url=proj_item.get("url") or proj_item.get("link") or proj_item.get("website"),
                            github=proj_item.get("github") or proj_item.get("repository") or proj_item.get("repo"),
                            duration=proj_item.get("duration") or proj_item.get("date") or proj_item.get("dates") or proj_item.get("period")
                        ))
            
            # Parse skills with safer handling
            skills_data = data.get('skills', {})
            if isinstance(skills_data, dict):
                skills = ExtractedSkills(
                    technical_skills=skills_data.get('technical_skills', []) or [],
                    soft_skills=skills_data.get('soft_skills', []) or [],
                    languages=skills_data.get('languages', []) or [],
                    certifications=skills_data.get('certifications', []) or []
                )
            else:
                skills = ExtractedSkills()
            
            confidence_score = data.get('confidence_score', 0.5)
            
            return CVExtractionResult(
                personal_info=personal_info,
                experience=experience,
                education=education,
                projects=projects,
                skills=skills,
                confidence_score=confidence_score
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Response was: {response[:500]}...")  # Log first 500 chars to avoid huge logs
            
            # Try to manually extract some key information if JSON parsing fails
            return self._try_manual_parse(response, raw_text)
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Data type errors or missing fields")
            return self._fallback_extraction(raw_text)
    
    def _try_manual_parse(self, response: str, raw_text: str) -> CVExtractionResult:
        """Try to manually parse response when JSON parsing fails"""
        try:
            # Look for common patterns in the response
            personal_info = ExtractedPersonalInfo()
            
            # Try to find name
            name_match = re.search(r'"full_name"\s*:\s*"([^"]+)"', response)
            if name_match:
                personal_info.full_name = name_match.group(1)
                name_parts = personal_info.full_name.split()
                if len(name_parts) >= 2:
                    personal_info.first_name = name_parts[0]
                    personal_info.last_name = name_parts[-1]
            
            # Try to find email
            email_match = re.search(r'"email"\s*:\s*"([^"]+)"', response)
            if email_match:
                personal_info.email = email_match.group(1)
            
            # Try to find phone
            phone_match = re.search(r'"phone"\s*:\s*"([^"]+)"', response)
            if phone_match:
                personal_info.phone = phone_match.group(1)
            
            return CVExtractionResult(
                personal_info=personal_info,
                experience=[],
                education=[],
                projects=[],
                skills=ExtractedSkills(),
                confidence_score=0.4  # Lower confidence for manual parse
            )
        except Exception as e:
            logger.error(f"Manual parse also failed: {e}")
            return self._fallback_extraction(raw_text)
    
    def _fallback_extraction(self, raw_text: str) -> CVExtractionResult:
        """Fallback extraction using regex patterns when LLM fails"""
        logger.info("Using fallback extraction methods")
        
        personal_info = ExtractedPersonalInfo()
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, raw_text)
        if emails:
            personal_info.email = emails[0]
        
        # Extract phone number
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, raw_text)
            if phones:
                personal_info.phone = phones[0]
                break
        
        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_matches = re.findall(linkedin_pattern, raw_text, re.IGNORECASE)
        if linkedin_matches:
            personal_info.linkedin = f"https://{linkedin_matches[0]}"
        
        # Try to extract name from the first few lines
        lines = raw_text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if line and len(line.split()) <= 4 and not '@' in line and not 'linkedin' in line.lower():
                # Likely a name
                personal_info.full_name = line
                name_parts = line.split()
                if len(name_parts) >= 2:
                    personal_info.first_name = name_parts[0]
                    personal_info.last_name = name_parts[-1]
                break
        
        return CVExtractionResult(
            personal_info=personal_info,
            experience=[],
            education=[],
            projects=[],
            skills=ExtractedSkills(),
            confidence_score=0.3  # Lower confidence for fallback
        )

# Global instance
cv_processor = CVProcessor() 