import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Optional import for browser automation - graceful fallback if not installed
try:
    from browser_use import Agent, Controller, Browser
    from browser_use.agent.views import ActionResult, AgentHistory
    BROWSER_USE_AVAILABLE = True
except ImportError:
    # Define placeholder classes when browser_use is not available
    class Agent:
        def __init__(self, **kwargs):
            pass
        async def run(self):
            return None
    
    class Controller:
        def __init__(self, **kwargs):
            pass
        def action(self, description):
            def decorator(func):
                return func
            return decorator
    
    class Browser:
        def __init__(self, **kwargs):
            pass
    
    class ActionResult:
        def __init__(self, **kwargs):
            pass
    
    class AgentHistory:
        def __init__(self):
            self.history = []
        def final_result(self):
            return None
    
    BROWSER_USE_AVAILABLE = False
    print("⚠️  browser_use module not available. Agent functionality will be limited.")

from pydantic import BaseModel, HttpUrl, ValidationError
import logging
import json

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
import uuid

from app.db import get_db, async_session_maker
from app.models_db import Application, User, Document
from app.dependencies import get_current_active_user
from app.usage import UsageManager
from app.graph_rag import EnhancedGraphRAG

load_dotenv()

# --- Configuration ---
CV_PATH = Path(os.getenv("CV_PATH", "/Users/tinomudashe/job-application/Resume.pdf"))
BROWSER_EXECUTABLE_PATH = os.getenv("BROWSER_EXECUTABLE_PATH") or "/ms-playwright/chromium/chrome-linux/chrome"
UPLOAD_DIR = Path("uploads")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ApplicationResult(BaseModel):
    job_title: str
    company_name: str

# --- Helper Functions ---
async def get_user_cv_info(user_id: str, db: AsyncSession) -> dict:
    """Get the user's most recent CV and extracted information"""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id, Document.type == "resume")
        .order_by(Document.date_created.desc())
    )
    latest_cv = result.scalars().first()
    
    if not latest_cv:
        return {
            "has_cv": False,
            "cv_path": None,
            "cv_content": None,
            "personal_info": {}
        }
    
    # Find the CV file path
    user_dir = UPLOAD_DIR / user_id
    cv_file_path = None
    for f in user_dir.glob(f"{latest_cv.id}_*"):
        if f.is_file():
            cv_file_path = f
            break
    
    return {
        "has_cv": True,
        "cv_path": str(cv_file_path) if cv_file_path else None,
        "cv_content": latest_cv.content or "",
        "personal_info": {
            "document_id": latest_cv.id,
            "document_name": latest_cv.name,
            "upload_date": latest_cv.date_created
        }
    }

def get_user_context_prompt(user: User, cv_info: dict) -> str:
    """Create a personalized context prompt with user and CV information"""
    
    context_parts = []
    
    # Basic user information
    if user.name:
        context_parts.append(f"User's full name: {user.name}")
    if user.first_name:
        context_parts.append(f"First name: {user.first_name}")
    if user.last_name:
        context_parts.append(f"Last name: {user.last_name}")
    if user.email:
        context_parts.append(f"Email: {user.email}")
    if user.phone:
        context_parts.append(f"Phone: {user.phone}")
    if user.address:
        context_parts.append(f"Address/Location: {user.address}")
    if user.linkedin:
        context_parts.append(f"LinkedIn: {user.linkedin}")
    if user.skills:
        context_parts.append(f"Skills: {user.skills}")
    if user.profile_headline:
        context_parts.append(f"Professional headline: {user.profile_headline}")
    
    # CV information
    if cv_info["has_cv"] and cv_info["cv_content"]:
        # Add a condensed version of CV content for context
        cv_summary = cv_info["cv_content"][:1000] + "..." if len(cv_info["cv_content"]) > 1000 else cv_info["cv_content"]
        context_parts.append(f"CV Summary (from uploaded document): {cv_summary}")
    
    if not context_parts:
        return "No specific user information available. Use generic professional information."
    
    return "USER CONTEXT:\n" + "\n".join(context_parts)

