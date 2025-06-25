import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Controller, Browser
from browser_use.agent.views import ActionResult, AgentHistory
from pydantic import BaseModel, HttpUrl, ValidationError
import logging
import json

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid

from app.db import get_db, async_session_maker
from app.models_db import Application, User
from app.dependencies import get_current_active_user
from app.usage import UsageManager

load_dotenv()

# --- Configuration ---
CV_PATH = Path(os.getenv("CV_PATH", "/Users/tinomudashe/job-application/Resume.pdf"))
# CHROME_USER_DATA_DIR = os.getenv("CHROME_USER_DATA_DIR", "~/.config/browseruse/profiles/default")
BROWSER_EXECUTABLE_PATH = os.getenv("BROWSER_EXECUTABLE_PATH") or "/ms-playwright/chromium/chrome-linux/chrome"  # Default to Chrome in Playwright Docker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ApplicationResult(BaseModel):
    job_title: str
    company_name: str

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
    user_details: dict, 
    db_user_id: str, 
):
    """The core function that runs the browser agent and saves the result."""
    controller = Controller(output_model=ApplicationResult)

    @controller.action('Read my cv for context to fill forms')
    def read_cv():
        from PyPDF2 import PdfReader
        if not CV_PATH.exists():
            return f"CV file not found at {CV_PATH}"
        pdf = PdfReader(str(CV_PATH))
        text = "".join(page.extract_text() or "" for page in pdf.pages)
        return text

    @controller.action('Upload cv to element')
    async def upload_cv(index: int, browser_session):
        path = str(CV_PATH.resolve())
        if not os.path.exists(path):
            return f"🚫 File does not exist at path: {path}"
        file_upload_dom_el = await browser_session.find_file_upload_element_by_index(index)
        if not file_upload_dom_el:
            return f"⚠️ No file upload element DOM found at index {index}"
        file_upload_el = await browser_session.get_locate_element(file_upload_dom_el)
        if not file_upload_el:
            return f"⚠️ No locator created for element at index {index}"
        try:
            await file_upload_el.set_input_files(path)
            return f"✅ Successfully uploaded file \"{path}\" to index {index}"
        except Exception as e:
            return f"❌ Failed to upload file to index {index}: {str(e)}"

    @controller.action('Ask human for help with a question')
    def ask_human(question: str) -> ActionResult:
        answer = input(f'Agent needs help: {question}\nYour answer > ')
        return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
    
    browser = Browser(
        wss_url="ws://127.0.0.1:3000/",
        incognito=True,
        # We don't need keep_alive as the agent will manage the session
    )

    task_prompt = (
        f"You are an expert at applying for jobs online. Your goal is to apply for the job at {job_url} using the provided user details.\n"
        f"Your process should be as follows:\n"
        f"1. Navigate to the job URL and wait for the page to load. If the page does not load or returns an error, stop and report the issue.\n"
        f"2. Immediately upon page load, scan for and interact with any pop-ups, cookie banners, or intrusive elements (e.g., 'Dismiss', 'Accept', 'Close' buttons). After dismissing, re-evaluate all interactive elements on the page to get updated indices and attributes. This re-evaluation is critical for subsequent actions.\n"
        f"3. Locate the main job application form. If it's behind an 'Apply' or 'Start Application' button, click it to reveal the form. Re-evaluate elements after revealing the form.\n"
        f"4. Identify all input fields and interactive elements on the form that require user data. Prioritize identification by using their visible labels (e.g., 'First Name:', 'Email Address:'), 'name' attributes, 'data-qa' attributes, or other strong semantic identifiers. Only use numerical indices if no other reliable identifier is found, and if so, explicitly mention that the index was used and why, and be prepared to re-evaluate if it fails.\n"
        f"5. Fill in the form fields with the provided user details. For each field:\n"
        f"   - First try to find the field by its label text or semantic identifier\n"
        f"   - If not found, try common attribute patterns (name, id, aria-label)\n"
        f"   - Only use index-based selection as a last resort\n"
        f"   - After each input, verify the field contains the entered value\n"
        f"6. If a CV upload is required:\n"
        f"   - Identify the file upload element using the same priority of identifiers\n"
        f"   - Use the 'Upload cv to element' action with the appropriate index\n"
        f"   - Verify the upload was successful before proceeding\n"
        f"7. Before submission:\n"
        f"   - Review all required fields are filled\n"
        f"   - Check for any validation errors\n"
        f"   - Ensure all uploaded documents are properly attached\n"
        f"8. Submit the form and wait for the response:\n"
        f"   - Look for the submit button using the same identifier priority\n"
        f"   - Click the submit button\n"
        f"   - Wait for the page to update or redirect\n"
        f"9. After submission, thoroughly scan the page for a success message (e.g., 'Application Submitted!', 'Thank You!') or any clear indication that the application was successful. Extract the job title and company name from the success page or a suitable post-submission element. If a clear success message is not found, use contextual information on the page to determine success (e.g., redirection to a confirmation page, removal of the form, etc.).\n"
        f"10. If at any point you encounter errors (e.g., 'element not found', 'failed to input text', even after re-evaluation), or cannot make tangible progress towards filling the form or submitting after several attempts, use 'Ask human for help with a question' for assistance. When asking, clearly state the exact problem, the last successful action, and what specific element or step prevents further progress (mentioning if an index was used and failed, and if semantic targeting was attempted). If assistance doesn't immediately resolve the issue, stop and report the problem."
        f"11. Finally, call the 'done' function with 'success=True' if the application was definitively submitted and the job details extracted, or 'success=False' otherwise, along with the extracted job title and company name. If the application failed due to missing required information (e.g., human could not provide it), ensure 'success=False' is returned.\n"
    )
    
 
    memory_config = {
        "llm_instance": llm,
        "agent_id": f"job_applicant_agent_{db_user_id}",
        "embedder_provider": "gemini",
        "embedder_model": "models/text-embedding-004",
        "vector_store_provider": "faiss",
        "vector_store_collection_name": f"job_application_memories_{db_user_id}"
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
            logger.info(f"Starting browser automation for user {db_user_id} on: {job_url} (Attempt {attempt})")
            result = await browser_agent.run()
            logger.info(f"Browser automation finished for user {db_user_id}. Result: {result}")
        finally:
            logger.info(f"Browser session for user {db_user_id} completed for attempt {attempt}.")

        job_title, company_name = _parse_agent_result(result)
        is_success = _get_final_done_status(result)
        if is_success:
            summary = f"Success on attempt {attempt}."
            break
        else:
            # Try to extract a summary error from the result
            if hasattr(result, 'history') and result.history:
                last_action = result.history[-1]
                if hasattr(last_action, 'error') and last_action.error:
                    last_error = last_action.error
            summary = f"Failed attempt {attempt}. {last_error or 'Unknown error.'}"
    else:
        # If all attempts failed
        job_title, company_name = "Unknown", "Unknown"
        summary = f"Failed after {max_attempts} attempts. {last_error or 'Unknown error.'}"
        is_success = False

    # --- Save Application to DB ---
    async with async_session_maker() as db:
        new_application = Application(
            id=str(uuid.uuid4()),
            user_id=db_user_id,
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
        logger.info(f"Successfully saved application for {job_title} at {company_name}.")

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
    first_name: str
    last_name: str
    email: str
    phone: str

@router.post("/agent/apply", status_code=202)
async def apply_for_job(
    request: ApplicationRequest,
    background_tasks: BackgroundTasks,
    db_user: User = Depends(get_current_active_user)
):
    """
    Triggers a background task to apply for a job using the browser agent.
    """
    if not CV_PATH.exists():
        raise HTTPException(status_code=500, detail=f"CV file not found at {CV_PATH}")

    # Use request data, but fill in from db_user if missing
    user_details = request.dict(include={'first_name', 'last_name', 'email', 'phone'})
    if not user_details.get('first_name'):
        user_details['first_name'] = getattr(db_user, 'first_name', None) or (db_user.name.split()[0] if db_user.name else None)
    if not user_details.get('last_name'):
        user_details['last_name'] = getattr(db_user, 'last_name', None) or (db_user.name.split()[1] if db_user.name and len(db_user.name.split()) > 1 else None)
    if not user_details.get('email'):
        user_details['email'] = db_user.email
    if not user_details.get('phone'):
        user_details['phone'] = getattr(db_user, 'phone', None)

    async def agent_task():
        result = await run_application_agent(request.job_url, user_details, db_user.id)
        job_title, company_name = _parse_agent_result(result)
        is_success = _get_final_done_status(result)
        status = "applied" if is_success else "failed"
        async with async_session_maker() as db:
            new_application = Application(
                id=str(uuid.uuid4()),
                user_id=db_user.id,
                job_title=job_title,
                company_name=company_name,
                job_url=str(request.job_url),
                status=status,
                notes=f"Applied via agent. Result: {result}",
                date_applied=datetime.now(timezone.utc),
                success=is_success
            )
            db.add(new_application)
            await db.commit()
        if is_success:
            # Only deduct usage if successful
            _ = await UsageManager(feature="applications").__call__()

    background_tasks.add_task(agent_task)
    return {"message": "Job application task has been started in the background."} 