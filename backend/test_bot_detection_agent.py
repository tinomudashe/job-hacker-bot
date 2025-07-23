import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Controller
from browser_use.browser import BrowserProfile, BrowserSession
from browser_use.agent.memory import MemoryConfig
import io
import docx
from pypdf import PdfReader
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

CV = Path.cwd() / '/Users/tinomudashe/job-application/Resume.pdf'
if not CV.exists():
    raise FileNotFoundError(f'You need to set the path to your cv file in the CV variable. CV file not found at {CV}')

controller = Controller()

@controller.action('Read my cv for context to fill forms')
def read_cv():
    pdf = PdfReader(CV)
    text = ''
    for page in pdf.pages:
        text += page.extract_text() or ''
    return text

@controller.action(
    'Upload cv to element - call this function to upload if element is not found, try with different index of the same upload element',
)
async def upload_cv(index: int, browser_session: BrowserSession):
    path = str(CV.resolve())

    # Check if file exists
    if not os.path.exists(path):
        return f"🚫 File does not exist at path: {path}"

    # Locate the file upload DOM element by index
    file_upload_dom_el = await browser_session.find_file_upload_element_by_index(index)
    if file_upload_dom_el is None:
        return f"⚠️ No file upload element DOM found at index {index}"

    # Convert DOM to a Playwright Locator
    file_upload_el = await browser_session.get_locate_element(file_upload_dom_el)
    if file_upload_el is None:
        return f"⚠️ No locator created for element at index {index}"

    try:
        # Attempt to upload file
        await file_upload_el.set_input_files(path)
        return f"✅ Successfully uploaded file \"{path}\" to index {index}"
    except Exception as e:
        return f"❌ Failed to upload file to index {index}: {str(e)}"

browser_session = BrowserSession(
    browser_profile=BrowserProfile(
        executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        disable_security=True,
        user_data_dir='~/.config/browseruse/profiles/default',
    )
)

async def main():
    model = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
    planner = ChatGoogleGenerativeAI(model='gemini-2.0-flash')

    # Fill in your details here
    first_name = "Jan"
    last_name = "Kowalski"
    email = "jan.kowalski@example.com"
    phone = "123456789"

  

    # Updated task with instructions to fill in one element at a time
    task = (
         "Go to https://openchip.factorialhr.com/job_posting/junior-devops-242599?src=LKDN"
        "Fill in the application form with the following details: "
        f"Imię: {first_name}, Nazwisko: {last_name}, Email: {email}, Numer telefonu: +48123456789. "
        "Call 'read_cv' to get your CV content if any questions in the form require professional background or work experience. "
        "Only call 'upload_cv' if the CV file is explicitly required or there's a file input for uploading a resume. "
        "Try upload index 0 first, increment if needed. "
        "Accept all required consents and submit the form. "
        "Return a summary of the submission result."
    )

    agent = Agent(task=task, 
                  llm=model, 
                  controller=controller,
                  enable_memory=True, 
                  browser_session=browser_session,
                  planner_llm=planner,
                  use_vision_for_planner=True,
                  is_planner_reasoning=True,
                  memory_config = MemoryConfig(
                        llm_instance=model,  # Pass the LLM instance for memory
                        agent_id="my_agent",
                        memory_interval=15,  # Summarize every 15 steps
                        embedder_provider="gemini",
                        embedder_model="models/text-embedding-004",
                        vector_store_provider="faiss",
                        vector_store_collection_name="my_browser_use_memories"
                    )
                  )
    await agent.run()

if __name__ == '__main__':
    asyncio.run(main())