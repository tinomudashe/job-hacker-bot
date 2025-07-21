from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from app.routers import jobs
from app.routers.graph_rag_demo import router as graph_rag_demo_router
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

app = FastAPI()

# Configure CORS
origins = [
    "https://jobhackerbot.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(resume_generator_router, prefix="/api", tags=["resume-generator"])
app.include_router(job_search_router, prefix="/api", tags=["job-search"])
app.include_router(jobs.router)
app.include_router(graph_rag_demo_router, prefix="/api", tags=["graph-rag-demo"])
app.include_router(test_regenerate_router, prefix="/api", tags=["test-regenerate"])
app.include_router(messages_router, prefix="/api", tags=["messages"])
app.include_router(uploads_router, prefix="/api", tags=["uploads"])
app.include_router(tts_router, prefix="/api", tags=["tts"])
app.include_router(stt_router, prefix="/api", tags=["stt"])
app.include_router(pages_router, prefix="/api", tags=["pages"])
app.include_router(pdf_router, prefix="/api", tags=["pdf"])
app.include_router(cover_letter_documents_router, prefix="/api", tags=["cover-letter-documents"])
app.include_router(messages_router, prefix="/api/chat", tags=["chat"])
app.include_router(marketing_router, tags=["marketing"])
app.include_router(admin_router, tags=["admin"])
@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Application Automation API"} 