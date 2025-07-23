import logging
import re
from typing import Dict, Optional, List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, EmailStr
import json
from pathlib import Path
import io
import docx
from PIL import Image
from pdf2image import convert_from_path
from pypdf import PdfReader

from app.resume import ResumeData, PersonalInfo, Experience, Education, Dates
from app.llm_utils import call_llm_for_json_extraction

logger = logging.getLogger(__name__)

class ExtractedPersonalInfo(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    profile_summary: Optional[str] = None

class ExtractedExperience(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class ExtractedEducation(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

class ExtractedSkills(BaseModel):
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    languages: List[str] = []
    certifications: List[str] = []

class CVExtractionResult(BaseModel):
    personal_info: ExtractedPersonalInfo
    experience: List[ExtractedExperience] = []
    education: List[ExtractedEducation] = []
    skills: ExtractedSkills
    raw_text: str
    confidence_score: float = 0.0

class CVProcessor:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.1,
            convert_system_message_to_human=True
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
        """Extract structured information from CV using LLM"""
        try:
            # Extract raw text
            raw_text = self.extract_text_from_file(file_path)
            
            if not raw_text.strip():
                raise ValueError("No text could be extracted from the file")
            
            # Use LLM to extract structured information
            extraction_prompt = self._create_extraction_prompt(raw_text)
            response = await self.llm.ainvoke(extraction_prompt)
            
            # Parse the LLM response
            extracted_data = self._parse_llm_response(response.content, raw_text)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting CV information: {e}")
            raise
    
    def _create_extraction_prompt(self, cv_text: str) -> str:
        """Create a prompt for LLM to extract structured information from CV"""
        return f"""
You are an expert CV/Resume parser. Extract the following information from the CV text below and return it as a JSON object.

IMPORTANT: Return ONLY valid JSON, no additional text or formatting.

Expected JSON structure:
{{
    "personal_info": {{
        "full_name": "Full name of the person",
        "first_name": "First name only",
        "last_name": "Last name only", 
        "email": "Email address",
        "phone": "Phone number",
        "address": "Full address or location",
        "linkedin": "LinkedIn profile URL",
        "website": "Personal website URL",
        "profile_summary": "Professional summary or objective"
    }},
    "experience": [
        {{
            "job_title": "Position title",
            "company": "Company name",
            "duration": "Employment duration (e.g., '2020-2023')",
            "description": "Job description and achievements"
        }}
    ],
    "education": [
        {{
            "degree": "Degree name",
            "institution": "University/School name",
            "graduation_year": "Year of graduation",
            "gpa": "GPA if mentioned"
        }}
    ],
    "skills": {{
        "technical_skills": ["List of technical skills"],
        "soft_skills": ["List of soft skills"],
        "languages": ["Languages spoken"],
        "certifications": ["Professional certifications"]
    }},
    "confidence_score": 0.95
}}

CV TEXT:
{cv_text}

Extract all available information. If a field is not found, use null for strings or empty arrays for lists. Be as accurate as possible and ensure the confidence_score reflects how well you could extract the information (0.0 to 1.0).
"""
    
    def _parse_llm_response(self, response: str, raw_text: str) -> CVExtractionResult:
        """Parse the LLM response and create a structured result"""
        try:
            # Clean the response to extract JSON
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            
            # Parse JSON
            data = json.loads(response_clean)
            
            # Create structured objects
            personal_info = ExtractedPersonalInfo(**data.get('personal_info', {}))
            
            experience = [
                ExtractedExperience(**exp) 
                for exp in data.get('experience', [])
            ]
            
            education = [
                ExtractedEducation(**edu) 
                for edu in data.get('education', [])
            ]
            
            skills = ExtractedSkills(**data.get('skills', {}))
            
            confidence_score = data.get('confidence_score', 0.5)
            
            return CVExtractionResult(
                personal_info=personal_info,
                experience=experience,
                education=education,
                skills=skills,
                raw_text=raw_text,
                confidence_score=confidence_score
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Response was: {response}")
            
            # Fallback: create a basic result with manual extraction
            return self._fallback_extraction(raw_text)
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
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
            skills=ExtractedSkills(),
            raw_text=raw_text,
            confidence_score=0.3  # Lower confidence for fallback
        )

# Global instance
cv_processor = CVProcessor() 