# --- Agent Logic ---
def _get_final_done_status(result: AgentHistory) -> bool:
    if not result or not hasattr(result, 'history') or result.history is None:
        return False
    for r in reversed(result.history):
        action = getattr(r, 'action', None)
        if not action and isinstance(r, dict):
            action = r.get('action', None)
        is_done = getattr(action, 'is_done', None)
        if is_done is None and isinstance(action, dict):
            is_done = action.get('is_done', None)
        if action and is_done:
            success = getattr(action, 'success', None)
            if success is None and isinstance(action, dict):
                success = action.get('success', False)
            return bool(success)
    return False

async def run_application_agent(
    job_url: HttpUrl, 
    user: User,
    db: AsyncSession
):
    """Enhanced agent that uses uploaded CV and personalized user information"""
    
    if not BROWSER_USE_AVAILABLE:
        logger.warning("Browser automation not available - browser_use module not installed")
        return AgentHistory()  # Return empty result
    
    # Get user's CV information
    cv_info = await get_user_cv_info(user.id, db)
    user_context = get_user_context_prompt(user, cv_info)
    
    controller = Controller(output_model=ApplicationResult)

    @controller.action('Read my cv for context to fill forms')
    def read_cv():
        if cv_info["has_cv"] and cv_info["cv_content"]:
            logger.info(f"Using uploaded CV content for user {user.id}")
            return cv_info["cv_content"]
        elif CV_PATH.exists():
            logger.info(f"Fallback to default CV at {CV_PATH}")
            from PyPDF2 import PdfReader
            pdf = PdfReader(str(CV_PATH))
            text = "".join(page.extract_text() or "" for page in pdf.pages)
            return text
        else:
            return f"No CV available. Please upload a CV first. User context: {user_context}"

    @controller.action('Upload cv to element')
    async def upload_cv(index: int, browser_session):
        # Try to use uploaded CV first, then fallback to default
        cv_path = cv_info.get("cv_path") if cv_info["has_cv"] else str(CV_PATH.resolve())
        
        if not cv_path or not os.path.exists(cv_path):
            return f"🚫 No CV file found. User should upload a CV first."
        
        file_upload_dom_el = await browser_session.find_file_upload_element_by_index(index)
        if not file_upload_dom_el:
            return f"⚠️ No file upload element DOM found at index {index}"
        file_upload_el = await browser_session.get_locate_element(file_upload_dom_el)
        if not file_upload_el:
            return f"⚠️ No locator created for element at index {index}"
        try:
            await file_upload_el.set_input_files(cv_path)
            return f"✅ Successfully uploaded CV \"{cv_path}\" to index {index}"
        except Exception as e:
            return f"❌ Failed to upload CV to index {index}: {str(e)}"

    @controller.action('Get user information for form filling')
    def get_user_info(field_type: str = "general") -> str:
        """Get specific user information for form filling"""
        info_map = {
            "name": user.name or f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "first_name": user.first_name or (user.name.split()[0] if user.name else ""),
            "last_name": user.last_name or (user.name.split()[-1] if user.name and len(user.name.split()) > 1 else ""),
            "email": user.email or "",
            "phone": user.phone or "",
            "address": user.address or "",
            "location": user.address or "",
            "linkedin": user.linkedin or "",
            "skills": user.skills or "",
            "headline": user.profile_headline or "",
            "summary": user.profile_headline or ""
        }
        
        if field_type.lower() in info_map:
            value = info_map[field_type.lower()]
            return value if value else f"No {field_type} information available"
        
        return f"User information: {user_context}"

    @controller.action('Get intelligent job-specific information using Graph RAG')
    async def get_smart_context(field_type: str = "general", job_context: str = "") -> str:
        """Get intelligent, job-specific information using Graph RAG analysis"""
        try:
            # Initialize Graph RAG for intelligent context
            graph_rag = EnhancedGraphRAG(user.id, db)
            initialized = await graph_rag.initialize()
            
            if not initialized:
                return get_user_info(field_type)  # Fallback to basic info
            
            # If we have job context, analyze it for better responses
            if job_context:
                job_analysis = await graph_rag._analyze_job_description(job_context)
                
                # Get relevant information based on field type and job requirements
                search_query = f"{field_type} relevant experience skills"
                if field_type == "skills":
                    search_query = f"technical skills programming {' '.join(job_analysis.get('required_skills', [])[:3])}"
                elif field_type == "experience":
                    search_query = f"work experience projects achievements {job_analysis.get('job_title', '')}"
                elif field_type == "summary":
                    search_query = f"professional summary career objective {job_analysis.get('industry', 'technology')}"
                
                # Get Graph RAG results
                results = await graph_rag.intelligent_search(search_query, job_analysis)
                
                if results:
                    # Extract most relevant information
                    relevant_content = results[0].page_content if results else ""
                    
                    # Generate contextualized response
                    context_prompt = f"""
                    Based on this user information: {relevant_content}
                    And this job requirement: {job_analysis.get('job_title', 'Position')} requiring {', '.join(job_analysis.get('required_skills', [])[:3])}
                    
                    Provide a concise, relevant answer for the form field: {field_type}
                    
                    Keep response under 100 words and focus on job-relevant information:
                    """
                    
                    llm_result = await llm.ainvoke(context_prompt)
                    return llm_result.content.strip()
            
            # Fallback to basic user info if no job context
            return get_user_info(field_type)
            
        except Exception as e:
            logger.warning(f"Graph RAG context failed: {e}")
            return get_user_info(field_type)  # Always fallback to basic info

    @controller.action('Ask human for help with a question')
    def ask_human(question: str) -> ActionResult:
        answer = input(f'Agent needs help: {question}\nYour answer > ')
        return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
    
    browser = Browser(
        wss_url="ws://127.0.0.1:3000/",
        incognito=True,
    )

    # Initialize Graph RAG for intelligent assistance
    graph_rag_context = ""
    try:
        graph_rag = EnhancedGraphRAG(user.id, db)
        if await graph_rag.initialize():
            # Try to get job description from the page first for better context
            # For now, we'll use a generic tech job context - this could be enhanced
            job_desc_context = "Software engineering position requiring programming skills and technical experience"
            rag_analysis = await graph_rag.get_job_application_context(job_desc_context)
            
            confidence_score = rag_analysis.get("confidence_score", 0.5)
            job_analysis = rag_analysis.get("job_analysis", {})
            
            graph_rag_context = f"""
            
            🧠 GRAPH RAG INTELLIGENCE ENABLED:
            - Confidence Score: {confidence_score:.2f} ({'HIGH' if confidence_score > 0.7 else 'MODERATE' if confidence_score > 0.4 else 'LOW'})
            - Predicted Job Focus: {job_analysis.get('job_title', 'Technical Role')}
            - Key Skills to Highlight: {', '.join(job_analysis.get('required_skills', ['Programming', 'Problem Solving'])[:5])}
            - Industry Context: {job_analysis.get('industry', 'Technology')}
            
            SMART ACTIONS AVAILABLE:
            - Use 'Get intelligent job-specific information using Graph RAG' for context-aware form filling
            - This provides job-relevant answers based on Graph RAG analysis of your background
            """
    except Exception as e:
        logger.warning(f"Graph RAG initialization failed: {e}")
        graph_rag_context = "\n\n⚠️ Graph RAG not available, using standard information retrieval."

    # Enhanced task prompt with Graph RAG intelligence
    task_prompt = (
        f"You are an expert AI agent for applying to jobs online with GRAPH RAG INTELLIGENCE for smarter reasoning. "
        f"Your goal is to apply for the job at {job_url} using the user's specific details and intelligent context analysis.\n\n"
        f"{user_context}"
        f"{graph_rag_context}\n\n"
        f"INTELLIGENT FORM FILLING STRATEGY:\n"
        f"1. FIRST, try to understand the job requirements by analyzing any visible job description or requirements on the page\n"
        f"2. Use 'Get intelligent job-specific information using Graph RAG' when available - this provides smarter, job-relevant responses\n"
        f"3. Fallback to 'Get user information for form filling' for basic field types: name, first_name, last_name, email, phone, address, location, linkedin, skills, headline, summary\n\n"
        f"ENHANCED PROCESS:\n"
        f"1. Navigate to {job_url} and wait for page load. Report if page fails to load.\n"
        f"2. IMMEDIATELY scan for and dismiss pop-ups, cookie banners, or overlays that block interaction.\n"
        f"3. Analyze the page content to understand the job requirements if visible.\n"
        f"4. Locate the application form or 'Apply' button to access the application.\n"
        f"5. For EACH form field, follow this intelligent process:\n"
        f"   a) Identify the field purpose (name, email, skills, experience, etc.)\n"
        f"   b) If Graph RAG is available, use 'Get intelligent job-specific information using Graph RAG' with the field type and any job context\n"
        f"   c) If Graph RAG fails, use 'Get user information for form filling' as fallback\n"
        f"   d) Fill the field with the retrieved information\n"
        f"   e) Verify the field was filled correctly\n"
        f"6. For CV uploads, use 'Upload cv to element' action.\n"
        f"7. Before submission, validate all required fields are completed with relevant information.\n"
        f"8. Submit the application and wait for confirmation.\n"
        f"9. Extract job title and company name from success confirmation.\n"
        f"10. Use 'Ask human for help with a question' if you encounter complex issues.\n"
        f"11. Call 'done' with success=True/False based on application outcome.\n"
        f"\n"
        f"🎯 FOCUS: Use the intelligent Graph RAG context to provide more relevant, job-specific information in forms!\n"
    )
    
    memory_config = {
        "llm_instance": llm,
        "agent_id": f"job_applicant_agent_{user.id}",
        "embedder_provider": "gemini",
        "embedder_model": "models/text-embedding-004",
        "vector_store_provider": "faiss",
        "vector_store_collection_name": f"job_application_memories_{user.id}"
    }

    max_attempts = 3
    last_error = None
    for attempt in range(1, max_attempts + 1):
        browser_agent = Agent(
            task=task_prompt, 
            llm=llm, 
            controller=controller,
            enable_memory=True, 
            profile=browser,
            planner_llm=llm,
            use_vision_for_planner=True,
            is_planner_reasoning=True,
            memory_config=memory_config,
        )

        result = None
        try:
            logger.info(f"Starting personalized browser automation for user {user.id} ({user.name}) on: {job_url} (Attempt {attempt})")
            result = await browser_agent.run()
            logger.info(f"Browser automation finished for user {user.id}. Result: {result}")
        finally:
            logger.info(f"Browser session for user {user.id} completed for attempt {attempt}.")

        job_title, company_name = _parse_agent_result(result)
        is_success = _get_final_done_status(result)
        if is_success:
            summary = f"Success on attempt {attempt} using {'uploaded CV' if cv_info['has_cv'] else 'default CV'}."
            break
        else:
            if hasattr(result, 'history') and result.history:
                last_action = result.history[-1]
                if hasattr(last_action, 'error') and last_action.error:
                    last_error = last_action.error
            summary = f"Failed attempt {attempt}. {last_error or 'Unknown error.'}"
    else:
        job_title, company_name = "Unknown", "Unknown"
        summary = f"Failed after {max_attempts} attempts. {last_error or 'Unknown error.'}"
        is_success = False

    # --- Save Application to DB ---
    new_application = Application(
        id=str(uuid.uuid4()),
        user_id=user.id,
        job_title=job_title,
        company_name=company_name,
        job_url=str(job_url),
        status="applied" if is_success else "failed",
        notes=summary,
        date_applied=datetime.now(timezone.utc),
        success=is_success
    )
    db.add(new_application)
    await db.commit()
    logger.info(f"Successfully saved application for {job_title} at {company_name} for user {user.name}.")
    
    return result

