import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Setup logger
logger = logging.getLogger(__name__)

# Optional import for Google Cloud Speech - graceful fallback if not available
try:
    from google.cloud import speech
    from google.api_core.client_options import ClientOptions
    SPEECH_AVAILABLE = True
except ImportError:
    speech = None
    ClientOptions = None
    SPEECH_AVAILABLE = False
    logger.warning("Google Cloud Speech module not found. Speech-to-text will be disabled.")

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User

router = APIRouter()

# --- Securely load API Key and initialize client at startup ---
google_api_key = os.getenv("GOOGLE_API_KEY")
stt_client = None

if SPEECH_AVAILABLE and google_api_key:
    try:
        client_options = ClientOptions(api_key=google_api_key)
        stt_client = speech.SpeechClient(client_options=client_options)
        logger.info("✅ Google Cloud Speech-to-Text client initialized successfully.")
    except Exception as e:
        stt_client = None
        SPEECH_AVAILABLE = False
        logger.error(f"❌ Failed to initialize Google Cloud Speech-to-Text client: {e}")
elif not google_api_key:
    SPEECH_AVAILABLE = False
    logger.warning("⚠️ GOOGLE_API_KEY environment variable not set. Speech-to-text will be disabled.")

class STTResponse(BaseModel):
    transcript: str

@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Convert speech to text using Google Cloud Speech-to-Text API.
    This method is for short audio files (< 60 seconds).
    """
    if not SPEECH_AVAILABLE or not stt_client:
        raise HTTPException(
            status_code=503,
            detail="Speech-to-text service is not available or configured correctly. Check backend logs for details."
        )
    
    try:
        content = await file.read()
        audio = speech.RecognitionAudio(content=content)
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
        )

        response = stt_client.recognize(config=config, audio=audio)

        if not response.results or not response.results[0].alternatives:
            logger.warning("Speech-to-text transcription resulted in no content.")
            raise HTTPException(status_code=400, detail="Could not transcribe audio. The audio may be silent or unclear.")
            
        return STTResponse(transcript=response.results[0].alternatives[0].transcript)
    except Exception as e:
        logger.error(f"Google STT API error: {e}", exc_info=True)
        if "Could not automatically determine credentials" in str(e):
             raise HTTPException(status_code=401, detail="Google Cloud authentication failed.")
        raise HTTPException(status_code=500, detail="An error occurred with the speech-to-text service.") 