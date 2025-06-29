import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.db import get_db
from app.models_db import User
from app.dependencies import get_current_active_user
from app.resume import ResumeData, PersonalInfo, Experience, Education
from app.usage import UsageManager

logger = logging.getLogger(__name__)
router = APIRouter()

class GenerateContentRequest(BaseModel):
    job_description: str
    section: str  # 'summary', 'experience', 'education', 'skills'
    context: Optional[str] = None  # Additional context for generation

def create_content_generation_chain():
    """Creates a chain for generating resume content using Gemini 2.0 Flash."""
    
    prompt = ChatPromptTemplate.from_template(
        "You are an expert resume writer with years of experience helping job seekers.\n"
        "Generate professional and impactful content for a resume section.\n\n"
        "Section to generate: {section}\n"
        "Job Description: {job_description}\n"
        "Additional Context: {context}\n\n"
        "Generate content that is:\n"
        "1. Tailored to the job description\n"
        "2. Uses strong action verbs\n"
        "3. Quantifies achievements where possible\n"
        "4. Highlights relevant skills and experiences\n"
        "5. Is concise and impactful\n\n"
        "Generate the content in a professional tone suitable for the specified section."
    )
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        top_p=0.9,
        top_k=40
    )
    
    chain = prompt | llm | StrOutputParser()
    return chain

@router.post("/resume/generate-content")
async def generate_resume_content(
    request: GenerateContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _ = Depends(UsageManager(feature="resume_generation"))
):
    """
    Generates content for a specific section of the resume using AI.
    """
    try:
        chain = create_content_generation_chain()
        
        generated_content = await chain.ainvoke({
            "section": request.section,
            "job_description": request.job_description,
            "context": request.context or "No additional context provided."
        })
        
        return {"content": generated_content}
        
    except Exception as e:
        logger.error(f"Error generating resume content: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate resume content."
        ) 