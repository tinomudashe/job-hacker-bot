import logging
import httpx
from bs4 import BeautifulSoup
from typing import List, Optional, Union
from pydantic import BaseModel, HttpUrl, Field
from fastapi import APIRouter, Body, HTTPException, UploadFile, File, Form, Depends

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Optional import for Google Cloud Speech - graceful fallback if not available
try:
    from google.cloud import speech
    SPEECH_AVAILABLE = True
except ImportError:
    # Define placeholder for speech when not available
    speech = None
    SPEECH_AVAILABLE = False
    print("⚠️  Google Cloud Speech module not available. Audio transcription will be disabled.")

from app.db import get_db
from app.models_db import User
from app.dependencies import get_current_active_user


logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pydantic Models ---

class Flashcard(BaseModel):
    question: str
    answer: str

class FlashcardSet(BaseModel):
    flashcards: List[Flashcard]

class FlashcardRequest(BaseModel):
    source_type: str = Field(..., description="Type of source: 'job_description', 'url', or 'language'")
    content: str = Field(..., description="The job description, URL, or programming language name.")
    count: int = Field(10, gt=0, le=50, description="Number of flashcards to generate.")

class FeedbackRequest(BaseModel):
    question: str
    answer: str

class FeedbackResponse(BaseModel):
    feedback: str
    is_correct: bool
    tone_score: int = Field(..., ge=1, le=10, description="Tone quality score from 1-10")
    correctness_score: int = Field(..., ge=1, le=10, description="Content correctness score from 1-10")
    confidence_score: int = Field(..., ge=1, le=10, description="Confidence level score from 1-10")
    overall_score: int = Field(..., ge=1, le=10, description="Overall performance score from 1-10")
    improvement_tips: str = Field(..., description="Specific tips for improvement")

# --- Helper Functions ---

def extract_cv_details(content: str) -> str:
    """Extract detailed CV information from interview preparation content."""
    cv_details = ""
    
    # Extract user context section
    if "USER CONTEXT:" in content:
        lines = content.split('\n')
        in_user_context = False
        for line in lines:
            if "USER CONTEXT:" in line:
                in_user_context = True
                cv_details += line + "\n"
            elif in_user_context and line.startswith(("TARGET ROLE:", "COMPANY:", "INTERVIEW TYPE:")):
                break
            elif in_user_context:
                cv_details += line + "\n"
    
    # Look for specific background info patterns in the guide
    patterns_to_extract = [
        "Background:", "Recent Role:", "Key Skills:", "Experience:",
        "Current Role:", "worked at", "experience with", "Full-Stack",
        "freelance", "Upwork", "conversion", "React", "Next.js",
        "Spring Boot", "technologies", "projects", "achievements"
    ]
    
    lines = content.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(pattern.lower() in line_lower for pattern in patterns_to_extract):
            cv_details += line + "\n"
            
        # Extract company and technology mentions
        if any(word in line_lower for word in ["worked", "developed", "built", "created", "implemented"]):
            cv_details += line + "\n"
    
    # Look for flashcard data that might contain CV-specific questions
    if "<!--FLASHCARD_DATA:" in content:
        import re
        flashcard_match = re.search(r'<!--FLASHCARD_DATA:(.*?)-->', content, re.DOTALL)
        if flashcard_match:
            try:
                import json
                flashcard_data = json.loads(flashcard_match.group(1))
                for item in flashcard_data:
                    if isinstance(item, dict) and 'question' in item:
                        question = item['question']
                        # Extract company/technology names from existing questions
                        if any(keyword in question.lower() for keyword in ["worked", "company", "project", "experience"]):
                            cv_details += f"Previous question context: {question}\n"
            except:
                pass
    
    return cv_details.strip()

