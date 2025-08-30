import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
from app.users import router as users_router
from app.documents import router as documents_router
from app.rag import router as rag_router
from app.applications import router as applications_router
from app.agent import router as agent_router
from app.cv_generator import router as cv_generator_router
from app.challenge_generator import router as challenge_generator_router
from app.flashcard_generator import router as flashcard_generator_router
from app.orchestrator import router as orchestrator_router
from app.billing import router as billing_router
from app.cover_letter_generator import router as cover_letter_router
from app.resume import router as resume_router
from app.resume_generator import router as resume_generator_router
from app.job_search import router as job_search_router
from app.test_regenerate import router as test_regenerate_router
from app.messages import router as messages_router
from app.uploads import router as uploads_router
from app.tts import router as tts_router
from app.stt import router as stt_router
from app.pages import router as pages_router
from app.pdf_generator import router as pdf_router
from app.cover_letter_documents import router as cover_letter_documents_router
from app.marketing import router as marketing_router
from app.admin import router as admin_router
from app.email_api import router as email_router
from app.onboarding import router as onboarding_router
from app.chrome_extension_api import router as chrome_extension_router
from app.extension_tokens import router as extension_tokens_router
from app.tailored_resumes import router as tailored_resumes_router

app = FastAPI()

app_url = os.getenv("APP_URL", "https://jobhackerbot.com")
# Configure CORS
origins = [
    app_url,
    "https://www.jobhackerbot.com",  # Production with www
    "https://jobhackerbot.com",      # Production without www  
    "http://localhost:3000",         # Local development
    "chrome-extension://*",          # Chrome extensions
]

# For Chrome extensions, we need to allow all origins since the extension ID varies
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Chrome extension compatibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers will be included here
# from .users import router as users_router
# from .documents import router as documents_router
app.include_router(users_router, prefix="/api")
app.include_router(documents_router, prefix="/api", tags=["documents"])
app.include_router(rag_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(agent_router, prefix="/api", tags=["agent"])
app.include_router(cv_generator_router, prefix="/api", tags=["cv"])
app.include_router(challenge_generator_router, prefix="/api", tags=["challenges"])
app.include_router(flashcard_generator_router, prefix="/api", tags=["flashcards"])
app.include_router(orchestrator_router, prefix="/api", tags=["orchestrator"])
app.include_router(billing_router, prefix="/api/billing", tags=["billing"])
app.include_router(cover_letter_router, prefix="/api", tags=["cover-letters"])
app.include_router(resume_router, prefix="/api", tags=["resume"])
app.include_router(tailored_resumes_router, prefix="/api", tags=["tailored-resumes"])
app.include_router(resume_generator_router, prefix="/api", tags=["resume-generator"])
app.include_router(job_search_router, prefix="/api", tags=["job-search"])
app.include_router(test_regenerate_router, prefix="/api", tags=["test-regenerate"])
app.include_router(messages_router, prefix="/api", tags=["messages"])
app.include_router(uploads_router, prefix="/api", tags=["uploads"])
app.include_router(tts_router, prefix="/api", tags=["tts"])
app.include_router(stt_router, prefix="/api", tags=["stt"])
app.include_router(pages_router, prefix="/api", tags=["pages"])
app.include_router(pdf_router, prefix="/api", tags=["pdf"])
app.include_router(cover_letter_documents_router, prefix="/api", tags=["cover-letter-documents"])
app.include_router(marketing_router, tags=["marketing"])
app.include_router(admin_router, tags=["admin"])
app.include_router(email_router, tags=["email"])
app.include_router(onboarding_router, prefix="/api", tags=["onboarding"])
app.include_router(chrome_extension_router, tags=["chrome-extension"])
app.include_router(extension_tokens_router, tags=["extension-tokens"])

# Add validation error handler to see what's failing
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.url}: {exc.errors()}")
    logger.error(f"Request body: {exc.body}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(exc.body)[:500]},
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Application Automation API"} 