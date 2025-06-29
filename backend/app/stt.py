from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from google.cloud import speech
from pydantic import BaseModel
from google.api_core.client_options import ClientOptions

router = APIRouter()

class STTResponse(BaseModel):
    transcript: str

@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    api_key: str = Form(...)
):
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