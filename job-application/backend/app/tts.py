from fastapi import APIRouter, HTTPException
from google.cloud import texttospeech
from pydantic import BaseModel
from fastapi.responses import Response
from google.api_core.client_options import ClientOptions

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-Chirp3-HD-Achernar"
    api_key: str

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
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