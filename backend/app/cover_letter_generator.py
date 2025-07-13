import logging
from pydantic import BaseModel, HttpUrl
from fastapi import APIRouter, Body, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.db import get_db
from app.models_db import User, GeneratedCoverLetter
from app.dependencies import get_current_active_user
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from app.usage import UsageManager

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pydantic Models ---

class PersonalInfo(BaseModel):
    """Structured personal information for the user."""
    fullName: str
    email: str
    phone: str
    linkedin: str
    website: str | None = None

class CoverLetterDetails(BaseModel):
    """The structured output for the generated cover letter."""
    company_name: str
    job_title: str
    recipient_name: str | None = None
    recipient_title: str | None = None
    body: str
    personal_info: PersonalInfo

class CoverLetterRequest(BaseModel):
    """The request model for generating a cover letter."""
    job_description: str
    company_name: str
    job_title: str
    user_profile: PersonalInfo
    user_skills: str

class CoverLetterResponse(BaseModel):
    """The final structured response from the endpoint."""
    structured_cover_letter: CoverLetterDetails

# --- Agent Logic ---

def create_cover_letter_chain():
    """Sets up the chain for generating structured cover letters."""
    
    parser = PydanticOutputParser(pydantic_object=CoverLetterDetails)
    
    prompt = ChatPromptTemplate.from_template(
        "You are an expert career coach AI. Your task is to generate a professional and compelling cover letter based on the provided user and job details.\n\n"
        "**User Profile:**\n"
        "Name: {fullName}\n"
        "Email: {email}\n"
        "Phone: {phone}\n"
        "LinkedIn: {linkedin}\n"
        "Website: {website}\n"
        "Key Skills Summary: {user_skills}\n\n"
        "**Job Details:**\n"
        "Company: {company_name}\n"
        "Position: {job_title}\n"
        "Job Description: {job_description}\n\n"
        "**Instructions:**\n"
        "1.  Analyze the job description and the user's skills to create a highly tailored cover letter body.\n"
        "2.  Highlight the strongest alignments between the user's experience and the job requirements.\n"
        "3.  If possible, infer the hiring manager's name and title from the job description (e.g., 'reports to the Engineering Manager'). If not, leave them as null.\n"
        "4.  The cover letter body should be professional, concise, and engaging. Do not include placeholders for contact info in the body itself, as it is handled separately.\n"
        "5.  Fill out the personal information from the provided user profile.\n\n"
        "**Output Format:**\n"
        "Please format your response as a JSON object that strictly follows this schema:\n"
        "{format_instructions}\n",
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
    
    chain = prompt | llm | parser
    
    return chain

# --- API Endpoint ---

@router.post("/cover-letters/generate", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterRequest,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user),
    _ = Depends(UsageManager(feature="cover_letters"))
):
    """
    Generates a structured cover letter based on user details and a job description.
    """
    try:
        logger.info(f"Generating structured cover letter for {request.job_title} at {request.company_name}")
        chain = create_cover_letter_chain()
        
        structured_result = await chain.ainvoke({
            "fullName": request.user_profile.fullName,
            "email": request.user_profile.email,
            "phone": request.user_profile.phone,
            "linkedin": request.user_profile.linkedin,
            "website": request.user_profile.website,
            "user_skills": request.user_skills,
            "company_name": request.company_name,
            "job_title": request.job_title,
            "job_description": request.job_description,
        })
        
        # Save the structured record to the database as a JSON string
        new_record = GeneratedCoverLetter(
            id=str(uuid4()),
            user_id=db_user.id,
            content=structured_result.model_dump_json()
        )
        db.add(new_record)
        await db.commit()
        
        return CoverLetterResponse(structured_cover_letter=structured_result)

    except Exception as e:
        logger.error(f"Error generating structured cover letter: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate structured cover letter.")