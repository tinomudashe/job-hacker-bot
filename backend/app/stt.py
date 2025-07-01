from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Optional import for Google Cloud Speech - graceful fallback if not available
try:
    from google.cloud import speech
    from google.api_core.client_options import ClientOptions
    SPEECH_AVAILABLE = True
except ImportError:
    speech = None
    ClientOptions = None
    SPEECH_AVAILABLE = False
    print("⚠️  Google Cloud Speech module not available in STT. Speech-to-text will be disabled.")

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User

router = APIRouter()

class STTResponse(BaseModel):
    transcript: str

@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Convert speech to text using Google Cloud Speech API.
    Requires authentication and Google Cloud Speech service.
    """
    if not SPEECH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Speech-to-text service unavailable. Google Cloud Speech module is not installed or configured."
        )
    
    try:
        client = speech.SpeechClient(
            client_options={"api_key": api_key}
        )

        content = await file.read()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
        )

        response = client.recognize(config=config, audio=audio)

        if not response.results or not response.results[0].alternatives:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
            
        return STTResponse(transcript=response.results[0].alternatives[0].transcript)
    except Exception as e:
        if "Could not automatically determine credentials" in str(e):
            raise HTTPException(status_code=401, detail="Google Cloud authentication failed. Please check your API key or service account credentials.")
        raise HTTPException(status_code=500, detail=str(e)) 