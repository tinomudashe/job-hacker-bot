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
from app.usage import UsageManager

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pydantic Models ---

class CoverLetterRequest(BaseModel):
    job_description: str
    company_name: str
    job_title: str
    user_name: str
    user_skills: str # A summary of user's skills

class CoverLetterResponse(BaseModel):
    cover_letter_text: str

# --- Agent Logic ---

def create_cover_letter_chain():
    """Sets up the chain for generating cover letters."""
    
    prompt = ChatPromptTemplate.from_template(
        "You are an expert career coach. Write a professional and compelling cover letter.\n\n"
        "**My Details:**\n"
        "Name: {user_name}\n"
        "My key skills: {user_skills}\n\n"
        "**Job Details:**\n"
        "Company: {company_name}\n"
        "Position: {job_title}\n"
        "Job Description: {job_description}\n\n"
        "Please draft a cover letter that is tailored to this specific role, highlighting how my skills align with the job description. Do not include placeholders for contact information like address or phone number."
    )
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
    
    chain = prompt | llm | StrOutputParser()
    
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
    Generates a cover letter based on user details and a job description.
    """
    try:
        logger.info(f"Generating cover letter for {request.job_title} at {request.company_name}")
        chain = create_cover_letter_chain()
        
        cover_letter_text = await chain.ainvoke({
            "user_name": request.user_name,
            "user_skills": request.user_skills,
            "company_name": request.company_name,
            "job_title": request.job_title,
            "job_description": request.job_description,
        })
        
        # Save record to database
        new_record = GeneratedCoverLetter(
            id=str(uuid4()),
            user_id=db_user.id,
            content=cover_letter_text
        )
        db.add(new_record)
        await db.commit()
        
        return CoverLetterResponse(cover_letter_text=cover_letter_text)

    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate cover letter.") 