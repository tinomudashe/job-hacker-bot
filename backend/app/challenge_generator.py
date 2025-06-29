import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Body, HTTPException, Depends
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.models_db import User
from app.dependencies import get_current_active_user
from app.usage import UsageManager

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pydantic Models ---

class CodingChallengeRequest(BaseModel):
    job_description: str

class CodingChallenge(BaseModel):
    title: str
    difficulty: str
    problem_statement: str
    examples: List[str]
    constraints: Optional[str] = "No specific constraints."

# --- Agent Logic ---

def create_challenge_generation_agent():
    """Sets up the agent for generating coding challenges."""
    
    parser = JsonOutputParser(pydantic_object=CodingChallenge)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert hiring manager and senior software engineer. Your task is to create a relevant coding challenge based on the provided job description. "
         "The challenge should be practical and test the core technical skills mentioned. The output must be a JSON object that strictly follows the provided format instructions."),
        ("human", 
         "Please generate a coding challenge based on this job description:\n\n"
         "--- JOB DESCRIPTION ---\n"
         "{job_description}\n"
         "--- END JOB DESCRIPTION ---\n\n"
         "{format_instructions}")
    ])
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
    
    chain = prompt | llm | parser
    
    return chain, parser.get_format_instructions()

# --- API Endpoint ---

@router.post("/challenges/generate", response_model=CodingChallenge)
async def generate_coding_challenge(
    request: CodingChallengeRequest = Body(
        ...,
        examples={
            "default": {
                "summary": "Example Job Description for a Backend Engineer",
                "value": {
                    "job_description": "We are seeking a Backend Python Developer with experience in FastAPI, PostgreSQL, and building RESTful APIs. The ideal candidate will be skilled in data modeling and creating efficient, scalable services. Experience with cloud platforms like AWS is a plus."
                }
            }
        }
    ),
    _: bool = Depends(UsageManager(feature="interview_tools"))
):
    """
    Generates a coding challenge based on a job description.
    """
    try:
        logger.info("Initializing coding challenge generation agent.")
        agent, format_instructions = create_challenge_generation_agent()
        
        logger.info("Generating challenge...")
        challenge = await agent.ainvoke({
            "job_description": request.job_description,
            "format_instructions": format_instructions
        })
        
        return challenge
    except Exception as e:
        logger.error(f"Error generating coding challenge: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate coding challenge.") 