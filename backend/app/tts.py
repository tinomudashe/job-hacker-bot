import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Setup logger
logger = logging.getLogger(__name__)

# Optional import for Google Cloud Text-to-Speech - graceful fallback if not available
try:
    from google.cloud import texttospeech
    from google.api_core.client_options import ClientOptions
    TTS_AVAILABLE = True
except ImportError:
    texttospeech = None
    ClientOptions = None
    TTS_AVAILABLE = False
    logger.warning("Google Cloud Text-to-Speech module not found. Text-to-speech will be disabled.")

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User

router = APIRouter()

# --- Securely load API Key and initialize client at startup ---
google_api_key = os.getenv("GOOGLE_API_KEY")
tts_client = None

if TTS_AVAILABLE and google_api_key:
    try:
        client_options = ClientOptions(api_key=google_api_key)
        tts_client = texttospeech.TextToSpeechClient(client_options=client_options)
        logger.info("✅ Google Cloud Text-to-Speech client initialized successfully.")
    except Exception as e:
        tts_client = None
        TTS_AVAILABLE = False
        logger.error(f"❌ Failed to initialize Google Cloud Text-to-Speech client: {e}")
elif not google_api_key:
    TTS_AVAILABLE = False
    logger.warning("⚠️ GOOGLE_API_KEY environment variable not set. Text-to-speech will be disabled.")

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-Chirp3-HD-Achernar"

@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Convert text to speech using Google Cloud Text-to-Speech API.
    Requires authentication and Google Cloud Text-to-Speech service.
    """
    if not TTS_AVAILABLE or not tts_client:
        raise HTTPException(
            status_code=503,
            detail="Text-to-speech service is not available or configured correctly. Check backend logs for details."
        )
    
    try:
        synthesis_input = texttospeech.SynthesisInput(text=request.text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", name=request.voice
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return Response(content=response.audio_content, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Google TTS API error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred with the text-to-speech service.") 