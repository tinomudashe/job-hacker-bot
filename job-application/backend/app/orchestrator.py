import os
import logging
import httpx
from typing import List, Optional
import uuid
import json

# Set Google Cloud environment variables if not already set
if not os.getenv('GOOGLE_CLOUD_PROJECT'):
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'blogai-457111'
if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    # Try different possible paths
    possible_paths = [
        './app/job-bot-credentials.json',
        'app/job-bot-credentials.json',
        '/Users/tinomudashe/job-application/backend/app/job-bot-credentials.json'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
            break

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db import get_db
from app.models_db import User, ChatMessage, Resume, Document, GeneratedCoverLetter
from app.dependencies import get_current_active_user_ws
from app.clerk import verify_token
from app.resume import ResumeData, PersonalInfo, Experience, Education
from app.job_search import JobSearchRequest, search_jobs
from app.vector_store import get_user_vector_store
from langchain.tools.retriever import create_retriever_tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.tools.render import render_text_description

# --- Configuration & Logging ---
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter()

GOOGLE_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# --- Tool Input Schemas ---


class PersonalInfoInput(BaseModel):
    """Schema for updating the personal information section of a resume."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None


class WorkExperienceInput(BaseModel):
    """Schema for adding a single work-experience entry."""
    job_title: str
    company: str
    dates: str
    description: str


class EducationInput(BaseModel):
    """Schema for adding an education entry."""
    degree: str
    institution: str
    dates: str


class SkillsInput(BaseModel):
    """Schema for overwriting the skills section with a complete list of skills."""
    skills: List[str]




# --- Master Agent Setup ---
def create_master_agent(tools: List, documents: List[str] = []):
    document_list = "\n".join(f"- {doc}" for doc in documents)
    system_message = f"""You are Job Hacker Bot, a helpful and friendly assistant specialized in job searching and career development.

You have access to the following documents and the user's personal information (name, email, etc.):
{document_list}

## Job Search Guidelines:
- **Basic Job Search**: Use search_jobs_tool for standard Google Cloud Talent API searches
- **Advanced Browser Search**: Use search_jobs_with_browser for more comprehensive results with browser automation
  * Supports LinkedIn, Indeed, Glassdoor, Monster, ZipRecruiter
  * Extracts complete job details including full descriptions and requirements
  * Better for finding fresh job postings and detailed information
  * Use when users want comprehensive job details or specific job board searches
- For general job searches, you can search with just a location (e.g., location="Poland")
- For specific roles, include both query and location (e.g., query="software engineer", location="Warsaw")
- Always provide helpful context about the jobs you find
- Format job results in a clear, readable way with proper headings and bullet points

## Cover Letter Generation Guidelines:
- When users ask for cover letters, CV letters, or application letters:
  * **URL-based generation**: Use generate_cover_letter_from_url tool (supports browser automation)
  * **Manual generation**: Use generate_cover_letter tool for provided job details
- **URL Processing Methods**:
  * Browser automation (default): More accurate extraction, handles JavaScript sites
  * Basic scraping: Faster fallback for simple sites
- **Supported Job Boards**: LinkedIn, Indeed, Glassdoor, Monster, company career pages, and more
- For URL-based generation: Simply need the job posting URL 
- For manual generation: Ask for company name, job title, and job description
- Always encourage users to provide specific skills they want to highlight (optional)
- The generated cover letter will be automatically saved to their account
- Provide PDF download links in multiple styles (modern, classic, minimal)

## Advanced Browser Automation Features:
- **Job URL Extraction**: Can browse job boards and extract multiple job URLs
- **Detailed Job Analysis**: Extracts comprehensive job information including hidden details
- **Smart Navigation**: Handles pop-ups, cookie banners, and pagination automatically
- **Multi-Board Support**: Works across different job platforms with tailored extraction strategies

## Resume PDF Generation Guidelines:
- When users ask for resume PDFs, styled resumes, or downloadable CVs, use the generate_resume_pdf tool
- Offer multiple professional styling options
- Ensure users have resume data before generating PDFs
- Guide users to add missing information if needed

## Response Format:
- Always respond in markdown format
- Use headings, lists, and other formatting elements to make responses easy to read
- Feel free to use emojis to make conversations more engaging and friendly!
- When presenting job results, organize them clearly with company names, locations, and key details
- For cover letters, present them in a clear, professional format with proper spacing

## Examples of good interactions:
- Job Search: "Find software engineer jobs in Poland" → query="software engineer", location="Poland"
- URL Cover Letter: "Generate a cover letter for this job: [LinkedIn URL]" → use generate_cover_letter_from_url tool
- Manual Cover Letter: "Generate a cover letter for a Data Analyst position at Google" → Ask for job description, then use generate_cover_letter tool
- Resume PDF: "Download my resume as PDF" → Use generate_resume_pdf tool
- General: "Show me jobs in Warsaw" → location="Warsaw" (query will be auto-generated)
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0)
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_active_user_ws),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    
    # --- Fetch User Documents & Vector Store ---
    doc_result = await db.execute(select(Document.name).where(Document.user_id == user.id))
    user_documents = doc_result.scalars().all()
    vector_store = await get_user_vector_store(user.id, db)
    retriever = vector_store.as_retriever() if vector_store else None

    # --- Helper Functions for Intelligent Extraction ---
    def _choose_extraction_method(url: str) -> str:
        """Choose the best extraction method based on URL characteristics."""
        url_lower = url.lower()
        
        # Complex sites that need browser automation
        if any(domain in url_lower for domain in ['linkedin.com', 'indeed.com', 'glassdoor.com']):
            return "browser"
        
        # Simple company career pages - use lightweight
        if any(pattern in url_lower for pattern in ['careers', 'jobs', 'apply', 'hiring']):
            return "lightweight"
        
        # Default to lightweight for unknown sites
        return "lightweight"
    
    def _is_complex_site(url: str) -> bool:
        """Determine if a site likely needs browser automation."""
        complex_domains = ['linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com', 'ziprecruiter.com']
        return any(domain in url.lower() for domain in complex_domains)
    
    async def _try_browser_extraction(url: str) -> tuple:
        """Try browser-based extraction."""
        try:
            from app.browser_job_extractor import extract_job_from_url
            
            job_extraction = await extract_job_from_url(url)
            if job_extraction:
                job_details = type('JobDetails', (), {
                    'title': job_extraction.title,
                    'company': job_extraction.company,
                    'location': job_extraction.location,
                    'description': job_extraction.description,
                    'requirements': job_extraction.requirements
                })()
                return job_details, "browser automation"
        except Exception as e:
            log.warning(f"Browser extraction failed: {e}")
        return None, ""
    
    async def _try_lightweight_extraction(url: str) -> tuple:
        """Try LangChain WebBrowser approach."""
        try:
            from app.langchain_web_extractor import extract_job_lightweight
            
            job_extraction = await extract_job_lightweight(url)
            if job_extraction:
                job_details = type('JobDetails', (), {
                    'title': job_extraction.title,
                    'company': job_extraction.company,
                    'location': job_extraction.location,
                    'description': job_extraction.description,
                    'requirements': job_extraction.requirements
                })()
                return job_details, "lightweight web extraction"
        except Exception as e:
            log.warning(f"Lightweight extraction failed: {e}")
        return None, ""
    
    async def _try_basic_extraction(url: str) -> tuple:
        """Try basic HTTP scraping."""
        try:
            from app.url_scraper import scrape_job_url
            
            job_details = await scrape_job_url(url)
            if job_details:
                return job_details, "basic HTTP scraping"
        except Exception as e:
            log.warning(f"Basic extraction failed: {e}")
        return None, ""

    # --- Helper & Tool Definitions ---
    async def get_or_create_resume():
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()

        if db_resume and db_resume.data:
            return db_resume, ResumeData(**db_resume.data)
        
        # Create default personal info with user's Clerk data if available
        default_personal_info = PersonalInfo(
            name=f"{user.first_name or ''} {user.last_name or ''}".strip() or "User",
            email=user.email if user.email else None,
            phone="",
            linkedin=user.linkedin if hasattr(user, 'linkedin') else None,
            location="",
            summary=""
        )
        
        new_resume_data = ResumeData(
            personalInfo=default_personal_info, 
            experience=[], 
            education=[], 
            skills=[]
        )
        new_db_resume = Resume(user_id=user.id, data=new_resume_data.dict())
        db.add(new_db_resume)
        await db.commit()
        await db.refresh(new_db_resume)
        return new_db_resume, new_resume_data
    
    @tool
    async def search_jobs_tool(
        query: Optional[str] = None,
        location: Optional[str] = None,
        distance_in_miles: Optional[float] = 30.0,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None
    ) -> str:
        """Search for real-time job postings. 
        
        Args:
            query: Job search terms (e.g., 'software engineer', 'python developer', 'data analyst'). 
                  If not provided, will search for general jobs in the specified location.
            location: Location to search in (e.g., 'Poland', 'Warsaw', 'Krakow'). Defaults to Poland.
            distance_in_miles: Search radius in miles. Defaults to 30.
            job_type: Type of employment (e.g., 'full-time', 'part-time', 'contract').
            experience_level: Required experience level (e.g., 'entry-level', 'mid-level', 'senior').
        
        Returns:
            JSON string containing job listings with titles, companies, locations, and descriptions.
        """
        try:
            # If no query provided, use a generic search term
            search_query = query or "jobs"
            
            # If location is provided but query is not, make it location-specific
            if not query and location:
                search_query = f"jobs in {location}"
            
            search_request = JobSearchRequest(
                query=search_query,
                location=location or "Poland",
                distance_in_miles=distance_in_miles,
                job_type=job_type,
                experience_level=experience_level
            )
            
            log.info(f"Searching jobs with query: '{search_query}', location: '{location or 'Poland'}'")
            # Use real Google Cloud Talent API if project is configured, otherwise use debug mode
            use_real_api = bool(os.getenv('GOOGLE_CLOUD_PROJECT'))
            results = await search_jobs(search_request, user.id, debug=not use_real_api)
            
            if not results:
                return f"No jobs found for '{search_query}' in {location or 'Poland'}. Try using different keywords or expanding your search criteria."
            
            job_list = [job.dict() for job in results]
            
            # Format the response nicely
            formatted_response = {
                "search_query": search_query,
                "location": location or "Poland",
                "total_jobs": len(job_list),
                "jobs": job_list
            }
            
            return json.dumps(formatted_response, indent=2)

        except Exception as e:
            log.error(f"Error in search_jobs_tool: {e}", exc_info=True)
            return f"Sorry, I encountered an error while searching for jobs: {str(e)}. Please try again with different search terms."

    @tool
    async def update_personal_information(
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        linkedin: Optional[str] = None,
        location: Optional[str] = None,
        summary: Optional[str] = None
    ) -> str:
        """Updates the personal information part of the user's resume."""
        db_resume, resume_data = await get_or_create_resume()

        input_data = PersonalInfoInput(
            name=name, email=email, phone=phone, 
            linkedin=linkedin, location=location, summary=summary
        )
        for field, value in input_data.dict(exclude_none=True).items():
            setattr(resume_data.personalInfo, field, value)

        db_resume.data = resume_data.dict()
        await db.commit()
        return "✅ Personal information updated successfully."

    @tool
    async def add_work_experience(
        job_title: str,
        company: str,
        dates: str,
        description: str
    ) -> str:
        """Appends one work-experience entry to the resume."""
        db_resume, resume_data = await get_or_create_resume()

        new_experience = Experience(
            id=str(uuid.uuid4()),
            jobTitle=job_title,
            company=company,
            dates=dates,
            description=description,
        )
        resume_data.experience.append(new_experience)

        db_resume.data = resume_data.dict()
        await db.commit()
        return "✅ Work experience added successfully."

    @tool
    async def add_education(
        degree: str,
        institution: str,
        dates: str
    ) -> str:
        """Appends one education entry to the resume."""
        db_resume, resume_data = await get_or_create_resume()

        new_education = Education(
            id=str(uuid.uuid4()),
            degree=degree,
            institution=institution,
            dates=dates,
        )
        resume_data.education.append(new_education)

        db_resume.data = resume_data.dict()
        await db.commit()
        return "✅ Education entry added successfully."

    @tool
    async def set_skills(skills: List[str]) -> str:
        """Replaces the entire skills list with the provided list of skills."""
        db_resume, resume_data = await get_or_create_resume()
        resume_data.skills = skills
        db_resume.data = resume_data.dict()
        await db.commit()
        return "✅ Skills updated successfully."

    @tool
    async def list_documents() -> str:
        """Lists the documents available to the user."""
        result = await db.execute(
            select(Document.name).where(Document.user_id == user.id)
        )
        documents = result.scalars().all()
        if not documents:
            return "No documents found."
        return "Available documents:\n" + "\n".join(f"- {doc}" for doc in documents)

    @tool
    async def read_document(filename: str) -> str:
        """Reads the content of a specified document."""
        filepath = UPLOAD_DIR / filename
        if not filepath.exists():
            return f"Error: Document '{filename}' not found."
        
        try:
            return filepath.read_text()
        except Exception as e:
            return f"Error reading document: {e}"

    @tool
    async def search_jobs_with_browser(
        query: str,
        location: str = "Remote",
        job_board: str = "linkedin",
        max_jobs: int = 5
    ) -> str:
        """Search for jobs using advanced browser automation.
        
        Args:
            query: Job search keywords (e.g., 'software engineer', 'data analyst')
            location: Location to search in (e.g., 'Poland', 'Remote', 'New York')
            job_board: Job board to search ('linkedin', 'indeed', 'glassdoor', 'monster')
            max_jobs: Maximum number of jobs to extract (default 5)
        
        Returns:
            JSON string containing detailed job information with URLs for cover letter generation
        """
        try:
            # Import here to avoid circular imports
            from app.browser_job_extractor import search_jobs_with_browser
            
            log.info(f"Starting browser job search for '{query}' on {job_board}")
            
            # Search and extract jobs using browser automation
            job_extractions = await search_jobs_with_browser(
                search_query=query,
                location=location,
                job_board=job_board,
                max_jobs=max_jobs
            )
            
            if not job_extractions:
                return f"No jobs found for '{query}' in {location} on {job_board}. Try different keywords or location."
            
            # Convert to JSON format for the agent
            jobs_data = []
            for job in job_extractions:
                jobs_data.append({
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "description": job.description[:500] + "..." if len(job.description) > 500 else job.description,
                    "requirements": job.requirements[:300] + "..." if len(job.requirements) > 300 else job.requirements,
                    "url": job.url,
                    "salary": job.salary,
                    "job_type": job.job_type,
                    "posted_date": job.posted_date
                })
            
            result = {
                "search_query": query,
                "location": location,
                "job_board": job_board,
                "total_jobs": len(jobs_data),
                "jobs": jobs_data
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            log.error(f"Error in browser job search: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while searching for jobs: {str(e)}. Please try again."

    @tool
    async def generate_cover_letter_from_url(
        job_url: str,
        user_skills: Optional[str] = None,
        extraction_method: str = "auto"
    ) -> str:
        """Generate a personalized cover letter from a job posting URL.
        
        Args:
            job_url: URL of the job posting (e.g., LinkedIn, Indeed, company website)
            user_skills: Optional specific skills to highlight
            extraction_method: Method to use ("auto", "browser", "lightweight", "basic")
                - auto: Intelligently chooses best method based on URL
                - browser: Full browser automation (most accurate, slower)
                - lightweight: LangChain WebBrowser approach (fast, good for static sites)
                - basic: Simple HTTP scraping (fastest, limited)
        
        Returns:
            A professionally written cover letter based on the job posting URL
        """
        try:
            log.info(f"Starting job extraction for: {job_url} using method: {extraction_method}")
            
            # Intelligent method selection
            if extraction_method == "auto":
                extraction_method = _choose_extraction_method(job_url)
                log.info(f"Auto-selected extraction method: {extraction_method}")
            
            job_details = None
            method_used = ""
            
            # Try extraction methods in priority order
            if extraction_method == "browser":
                job_details, method_used = await _try_browser_extraction(job_url)
            elif extraction_method == "lightweight":
                job_details, method_used = await _try_lightweight_extraction(job_url)
            elif extraction_method == "basic":
                job_details, method_used = await _try_basic_extraction(job_url)
            else:  # auto fallback chain
                # Try browser first for complex sites
                if _is_complex_site(job_url):
                    job_details, method_used = await _try_browser_extraction(job_url)
                    if not job_details:
                        job_details, method_used = await _try_lightweight_extraction(job_url)
                        if not job_details:
                            job_details, method_used = await _try_basic_extraction(job_url)
                else:
                    # Try lightweight first for simple sites
                    job_details, method_used = await _try_lightweight_extraction(job_url)
                    if not job_details:
                        job_details, method_used = await _try_browser_extraction(job_url)
                        if not job_details:
                            job_details, method_used = await _try_basic_extraction(job_url)
            
            if not job_details:
                return f"❌ Sorry, I couldn't extract job details from that URL using any available method. Please check the URL and try again, or provide the job details manually."
            
            log.info(f"Successfully extracted job using {method_used}: {job_details.title} at {job_details.company}")
            
            # Combine description and requirements for full job context
            full_job_description = f"{job_details.description}\n\nRequirements: {job_details.requirements}"
            
            # Use the existing cover letter generation logic by calling it directly
            # Get user's name from Clerk profile
            user_name = user.first_name or "User"
            if user.last_name:
                user_name = f"{user.first_name} {user.last_name}"
            
            # Get user information from vector store if available
            user_context = ""
            if vector_store:
                try:
                    # Search for user's resume, experience, and skills information
                    search_queries = [
                        "resume experience skills",
                        "work experience background",
                        "education qualifications",
                        "technical skills programming"
                    ]
                    
                    context_parts = []
                    for query in search_queries:
                        docs = await vector_store.asimilarity_search(query, k=3)
                        if docs:
                            for doc in docs:
                                if doc.page_content not in context_parts:
                                    context_parts.append(doc.page_content)
                    
                    if context_parts:
                        user_context = "\n".join(context_parts[:5])  # Limit to top 5 relevant pieces
                except Exception as ve:
                    log.warning(f"Could not retrieve vector store data: {ve}")
            
            # Use provided skills or create a general description
            if not user_skills:
                user_skills = "Various professional skills and experience as detailed in my background"
            
            # Create the cover letter generation prompt with vector store context
            prompt = ChatPromptTemplate.from_template(
                "You are an expert career coach. Write a professional and compelling cover letter.\n\n"
                "**Candidate Information:**\n"
                "Name: {user_name}\n"
                "Skills/Experience: {user_skills}\n\n"
                "**Additional Background Context:**\n"
                "{user_context}\n\n"
                "**Job Details:**\n"
                "Company: {company_name}\n"
                "Position: {job_title}\n"
                "Job Description: {job_description}\n\n"
                "Instructions:\n"
                "- Write a professional cover letter tailored to this specific role\n"
                "- Use the background context to highlight relevant experience and skills\n"
                "- Make it engaging and specific to the job requirements\n"
                "- Do not include placeholders for contact information\n"
                "- Keep it concise but impactful (3-4 paragraphs)\n"
                "- Show enthusiasm for the role and company"
            )
            
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)
            chain = prompt | llm
            
            # Generate the cover letter
            result = await chain.ainvoke({
                "user_name": user_name,
                "user_skills": user_skills,
                "user_context": user_context or "No additional background information available.",
                "company_name": job_details.company,
                "job_title": job_details.title,
                "job_description": full_job_description,
            })
            
            cover_letter_text = result.content
            
            # Save the cover letter to database
            new_cover_letter = GeneratedCoverLetter(
                id=str(uuid.uuid4()),
                user_id=user.id,
                content=cover_letter_text
            )
            db.add(new_cover_letter)
            await db.commit()
            
            return f"""## 📄 Cover Letter for {job_details.title} at {job_details.company}

{cover_letter_text}

---

✅ **Cover letter generated from URL and saved successfully!** 

**📊 Extracted Job Details:**
- **Company**: {job_details.company}
- **Position**: {job_details.title}
- **Location**: {job_details.location}

**Download Options:**
- 📋 Copy the text above for your application
- 📄 [Download as PDF (Modern Style)](/api/pdf/generate?content_type=cover_letter&content_id={new_cover_letter.id}&style=modern&company_name={job_details.company}&job_title={job_details.title})
- 📄 [Download as PDF (Classic Style)](/api/pdf/generate?content_type=cover_letter&content_id={new_cover_letter.id}&style=classic&company_name={job_details.company}&job_title={job_details.title})
- 📄 [Download as PDF (Minimal Style)](/api/pdf/generate?content_type=cover_letter&content_id={new_cover_letter.id}&style=minimal&company_name={job_details.company}&job_title={job_details.title})

*Click any download link to get a professionally formatted PDF version of your cover letter.*"""
            
        except Exception as e:
            log.error(f"Error generating cover letter from URL: {e}", exc_info=True)
            return f"❌ Sorry, I couldn't extract the job details from that URL: {str(e)}. Please check the URL and try again, or provide the job details manually."

    @tool
    async def generate_cover_letter(
        company_name: str,
        job_title: str,
        job_description: str,
        user_skills: Optional[str] = None
    ) -> str:
        """Generate a personalized cover letter for a specific job application.
        
        Args:
            company_name: Name of the company you're applying to
            job_title: Title of the job position
            job_description: Full job description or key requirements
            user_skills: Optional specific skills to highlight (if not provided, will use vector store data)
        
        Returns:
            A professionally written cover letter tailored to the job
        """
        try:
            # Get user's name from Clerk profile
            user_name = user.first_name or "User"
            if user.last_name:
                user_name = f"{user.first_name} {user.last_name}"
            
            # Get user information from vector store if available
            user_context = ""
            if vector_store:
                try:
                    # Search for user's resume, experience, and skills information
                    search_queries = [
                        "resume experience skills",
                        "work experience background",
                        "education qualifications",
                        "technical skills programming"
                    ]
                    
                    context_parts = []
                    for query in search_queries:
                        docs = await vector_store.asimilarity_search(query, k=3)
                        if docs:
                            for doc in docs:
                                if doc.page_content not in context_parts:
                                    context_parts.append(doc.page_content)
                    
                    if context_parts:
                        user_context = "\n".join(context_parts[:5])  # Limit to top 5 relevant pieces
                except Exception as ve:
                    log.warning(f"Could not retrieve vector store data: {ve}")
            
            # Use provided skills or create a general description
            if not user_skills:
                user_skills = "Various professional skills and experience as detailed in my background"
            
            # Create the cover letter generation prompt with vector store context
            prompt = ChatPromptTemplate.from_template(
                "You are an expert career coach. Write a professional and compelling cover letter.\n\n"
                "**Candidate Information:**\n"
                "Name: {user_name}\n"
                "Skills/Experience: {user_skills}\n\n"
                "**Additional Background Context:**\n"
                "{user_context}\n\n"
                "**Job Details:**\n"
                "Company: {company_name}\n"
                "Position: {job_title}\n"
                "Job Description: {job_description}\n\n"
                "Instructions:\n"
                "- Write a professional cover letter tailored to this specific role\n"
                "- Use the background context to highlight relevant experience and skills\n"
                "- Make it engaging and specific to the job requirements\n"
                "- Do not include placeholders for contact information\n"
                "- Keep it concise but impactful (3-4 paragraphs)\n"
                "- Show enthusiasm for the role and company"
            )
            
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)
            chain = prompt | llm
            
            # Generate the cover letter
            result = await chain.ainvoke({
                "user_name": user_name,
                "user_skills": user_skills,
                "user_context": user_context or "No additional background information available.",
                "company_name": company_name,
                "job_title": job_title,
                "job_description": job_description,
            })
            
            cover_letter_text = result.content
            
            # Save the cover letter to database
            new_cover_letter = GeneratedCoverLetter(
                id=str(uuid.uuid4()),
                user_id=user.id,
                content=cover_letter_text
            )
            db.add(new_cover_letter)
            await db.commit()
            
            # Create download links
            pdf_download_link = f"/api/pdf/generate"
            
            return f"""## 📄 Cover Letter for {job_title} at {company_name}

{cover_letter_text}

---

✅ **Cover letter generated and saved successfully!** 

**Download Options:**
- 📋 Copy the text above for your application
- 📄 [Download as PDF (Modern Style)](/api/pdf/generate?content_type=cover_letter&content_id={new_cover_letter.id}&style=modern&company_name={company_name}&job_title={job_title})
- 📄 [Download as PDF (Classic Style)](/api/pdf/generate?content_type=cover_letter&content_id={new_cover_letter.id}&style=classic&company_name={company_name}&job_title={job_title})
- 📄 [Download as PDF (Minimal Style)](/api/pdf/generate?content_type=cover_letter&content_id={new_cover_letter.id}&style=minimal&company_name={company_name}&job_title={job_title})

*Click any download link to get a professionally formatted PDF version of your cover letter.*"""
            
        except Exception as e:
            log.error(f"Error generating cover letter: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while generating your cover letter: {str(e)}. Please try again with the job details."

    @tool
    async def generate_resume_pdf(
        style: str = "modern"
    ) -> str:
        """Generate a professionally styled PDF version of your resume.
        
        Args:
            style: PDF style theme - "modern", "classic", or "minimal"
        
        Returns:
            Download links for the resume PDF in different styles
        """
        try:
            # Check if user has resume data
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            db_resume = result.scalars().first()
            
            if not db_resume:
                return "❌ No resume data found. Please add your personal information, experience, and skills first using the resume tools."
            
            return f"""## 📄 Resume PDF Generation

✅ **Your resume is ready for download!**

**Download Options:**
- 📄 [Download Resume (Modern Style)](/api/pdf/generate?content_type=resume&style=modern)
- 📄 [Download Resume (Classic Style)](/api/pdf/generate?content_type=resume&style=classic)  
- 📄 [Download Resume (Minimal Style)](/api/pdf/generate?content_type=resume&style=minimal)

**Style Previews:**
- **Modern**: Clean design with blue accents and modern typography
- **Classic**: Traditional format with serif fonts and formal layout
- **Minimal**: Simple, clean design with plenty of white space

*Click any download link to get a professionally formatted PDF version of your resume.*"""
            
        except Exception as e:
            log.error(f"Error generating resume PDF: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while preparing your resume PDF: {str(e)}. Please try again."

    tools = [
        search_jobs_tool,
        update_personal_information,
        add_work_experience,
        add_education,
        set_skills,
        list_documents,
        read_document,
        generate_cover_letter_from_url,
        generate_cover_letter,
        generate_resume_pdf,
    ]
    
    if retriever:
        retriever_tool = create_retriever_tool(
            retriever,
            "document_retriever",
            "Searches and returns information from the user's documents."
        )
        tools.append(retriever_tool)

    master_agent = create_master_agent(tools, user_documents)

    # --- Chat History & Main Loop ---
    history_records = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
        .where(ChatMessage.page_id.is_(None))  # Only load messages without page context for now
        .order_by(ChatMessage.created_at)
    )
    
    current_chat_history = []
    for r in history_records.scalars().all():
        try:
            content = json.loads(r.message)
        except (json.JSONDecodeError, TypeError):
            content = r.message
        
        if r.is_user_message:
            current_chat_history.append(HumanMessage(id=r.id, content=content if isinstance(content, str) else json.dumps(content)))
        else:
            current_chat_history.append(AIMessage(id=r.id, content=content if isinstance(content, str) else json.dumps(content)))

    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse message data to check for page context
            message_content = data
            page_id = None
            
            try:
                message_data = json.loads(data)
                
                if message_data.get("type") == "clear_context":
                    current_chat_history = []
                    log.info(f"Chat context cleared for user {user.id}")
                    continue
                elif message_data.get("type") == "regenerate":
                    if len(current_chat_history) > 1:
                        # Remove the last AI message
                        current_chat_history.pop()
                        # Get the last human message
                        last_human_message = current_chat_history[-1].content
                        
                        response = await master_agent.ainvoke({
                            "input": last_human_message,
                            "chat_history": current_chat_history[:-1],
                        })
                        result = response.get("output", "I'm sorry, I encountered an issue.")
                        await websocket.send_text(result)
                        
                        # Save AI message with page context
                        ai_message_id = str(uuid.uuid4())
                        db.add(ChatMessage(
                            id=ai_message_id,
                            user_id=user.id,
                            page_id=page_id,
                            message=result,
                            is_user_message=False
                        ))
                        await db.commit()
                        current_chat_history.append(AIMessage(id=ai_message_id, content=result))
                    continue
                elif "content" in message_data:
                    # New format with page context
                    message_content = message_data["content"]
                    page_id = message_data.get("page_id")
                    
                    # If we have a page_id, load the conversation history for that page
                    if page_id and not current_chat_history:
                        page_history = await db.execute(
                            select(ChatMessage)
                            .where(ChatMessage.user_id == user.id)
                            .where(ChatMessage.page_id == page_id)
                            .order_by(ChatMessage.created_at)
                        )
                        
                        current_chat_history = []
                        for r in page_history.scalars().all():
                            try:
                                content = json.loads(r.message)
                            except (json.JSONDecodeError, TypeError):
                                content = r.message
                            
                            if r.is_user_message:
                                current_chat_history.append(HumanMessage(id=r.id, content=content if isinstance(content, str) else json.dumps(content)))
                            else:
                                current_chat_history.append(AIMessage(id=r.id, content=content if isinstance(content, str) else json.dumps(content)))
                
            except json.JSONDecodeError:
                # It's a regular text message (legacy format)
                pass
            
            # Save user message with page context
            user_message_id = str(uuid.uuid4())
            db.add(ChatMessage(
                id=user_message_id,
                user_id=user.id,
                page_id=page_id,
                message=message_content,
                is_user_message=True
            ))
            await db.commit()
            
            current_chat_history.append(HumanMessage(id=user_message_id, content=message_content))

            # Pass message to our agent
            response = await master_agent.ainvoke({
                "input": message_content,
                "chat_history": current_chat_history,
            })
            result = response.get("output", "I'm sorry, I encountered an issue.")
            
            await websocket.send_text(result)
            
            # Save AI message with page context
            ai_message_id = str(uuid.uuid4())
            db.add(ChatMessage(
                id=ai_message_id,
                user_id=user.id,
                page_id=page_id,
                message=result,
                is_user_message=False
            ))
            await db.commit()
            
            current_chat_history.append(AIMessage(id=ai_message_id, content=result))
            
    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        log.error(f"WebSocket error for user {user.id}: {e}")
        await websocket.send_text(f"An error occurred: {str(e)}") 