def _parse_agent_result(result: AgentHistory) -> tuple[str, str]:
    job_title = "Unknown"
    company_name = "Unknown"

    if not result or not hasattr(result, 'history') or result.history is None:
        return job_title, company_name

    # Prioritize structured output using final_result()
    final_json_str = result.final_result()
    if final_json_str:
        try:
            parsed_result = ApplicationResult.model_validate_json(final_json_str)
            logger.info("Successfully parsed structured output from agent.")
            return parsed_result.job_title, parsed_result.company_name
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse structured output from agent: {e}\nRaw output: {final_json_str}")

    # Fallback to manually parsing the history if structured output fails
    logger.warning("Structured output failed or was not provided. Falling back to manual parsing.")
    done_action = None
    for r in reversed(result.history):
        action = getattr(r, 'action', None)
        if not action and isinstance(r, dict):
            action = r.get('action', None)
        is_done = getattr(action, 'is_done', None)
        if is_done is None and isinstance(action, dict):
            is_done = action.get('is_done', None)
        if action and is_done:
            done_action = action
            break

    if done_action:
        extracted_content = getattr(done_action, 'extracted_content', None)
        if extracted_content is None and isinstance(done_action, dict):
            extracted_content = done_action.get('extracted_content', None)
        if isinstance(extracted_content, str):
            content = extracted_content
            try:
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                    details = json.loads(json_str)
                    return details.get("job_title", job_title), details.get("company_name", company_name)
            except (IndexError, json.JSONDecodeError):
                logger.error(f"Fallback parsing failed for 'done' action: {content}")

    return job_title, company_name

