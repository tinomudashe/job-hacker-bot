import logging
import httpx
from bs4 import BeautifulSoup
from typing import List, Optional, Union
from pydantic import BaseModel, HttpUrl, Field
from fastapi import APIRouter, Body, HTTPException, UploadFile, File, Form, Depends

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from google.cloud import speech
from app.db import get_db
from app.models_db import User
from app.dependencies import get_current_active_user
from app.usage import UsageManager


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

# --- Helper Functions ---

async def transcribe_audio(audio_file: UploadFile) -> str:
    """Transcribes an audio file using Google Cloud Speech-to-Text."""
    try:
        client = speech.SpeechAsyncClient()
        
        content = await audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000, # This might need adjustment based on audio source
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
         "Please generate {count} flashcards on the topic of '{topic}'. The context for these flashcards is:\n\n"
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
         "You are a helpful and encouraging tutor. Your goal is to evaluate a user's answer to a flashcard question. "
         "Determine if the answer is correct, provide constructive feedback, and give a high-quality example answer. "
         "Be supportive in your feedback, even if the answer is wrong. The output must be a JSON object that strictly follows the provided format instructions."),
        ("human", 
         "Flashcard Question: '{question}'\n\n"
         "User's Answer: '{answer}'\n\n"
         "{format_instructions}")
    ])
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2)
    
    chain = prompt | llm | parser
    
    return chain, parser.get_format_instructions()

# --- API Endpoint ---

@router.post("/flashcards/generate", response_model=FlashcardSet)
async def generate_flashcards(
    request: FlashcardRequest,
    db_user: User = Depends(get_current_active_user),
    _ = Depends(UsageManager(feature="interview_tools"))
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
    _ = Depends(UsageManager(feature="interview_tools")),
    question: str = Form(...),
    text_answer: Optional[str] = Form(None),
    audio_answer: Optional[UploadFile] = File(None)
):
    """
    Provides feedback on a user's answer to a flashcard question.
    Accepts either a text answer or a base64-encoded audio file.
    """
    if not text_answer and not audio_answer:
        raise HTTPException(status_code=400, detail="Either 'text_answer' or 'audio_answer' must be provided.")
    if text_answer and audio_answer:
        raise HTTPException(status_code=400, detail="Provide either 'text_answer' or 'audio_answer', not both.")

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