async def transcribe_audio(audio_file: UploadFile) -> str:
    """Transcribes an audio file using Google Cloud Speech-to-Text."""
    if not SPEECH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Audio transcription service unavailable. Google Cloud Speech module is not installed or configured."
        )
    
    try:
        client = speech.SpeechAsyncClient()
        
        content = await audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000, # This might need adjustment based on audio source
            language_code="en-US",
        )

        response = await client.recognize(config=config, audio=audio)

        if not response.results or not response.results[0].alternatives:
            raise HTTPException(status_code=400, detail="Could not transcribe audio. The audio may be empty or unclear.")

        return response.results[0].alternatives[0].transcript
    except Exception as e:
        logger.error(f"Google Cloud Speech-to-Text error: {e}")
        # Note: You might need to set up Google Cloud authentication for this to work.
        # e.g., export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
        raise HTTPException(status_code=500, detail="Failed to process audio file.")

async def scrape_url_content(url: HttpUrl) -> str:
    """Scrapes the main textual content from a URL."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(str(url))
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        # Get text
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit text to a reasonable length for the LLM
        return text[:15000]

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error scraping {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Could not fetch content from URL: {e.name}")
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        raise HTTPException(status_code=500, detail="Failed to scrape content from URL.")

# --- Agent Logic ---

def create_flashcard_generation_agent():
    """Sets up the agent for generating flashcards."""
    
    parser = JsonOutputParser(pydantic_object=FlashcardSet)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert educator and content creator. Your task is to generate a set of high-quality flashcards based on the provided context. "
         "The questions should be clear and concise, and the answers should be accurate and informative. The output must be a JSON object that strictly follows the provided format instructions."),
        ("human", 
         "Generate {count} flashcards for '{topic}'. \n\n"
         "IMPORTANT INSTRUCTIONS:\n"
         "- If the topic mentions 'interview questions', generate ACTUAL interview questions that would be asked in a real job interview\n"
         "- Focus on realistic questions an interviewer would ask, not questions about the preparation material itself\n"
         "- Use the context to understand the job role, company, and candidate background to create relevant questions\n"
         "- Include a mix of: behavioral, technical, situational, and CV-SPECIFIC questions\n"
         "- CV-SPECIFIC questions MUST reference ACTUAL details from the candidate's background found in the context\n"
         "- NEVER use placeholders like [Company], [Project], [Technology] - always use the REAL names from the context\n"
         "- Extract specific company names, technologies, projects, achievements, and career details from the provided context\n"
         "- Make questions sound like a real interviewer who studied their resume with specific details\n"
         "- Examples of good CV-specific questions:\n"
         "  * 'I see you achieved a 5.6% conversion lift in one of your projects. Can you walk me through that?'\n"
         "  * 'You mentioned working with React and Next.js. How did you handle state management in those projects?'\n"
         "  * 'I notice you've been doing freelance work through Upwork. How do you manage client relationships?'\n"
         "- Include at least 3-4 questions that directly reference their CV details with REAL specifics\n\n"
         "--- CONTEXT ---\n"
         "{context}\n"
         "--- END CONTEXT ---\n\n"
         "{format_instructions}")
    ])
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.5)
    
    chain = prompt | llm | parser
    
    return chain, parser.get_format_instructions()

def create_feedback_agent():
    """Sets up the agent for providing feedback on an answer."""
    
    parser = JsonOutputParser(pydantic_object=FeedbackResponse)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert interview coach and communication specialist. Your task is to evaluate a user's answer to an interview question across multiple dimensions. "
         "Provide detailed, constructive feedback that helps them improve their interview performance. "
         "Rate each aspect on a scale of 1-10 and provide specific, actionable improvement tips. "
         "Be encouraging but honest in your assessment. The output must be a JSON object that strictly follows the provided format instructions."),
        ("human", 
         "Interview Question: '{question}'\n\n"
         "Candidate's Answer: '{answer}'\n\n"
         "Please evaluate this answer across the following dimensions:\n"
         "1. TONE SCORE (1-10): Assess confidence, enthusiasm, professionalism, and speaking clarity\n"
         "2. CORRECTNESS SCORE (1-10): Evaluate factual accuracy, relevance, and completeness of content\n"
         "3. CONFIDENCE SCORE (1-10): Rate how confident and self-assured the candidate sounds\n"
         "4. OVERALL SCORE (1-10): Holistic assessment of interview readiness\n\n"
         "Provide detailed feedback explaining your scores and specific tips for improvement.\n\n"
         "{format_instructions}")
    ])
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
    
    chain = prompt | llm | parser
    
    return chain, parser.get_format_instructions()

# --- API Endpoint ---

@router.post("/flashcards/generate", response_model=FlashcardSet)
async def generate_flashcards(
    request: FlashcardRequest,
    db_user: User = Depends(get_current_active_user)
):
    """
    Generates flashcards from a URL, job description, or programming language.
    """
    try:
        logger.info(f"Received request to generate {request.count} flashcards from source type '{request.source_type}'.")
        
        context = ""
        topic = request.content
        
        if request.source_type == "job_description":
            context = request.content
            # Check if this is an interview preparation guide vs actual job description
            if "[INTERVIEW_FLASHCARDS_AVAILABLE]" in request.content or "Interview Preparation Guide" in request.content:
                topic = "interview questions based on this job role and preparation content"
                
                # Extract job details and CV information for better context
                job_context = ""
                cv_context = ""
                
                if "**Role:**" in context:
                    # Extract role and company info from the guide header
                    lines = context.split('\n')
                    for line in lines:
                        if "**Role:**" in line:
                            job_context = line.strip()
                            break
                
                # Extract comprehensive CV/background information
                cv_context = extract_cv_details(context)
                logger.info(f"Extracted CV context length: {len(cv_context)} characters")
                if cv_context:
                    logger.info(f"CV context preview: {cv_context[:200]}...")
                
                if job_context:
                    role_info = job_context.replace('**Role:**', '').strip()
                    if cv_context:
                        topic = f"interview questions for {role_info} incorporating the candidate's CV background"
                        # Enhance context with extracted CV details at the top
                        context = f"CANDIDATE CV DETAILS:\n{cv_context}\n\n--- ORIGINAL CONTEXT ---\n{context}"
                    else:
                        topic = f"interview questions for {role_info}"
            else:
                topic = "the provided Job Description"
        elif request.source_type == "url":
            context = await scrape_url_content(request.content)
            topic = f"the content from {request.content}"
        elif request.source_type == "language":
            context = f"General knowledge about the {request.content} programming language."
            topic = request.content
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type provided.")

        agent, format_instructions = create_flashcard_generation_agent()
        
        logger.info(f"Generating flashcards for topic: {topic}")
        flashcard_set = await agent.ainvoke({
            "topic": topic,
            "context": context,
            "count": request.count,
            "format_instructions": format_instructions
        })
        
        return flashcard_set

    except HTTPException as e:
        raise e # Re-raise known HTTP exceptions
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate flashcards.")

@router.post("/flashcards/feedback", response_model=FeedbackResponse)
async def get_feedback_on_answer(
    db_user: User = Depends(get_current_active_user),
    question: str = Form(...),
    text_answer: Optional[str] = Form(None),
    audio_answer: Optional[UploadFile] = File(None)
):
    """
    Provides feedback on a user's answer to a flashcard question.
    Accepts either a text answer or audio file (if speech service is available).
    """
    if not text_answer and not audio_answer:
        raise HTTPException(status_code=400, detail="Either 'text_answer' or 'audio_answer' must be provided.")
    if text_answer and audio_answer:
        raise HTTPException(status_code=400, detail="Provide either 'text_answer' or 'audio_answer', not both.")
    
    # Check if audio is requested but speech service is unavailable
    if audio_answer and not SPEECH_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Audio transcription service unavailable. Please provide a text answer instead."
        )

    try:
        answer = ""
        if audio_answer:
            logger.info("Transcribing audio answer...")
            answer = await transcribe_audio(audio_answer)
            logger.info(f"Transcribed text: '{answer}'")
        else:
            answer = text_answer

        logger.info(f"Received request for feedback on question: '{question[:50]}...'")
        
        agent, format_instructions = create_feedback_agent()
        
        feedback = await agent.ainvoke({
            "question": question,
            "answer": answer,
            "format_instructions": format_instructions
        })
        
        return feedback

    except Exception as e:
        logger.error(f"Error generating feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate feedback.") 