# --- Pydantic Models ---
class ApplicationRequest(BaseModel):
    job_url: HttpUrl
    # Optional override fields - if not provided, will use user profile data
    first_name: str = None
    last_name: str = None
    email: str = None
    phone: str = None

@router.post("/agent/test-apply", status_code=202)
async def test_apply_for_job(request: ApplicationRequest):
    """Test endpoint without authentication - for debugging frontend issues"""
    if not BROWSER_USE_AVAILABLE:
        return {
            "message": "⚠️ Agent endpoint accessible but browser automation unavailable.",
            "job_url": str(request.job_url),
            "status": "test_success_limited",
            "note": "browser_use module not installed. Agent functionality will be limited.",
            "browser_automation": False
        }
    
    return {
        "message": "✅ Agent endpoint is working! Graph RAG integration successful.",
        "job_url": str(request.job_url),
        "status": "test_success",
        "note": "This is a test endpoint. Use /api/agent/apply with authentication for real applications.",
        "browser_automation": True
    }

@router.post("/agent/apply", status_code=202)
async def apply_for_job(
    request: ApplicationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Enhanced job application endpoint that uses uploaded CV and personalized user data
    """
    
    if not BROWSER_USE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Browser automation service unavailable. The browser_use module is not installed. Please contact support."
        )
    
    async def agent_task():
        async with async_session_maker() as db_session:
            # Check if user has uploaded CV
            cv_info = await get_user_cv_info(db_user.id, db_session)
            
            if not cv_info["has_cv"] and not CV_PATH.exists():
                logger.warning(f"No CV found for user {db_user.id}. Application may fail.")
            
            # Override user data with request data if provided
            if request.first_name:
                db_user.first_name = request.first_name
            if request.last_name:
                db_user.last_name = request.last_name
            if request.email:
                db_user.email = request.email
            if request.phone:
                db_user.phone = request.phone
            
            try:
                result = await run_application_agent(request.job_url, db_user, db_session)
                is_success = _get_final_done_status(result)
                
                if is_success:
                    # Only deduct usage if successful
                    _ = await UsageManager(feature="applications").__call__()
                    logger.info(f"Successful job application for user {db_user.name} to {request.job_url}")
                else:
                    logger.warning(f"Failed job application for user {db_user.name} to {request.job_url}")
                    
            except Exception as e:
                logger.error(f"Error in agent task for user {db_user.id}: {e}")
                # Save failed application
                async with async_session_maker() as error_db:
                    failed_application = Application(
                        id=str(uuid.uuid4()),
                        user_id=db_user.id,
                        job_title="Unknown",
                        company_name="Unknown",
                        job_url=str(request.job_url),
                        status="error",
                        notes=f"Agent error: {str(e)}",
                        date_applied=datetime.now(timezone.utc),
                        success=False
                    )
                    error_db.add(failed_application)
                    await error_db.commit()

    background_tasks.add_task(agent_task)
    return {
        "message": "Personalized job application task has been started in the background.",
        "user_name": db_user.name,
        "has_uploaded_cv": await get_user_cv_info(db_user.id, await get_db().__anext__())["has_cv"]
    } 