from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

# Optional import for Google Cloud Text-to-Speech - graceful fallback if not available
try:
    from google.cloud import texttospeech
    from google.api_core.client_options import ClientOptions
    TTS_AVAILABLE = True
except ImportError:
    texttospeech = None
    ClientOptions = None
    TTS_AVAILABLE = False
    print("⚠️  Google Cloud Text-to-Speech module not available in TTS. Text-to-speech will be disabled.")

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-Chirp3-HD-Achernar"
    api_key: str

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
    if not TTS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Text-to-speech service unavailable. Google Cloud Text-to-Speech module is not installed or configured."
        )
    
    try:
        client_options = ClientOptions(api_key=request.api_key)
        client = texttospeech.TextToSpeechClient(client_options=client_options)
        synthesis_input = texttospeech.SynthesisInput(text=request.text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", name=request.voice
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return Response(content=response.audio_content, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 