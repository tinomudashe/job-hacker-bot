import os
import logging
import httpx
from typing import List, Optional
import uuid
import json
from pathlib import Path
from datetime import datetime

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
from app.enhanced_memory import EnhancedMemoryManager

# --- Configuration & Logging ---
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter()

# Upload directory configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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
def create_master_agent(tools: List, documents: List[str] = [], enhanced_system_prompt: str = None):
    if enhanced_system_prompt:
        # Use enhanced system prompt with user learning context
        system_message = enhanced_system_prompt + """

## 🚀 CV & Career Development Assistance Priority:
- **Be Proactive**: Actively help users improve their CVs and advance their careers
- **Suggest Helpful Tools**: When users mention career goals, job searching, or CV issues, offer relevant guidance tools
- **Complete Career Support**: You have comprehensive tools to help with every aspect of career development

## 📚 Comprehensive CV & Career Tools Available:
### CV Creation & Enhancement:
- **get_cv_best_practices**: Provide industry-specific CV guidelines and best practices
- **analyze_skills_gap**: Analyze what skills users need for their target roles
- **get_ats_optimization_tips**: Help optimize CVs for Applicant Tracking Systems
- **refine_cv_for_role**: Enhance existing CVs for specific positions
- **generate_tailored_resume**: Create complete resumes tailored to job descriptions
- **create_resume_from_scratch**: Build new CVs based on career goals
- **enhance_resume_section**: Improve specific CV sections

### Career Development:
- **get_interview_preparation_guide**: Comprehensive interview prep for specific roles
- **get_salary_negotiation_advice**: Strategic guidance for compensation discussions
- **create_career_development_plan**: Long-term career planning with actionable steps

### When to Suggest CV Help:
- **New Users**: Offer CV assessment and improvement suggestions
- **Job Search Mentions**: When users search for jobs, suggest CV optimization
- **Career Questions**: For any career-related queries, offer comprehensive guidance
- **Skills Discussions**: Suggest skills gap analysis when users mention lacking abilities
- **Interview Mentions**: Immediately offer interview preparation tools
- **Salary Questions**: Provide negotiation guidance and market insights

## 💡 Proactive Assistance Examples:
- User searches jobs → "I found these opportunities! Would you like me to analyze your CV against these job requirements or help optimize it for ATS systems?"
- User mentions career goals → "I can create a comprehensive career development plan to help you reach that goal. Would you also like me to analyze the skills gap?"
- User asks about experience → "Based on your background, I can provide CV best practices for your industry or enhance specific sections of your resume."
- User mentions interviews → "I can create a personalized interview preparation guide for you! What role are you interviewing for?"

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

## Resume Generation & Enhancement Guidelines:
- **IMPORTANT**: For CV/Resume refinement, enhancement, or generation requests, ALWAYS use these modern tools first:
  * **refine_cv_for_role**: PRIMARY TOOL for CV refinement requests - use this for "refine CV", "enhance resume", etc.
  * **generate_tailored_resume**: For creating complete resumes tailored to specific jobs
  * **create_resume_from_scratch**: For building new resumes based on career goals  
  * **enhance_resume_section**: For improving specific resume sections
- **NEVER use the old RAG /rag/assist endpoint** for resume generation - it's deprecated and causes delays
- **Complete Resume Generation**: Use generate_tailored_resume for creating full resumes from job descriptions
- **Section Enhancement**: Use enhance_resume_section to improve specific parts (summary, experience, skills, education)
- **From Scratch Creation**: Use create_resume_from_scratch for building new resumes based on career goals
- **PDF Downloads**: Use show_resume_download_options for downloading existing resumes with styling options
- **Job-Specific Tailoring**: Always encourage users to provide job descriptions for better targeting
- **Progressive Building**: Help users build resumes step-by-step, section by section if needed
- **Quality Enhancement**: Suggest improvements and optimizations for ATS compatibility
- Be proactive: when users complete their resume, offer download options automatically

## CV Refinement Specific Instructions:
- When users ask to "refine CV", "enhance resume", "improve CV for AI roles", etc.:
  * **ALWAYS use refine_cv_for_role tool FIRST** - this is the primary refinement tool
  * Ask for specific job description if available for better tailoring
  * Explain the modern tools create better results than the old system
- Examples:
  * "Refine my CV for AI Engineering roles" → use refine_cv_for_role(target_role="AI Engineering")
  * "Enhance my CV for software jobs" → use refine_cv_for_role(target_role="Software Development")
  * "Improve my resume for data science" → use refine_cv_for_role(target_role="Data Science")
  * "Update my CV" → use refine_cv_for_role(target_role="[ask user for target role]")

## Download Instructions for Generated Content:
- **IMPORTANT**: When you generate resumes or CVs using generate_tailored_resume or create_resume_from_scratch:
  * Tell users that "A download button will appear on this message"
  * Explain they can click the download button to access PDF options
  * Mention they can choose from Modern, Classic, or Minimal styles
  * Let them know they can edit content before downloading
  * Inform them about preview functionality
- **User Education**: Always explain how to use the download feature:
  * "Look for the download button (📥) that appears on messages with generated content"
  * "Click it to open the PDF generation dialog with style options"
  * "You can edit the content, preview it, and download in your preferred style"

## Document Access Guidelines:
- **IMPORTANT**: When users ask about their CV, resume, experience, skills, or any document content:
  * **ALWAYS use enhanced_document_search tool first** to search their uploaded documents
  * **NEVER say you cannot access files** - you have document search capabilities
  * Examples: "from my cv what's my experience" → use enhanced_document_search("experience")
  * Examples: "what skills do I have" → use enhanced_document_search("skills")
  * Examples: "summarize my resume" → use enhanced_document_search("resume summary")
- **Document Analysis**: Use analyze_specific_document for detailed analysis of a particular document
- **Document Insights**: Use get_document_insights for comprehensive overview of all documents
- **Vector Store**: You have access to all uploaded documents through the document_retriever tool
- **Never tell users to copy/paste their CV content** - you can access it directly through search tools

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
- Resume PDF: "Download my resume as PDF" → Use show_resume_download_options tool
- **Tailored Resume**: "Create a resume for a Software Engineer position at Google" → use generate_tailored_resume tool
- **Resume from Scratch**: "Build me a resume for Product Manager roles" → use create_resume_from_scratch tool
- **Section Enhancement**: "Improve my professional summary" → use enhance_resume_section tool
- General: "Show me jobs in Warsaw" → location="Warsaw" (query will be auto-generated)
- **Document Questions**: "What's my experience?" → use enhanced_document_search("experience")
- **CV Summary**: "Summarize my CV" → use enhanced_document_search("resume summary")
- **Skills Query**: "What skills do I have?" → use enhanced_document_search("skills")
"""
    else:
        # Fallback to basic system prompt
        document_list = "\n".join(f"- {doc}" for doc in documents)
        system_message = f"""You are Job Hacker Bot, a helpful and friendly assistant specialized in job searching and career development.

## 🚀 Your Mission: Comprehensive Career Support
You are an expert career coach and CV specialist. Your primary goal is to help users:
- **Create outstanding CVs and resumes**
- **Develop successful career strategies**
- **Navigate job searches effectively**
- **Prepare for interviews and negotiations**
- **Advance in their chosen fields**

**Be proactive in offering help!** When users mention careers, jobs, or professional development, suggest relevant guidance and tools.

You have access to the following documents and the user's personal information (name, email, etc.):
{document_list}

## 📚 Your Comprehensive Career Toolkit:
### CV & Resume Excellence:
- **get_cv_best_practices**: Industry-specific CV guidelines and best practices
- **analyze_skills_gap**: Identify skills needed for target roles with learning roadmap
- **get_ats_optimization_tips**: Optimize CVs for Applicant Tracking Systems
- **refine_cv_for_role**: Enhance existing CVs for specific positions  
- **generate_tailored_resume**: Create complete resumes tailored to job descriptions
- **create_resume_from_scratch**: Build new CVs based on career goals
- **enhance_resume_section**: Improve specific CV sections (summary, experience, skills)

### Career Development:
- **get_interview_preparation_guide**: Comprehensive interview prep for specific roles
- **get_salary_negotiation_advice**: Strategic guidance for compensation discussions  
- **create_career_development_plan**: Long-term career planning with actionable steps

### Proactive Assistance Strategy:
- **New Conversations**: Offer CV assessment and career guidance
- **Job Search Queries**: Suggest CV optimization for found opportunities
- **Career Discussions**: Provide comprehensive career development support
- **Skills Questions**: Recommend skills gap analysis and learning plans
- **Interview Mentions**: Immediately offer tailored interview preparation

## Document Access Guidelines:
- **IMPORTANT**: When users ask about their CV, resume, experience, skills, or any document content:
  * **ALWAYS use enhanced_document_search tool first** to search their uploaded documents
  * **NEVER say you cannot access files** - you have document search capabilities
  * Examples: "from my cv what's my experience" → use enhanced_document_search("experience")
  * Examples: "what skills do I have" → use enhanced_document_search("skills")
  * Examples: "summarize my resume" → use enhanced_document_search("resume summary")
- **Document Analysis**: Use analyze_specific_document for detailed analysis of a particular document
- **Document Insights**: Use get_document_insights for comprehensive overview of all documents
- **Vector Store**: You have access to all uploaded documents through the document_retriever tool
- **Never tell users to copy/paste their CV content** - you can access it directly through search tools

## Resume Generation & CV Refinement Guidelines:
- **IMPORTANT**: For CV/Resume refinement, enhancement, or generation requests, ALWAYS use these modern tools:
  * **refine_cv_for_role**: PRIMARY TOOL for CV refinement - use for "refine CV", "enhance resume", etc.
  * **generate_tailored_resume**: For creating complete resumes tailored to specific jobs
  * **create_resume_from_scratch**: For building new resumes based on career goals
  * **enhance_resume_section**: For improving specific resume sections
- **NEVER use old RAG /rag/assist endpoint** - it's deprecated and causes delays
- **CV Refinement Examples**:
  * "Refine my CV for AI Engineering roles" → use refine_cv_for_role(target_role="AI Engineering")
  * "Enhance my resume" → use refine_cv_for_role(target_role="[ask user]")
  * "Improve my CV for tech jobs" → use refine_cv_for_role(target_role="Technology")

## Job Search Guidelines:
- **Basic Job Search**: Use search_jobs_tool for standard Google Cloud Talent API searches
- **Advanced Browser Search**: Use search_jobs_with_browser for more comprehensive results with browser automation
- For general job searches, you can search with just a location (e.g., location="Poland")
- For specific roles, include both query and location (e.g., query="software engineer", location="Warsaw")
- Always provide helpful context about the jobs you find

## Cover Letter Generation Guidelines:
- When users ask for cover letters, CV letters, or application letters:
  * **URL-based generation**: Use generate_cover_letter_from_url tool
  * **Manual generation**: Use generate_cover_letter tool for provided job details
- Always encourage users to provide specific skills they want to highlight (optional)

## Response Format:
- Always respond in markdown format
- Use headings, lists, and other formatting elements to make responses easy to read
- Feel free to use emojis to make conversations more engaging and friendly!
- **Be enthusiastic about helping with career development!**

## 💡 Example Proactive Responses:
- User: "I'm looking for jobs" → "I'd be happy to help! I can search for jobs and also help optimize your CV for those opportunities. What type of role are you targeting?"
- User: "I have an interview next week" → "Congratulations! I can create a comprehensive interview preparation guide tailored to your role. What position are you interviewing for?"
- User: "I want to improve my career" → "Perfect! I can help you create a complete career development plan, analyze skills gaps, and enhance your CV. What's your target role or industry?"
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
    
    # --- Initialize Enhanced Memory Manager ---
    try:
        from app.enhanced_memory import AsyncSafeEnhancedMemoryManager
        memory_manager = AsyncSafeEnhancedMemoryManager(db, user)
        log.info("Enhanced memory manager initialized successfully")
    except Exception as e:
        log.warning(f"Could not initialize enhanced memory manager: {e}")
        memory_manager = None
    
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

**📋 Download Options:**
Your cover letter is ready for download! You can download it in multiple professional styles using the download dialog. Choose from Modern, Classic, or Minimal styles, edit content if needed, and preview before downloading.

*A download button should appear on this message to access all styling and editing options.*"""
            
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

**📋 Download Options:**
Your cover letter is ready for download! You can download it in multiple professional styles using the download dialog. Choose from Modern, Classic, or Minimal styles, edit content if needed, and preview before downloading.

*A download button should appear on this message to access all styling and editing options.*

<!-- content_id={new_cover_letter.id} company_name={company_name} job_title={job_title} -->"""
            
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
            
            return f"""## 📄 Resume PDF Ready

✅ **Your resume is ready for download!**

You can download your resume in multiple professional styles using the download dialog. Choose from Modern, Classic, or Minimal styles, edit content if needed, and preview before downloading.

*A download button should appear on this message to access all styling and editing options.*"""
            
        except Exception as e:
            log.error(f"Error generating resume PDF: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while preparing your resume PDF: {str(e)}. Please try again."

    @tool
    async def show_resume_download_options() -> str:
        """Show download options for the user's resume with PDF styling choices.
        
        Returns:
            Professional resume download interface with multiple PDF styles
        """
        try:
            # Check if user has resume data
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            db_resume = result.scalars().first()
            
            if not db_resume:
                return "❌ **No Resume Found**\n\nPlease create your resume first by adding:\n- Personal information\n- Work experience\n- Education\n- Skills\n\nUse the resume tools to build your professional resume!"
            
            return f"""## 📄 **CV/Resume Ready for Download**

✅ **Your CV/Resume is ready for download!**

You can download your CV/Resume in multiple professional styles. The download dialog will let you:

- **Choose from 3 professional styles** (Modern, Classic, Minimal)
- **Edit content** before downloading if needed
- **Preview** your CV/Resume before downloading
- **Download all styles** at once

*A download button should appear on this message to access all options.*"""
            
        except Exception as e:
            log.error(f"Error showing resume download options: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while preparing your resume download options: {str(e)}. Please try again."

    @tool
    async def get_document_insights() -> str:
        """Get personalized insights about user's uploaded documents including analysis and recommendations.
        
        Returns:
            Comprehensive insights about user's documents, career alignment, and optimization recommendations
        """
        try:
            # Get document insights using enhanced memory system
            from app.documents import _generate_comprehensive_document_insights
            
            # Get user documents
            doc_result = await db.execute(
                select(Document).where(Document.user_id == user.id)
            )
            documents = doc_result.scalars().all()
            
            if not documents:
                return "📄 **No Documents Found**\n\nYou haven't uploaded any documents yet. Upload your resume, cover letters, or other career documents to get personalized insights and recommendations!\n\n**To upload documents:**\n- Use the attachment button in the chat\n- Drag and drop files into the chat\n- Supported formats: PDF, DOCX, TXT"
            
            # Get user learning profile
            if memory_manager:
                user_profile = await memory_manager._get_user_learning_profile_safe()
            else:
                user_profile = None
            
            # Generate comprehensive insights
            insights = await _generate_comprehensive_document_insights(
                documents, user_profile, memory_manager
            )
            
            # Track insights tool usage
            if memory_manager:
                await memory_manager.save_user_behavior_safe(
                    action_type="document_insights_tool",
                    context={
                        "documents_count": len(documents),
                        "recommendations_count": len(insights.get("recommendations", [])),
                        "optimization_tips_count": len(insights.get("optimization_tips", [])),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    success=True
                )
            
            # Format the response for chat
            response_parts = [
                "📄 **Document Insights & Analysis**\n",
                f"**Summary:** {insights['summary']}\n"
            ]
            
            # Document analysis
            if insights.get("document_analysis"):
                analysis = insights["document_analysis"]
                response_parts.append("**📊 Document Overview:**")
                response_parts.append(f"- Total Documents: {analysis.get('total_documents', 0)}")
                
                doc_types = analysis.get('document_types', {})
                if doc_types:
                    type_summary = ", ".join([f"{count} {doc_type}(s)" for doc_type, count in doc_types.items()])
                    response_parts.append(f"- Types: {type_summary}")
                
                if analysis.get('latest_update'):
                    response_parts.append(f"- Last Updated: {analysis['latest_update'][:10]}")
                response_parts.append("")
            
            # Career alignment
            if insights.get("career_alignment"):
                alignment = insights["career_alignment"]
                response_parts.append("**🎯 Career Alignment:**")
                response_parts.append(f"- Target Roles: {', '.join(alignment.get('target_roles', []))}")
                response_parts.append(f"- Alignment Score: {alignment.get('document_relevance_score', 0)}/1.0 ({alignment.get('alignment_status', 'Unknown')})")
                response_parts.append("")
            
            # Recommendations
            if insights.get("recommendations"):
                response_parts.append("**💡 Personalized Recommendations:**")
                for i, recommendation in enumerate(insights["recommendations"], 1):
                    response_parts.append(f"{i}. {recommendation}")
                response_parts.append("")
            
            # Optimization tips
            if insights.get("optimization_tips"):
                response_parts.append("**⚡ Optimization Tips:**")
                for i, tip in enumerate(insights["optimization_tips"], 1):
                    response_parts.append(f"{i}. {tip}")
                response_parts.append("")
            
            response_parts.append("💬 **Need help with any specific document? Just ask me to analyze a particular file or help you improve your resume/cover letter!**")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            log.error(f"Error getting document insights: {e}")
            return "❌ Sorry, I couldn't retrieve your document insights right now. Please try again or let me know if you need help with document analysis."

    @tool
    async def analyze_specific_document(document_name: str) -> str:
        """Analyze a specific document by name and provide detailed feedback.
        
        Args:
            document_name: Name or partial name of the document to analyze
            
        Returns:
            Detailed analysis and personalized feedback for the specified document
        """
        try:
            # Search for documents matching the name
            doc_result = await db.execute(
                select(Document).where(
                    Document.user_id == user.id,
                    Document.name.ilike(f"%{document_name}%")
                )
            )
            documents = doc_result.scalars().all()
            
            if not documents:
                return f"📄 **Document Not Found**\n\nI couldn't find any document matching '{document_name}'. \n\n**Available documents:**\n" + await list_documents()
            
            if len(documents) > 1:
                doc_list = "\n".join([f"- {doc.name} ({doc.type})" for doc in documents])
                return f"📄 **Multiple Documents Found**\n\nFound {len(documents)} documents matching '{document_name}':\n\n{doc_list}\n\nPlease be more specific with the document name."
            
            document = documents[0]
            
            # Get detailed analysis using enhanced memory system
            from app.documents import _analyze_single_document
            
            if memory_manager:
                user_profile = await memory_manager._get_user_learning_profile_safe()
            else:
                user_profile = None
            analysis = await _analyze_single_document(document, user_profile, memory_manager)
            
            # Track specific document analysis
            if memory_manager:
                await memory_manager.save_user_behavior_safe(
                action_type="specific_document_analysis_tool",
                context={
                    "document_id": document.id,
                    "document_name": document.name,
                    "document_type": document.type,
                    "relevance_score": analysis.get("relevance_score", 0),
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=True
            )
            
            # Format the detailed analysis response
            response_parts = [
                f"📄 **Analysis: {analysis['document_info']['name']}**\n",
                f"**Document Type:** {analysis['document_info']['type'].title()}",
                f"**Created:** {analysis['document_info']['created'][:10]}",
                f"**Last Updated:** {analysis['document_info']['updated'][:10]}\n"
            ]
            
            # Content analysis
            if analysis.get("content_analysis"):
                content = analysis["content_analysis"]
                response_parts.append("**📊 Content Analysis:**")
                response_parts.append(f"- Word Count: {content.get('word_count', 0)}")
                response_parts.append(f"- Reading Time: {content.get('estimated_reading_time', 'Unknown')}")
                response_parts.append("")
            
            # Relevance score
            if analysis.get("relevance_score"):
                score = analysis["relevance_score"]
                score_percentage = int(score * 100)
                response_parts.append(f"**🎯 Relevance to Your Career Goals:** {score_percentage}%")
                response_parts.append("")
            
            # Resume-specific analysis
            if analysis.get("sections_detected"):
                response_parts.append("**📋 Resume Sections Detected:**")
                response_parts.append(f"- Found: {', '.join(analysis['sections_detected'])}")
                response_parts.append("")
            
            if analysis.get("skills_found"):
                response_parts.append("**💼 Technical Skills Identified:**")
                response_parts.append(f"- {', '.join(analysis['skills_found'])}")
                response_parts.append("")
            
            # Cover letter analysis
            if analysis.get("tone_indicators"):
                response_parts.append("**🎭 Tone Analysis:**")
                response_parts.append(f"- Detected: {', '.join(analysis['tone_indicators'])}")
                response_parts.append("")
            
            # Personalized feedback
            if analysis.get("personalized_feedback"):
                response_parts.append("**💡 Personalized Feedback:**")
                for i, feedback in enumerate(analysis["personalized_feedback"], 1):
                    response_parts.append(f"{i}. {feedback}")
                response_parts.append("")
            
            # Improvement suggestions
            if analysis.get("improvement_suggestions"):
                response_parts.append("**⚡ Improvement Suggestions:**")
                for i, suggestion in enumerate(analysis["improvement_suggestions"], 1):
                    response_parts.append(f"{i}. {suggestion}")
                response_parts.append("")
            
            # Resume-specific feedback
            if analysis.get("resume_feedback"):
                response_parts.append("**📄 Resume-Specific Feedback:**")
                for i, feedback in enumerate(analysis["resume_feedback"], 1):
                    response_parts.append(f"{i}. {feedback}")
                response_parts.append("")
            
            # Cover letter feedback
            if analysis.get("cover_letter_feedback"):
                response_parts.append("**✉️ Cover Letter Feedback:**")
                for i, feedback in enumerate(analysis["cover_letter_feedback"], 1):
                    response_parts.append(f"{i}. {feedback}")
                response_parts.append("")
            
            response_parts.append("💬 **Want more specific help? I can help you rewrite sections, add keywords, or create new versions tailored to specific job applications!**")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            log.error(f"Error analyzing specific document: {e}")
            return f"❌ Sorry, I couldn't analyze the document '{document_name}' right now. Please try again or upload the document if it's missing."

    @tool
    async def enhanced_document_search(query: str) -> str:
        """Search through user's documents with enhanced context from their job search patterns.
        
        Args:
            query: Search query to find relevant information in user's documents
            
        Returns:
            Relevant document content enhanced with user's learning context
        """
        try:
            # Use enhanced vector store search
            from app.vector_store import search_documents_with_context
            
            search_results = await search_documents_with_context(
                user.id, query, db, k=5
            )
            
            if not search_results:
                return f"🔍 **No Results Found**\n\nI couldn't find any relevant information for '{query}' in your uploaded documents.\n\n**Suggestions:**\n- Try different keywords\n- Upload more documents\n- Check if your documents contain the information you're looking for"
            
            # Track enhanced search usage
            if memory_manager:
                await memory_manager.save_user_behavior_safe(
                action_type="enhanced_document_search",
                context={
                    "query": query,
                    "results_count": len(search_results),
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=len(search_results) > 0
            )
            
            # Format search results
            response_parts = [
                f"🔍 **Search Results for '{query}'**\n",
                f"Found {len(search_results)} relevant sections:\n"
            ]
            
            for i, result in enumerate(search_results, 1):
                # Truncate long results for readability
                truncated_result = result[:300] + "..." if len(result) > 300 else result
                response_parts.append(f"**{i}.** {truncated_result}\n")
            
            response_parts.append("💬 **Need more specific information? Ask me about any particular aspect or request a detailed analysis!**")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            log.error(f"Error in enhanced document search: {e}")
            return f"❌ Sorry, I couldn't search your documents for '{query}' right now. Please try again or let me know if you need help with document analysis."

    @tool
    async def generate_tailored_resume(
        job_title: str,
        company_name: str = "",
        job_description: str = "",
        user_skills: str = ""
    ) -> str:
        """Generate a complete, tailored resume based on a job description and user information.
        
        Args:
            job_title: The job title to tailor the resume for
            company_name: Target company name (optional)
            job_description: Full job description to tailor against
            user_skills: Additional skills to highlight (optional)
        
        Returns:
            A complete, professionally formatted resume tailored to the job
        """
        try:
            # Get existing resume data
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            db_resume = result.scalars().first()
            
            # Get user documents for context
            doc_result = await db.execute(
                select(Document).where(Document.user_id == user.id).order_by(Document.date_uploaded.desc())
            )
            documents = doc_result.scalars().all()
            
            # Build context from existing resume and documents
            context = f"User: {user.first_name} {user.last_name}\n"
            context += f"Email: {user.email}\n"
            
            if db_resume:
                resume_data = ResumeData(**db_resume.data)
                context += f"Current Resume Data:\n"
                context += f"- Name: {resume_data.personalInfo.name}\n"
                context += f"- Summary: {resume_data.personalInfo.summary}\n"
                context += f"- Skills: {', '.join(resume_data.skills)}\n"
                
                if resume_data.experience:
                    context += f"- Experience: {len(resume_data.experience)} positions\n"
                    for exp in resume_data.experience[:3]:  # Latest 3
                        context += f"  * {exp.jobTitle} at {exp.company} ({exp.dates})\n"
                
                if resume_data.education:
                    context += f"- Education: {len(resume_data.education)} entries\n"
                    for edu in resume_data.education[:2]:  # Latest 2
                        context += f"  * {edu.degree} from {edu.institution}\n"
            
            # Add document context
            if documents:
                context += f"\nAdditional Documents: {len(documents)} files uploaded\n"
                for doc in documents[:3]:  # Latest 3 documents
                    if doc.content and len(doc.content) > 100:
                        context += f"- {doc.name}: {doc.content[:200]}...\n"
            
            # Create the resume generation chain
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are an expert resume writer and career coach. Create a complete, professional resume tailored specifically for the target job.

USER CONTEXT:
{context}

TARGET JOB:
- Position: {job_title}
- Company: {company_name}
- Job Description: {job_description}
- Additional Skills to Highlight: {user_skills}

INSTRUCTIONS:
1. Create a complete, ATS-friendly resume that's perfectly tailored to this specific job
2. Use the user's existing information but optimize it for the target role
3. Highlight relevant skills, experience, and achievements that match the job requirements
4. Use strong action verbs and quantify achievements where possible
5. Ensure the professional summary directly addresses the job requirements
6. Reorganize and emphasize experience that's most relevant to the target role
7. Include relevant keywords from the job description naturally
8. Keep it concise but comprehensive (1-2 pages)

FORMAT:
Structure the resume with clear sections:
- Professional Summary (3-4 lines tailored to the job)
- Core Skills (bullet points matching job requirements)
- Professional Experience (prioritize most relevant roles)
- Education
- Additional sections if relevant (Certifications, Projects, etc.)

Generate a complete, ready-to-use resume that would impress hiring managers for this specific role."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7,
                top_p=0.9
            )
            
            chain = prompt | llm | StrOutputParser()
            
            # Generate the tailored resume
            tailored_resume = await chain.ainvoke({
                "context": context,
                "job_title": job_title,
                "company_name": company_name or "the target company",
                "job_description": job_description or "No specific job description provided",
                "user_skills": user_skills or "Use existing skills from profile"
            })
            
            # Save the generated resume content to database
            from uuid import uuid4
            new_resume_record = GeneratedCoverLetter(  # Reusing table for now
                id=str(uuid4()),
                user_id=user.id,
                content=tailored_resume
            )
            db.add(new_resume_record)
            await db.commit()
            
            return f"""## 📄 **Tailored Resume Generated Successfully!**

✅ **Your resume has been professionally tailored for the {job_title} position{f' at {company_name}' if company_name else ''}**

{tailored_resume}

---

### 🎯 **Resume Optimization Features:**
- **ATS-Optimized**: Formatted to pass Applicant Tracking Systems
- **Job-Specific**: Tailored keywords and skills matching the job description
- **Achievement-Focused**: Quantified accomplishments and strong action verbs
- **Professional Format**: Clean, readable structure preferred by hiring managers

### 📥 **Download Options:**
*A download button should appear to get your resume in multiple professional PDF styles (Modern, Classic, Minimal)*

**💡 Pro Tip:** Review the generated content and make any personal adjustments before downloading!

<!-- content_id={new_resume_record.id} -->"""
            
        except Exception as e:
            log.error(f"Error generating tailored resume: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while generating your tailored resume: {str(e)}. Please try again or provide more specific job details."

    @tool
    async def enhance_resume_section(
        section: str,
        job_description: str = "",
        current_content: str = ""
    ) -> str:
        """Enhance a specific section of your resume with AI-powered improvements.
        
        Args:
            section: Section to enhance (summary, experience, skills, education)
            job_description: Target job description for tailoring (optional)
            current_content: Current content of the section to improve
        
        Returns:
            Enhanced, professional content for the specified resume section
        """
        try:
            # Get user context
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            db_resume = result.scalars().first()
            
            user_context = f"User: {user.first_name} {user.last_name}"
            if db_resume:
                resume_data = ResumeData(**db_resume.data)
                user_context += f"\nCurrent Resume Context: {resume_data.personalInfo.summary or 'No summary available'}"
                user_context += f"\nSkills: {', '.join(resume_data.skills) if resume_data.skills else 'No skills listed'}"
            
            # Create enhancement chain
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are an expert resume writer. Enhance the specified resume section to be more impactful and professional.

USER CONTEXT:
{user_context}

SECTION TO ENHANCE: {section}
CURRENT CONTENT: {current_content}
TARGET JOB DESCRIPTION: {job_description}

ENHANCEMENT GUIDELINES:
1. **Professional Summary**: Create compelling 3-4 line summary highlighting key value propositions
2. **Experience**: Use strong action verbs, quantify achievements, focus on results and impact
3. **Skills**: Organize by relevance, include both technical and soft skills, match job requirements
4. **Education**: Highlight relevant coursework, honors, achievements, and certifications

INSTRUCTIONS:
- Make the content more impactful and results-oriented
- Use industry-standard terminology and keywords
- Ensure ATS compatibility
- Tailor to the job description if provided
- Keep content concise but comprehensive
- Use strong action verbs and quantifiable metrics

Generate enhanced content that would impress hiring managers and pass ATS systems."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7
            )
            
            chain = prompt | llm | StrOutputParser()
            
            enhanced_content = await chain.ainvoke({
                "user_context": user_context,
                "section": section,
                "current_content": current_content or f"No current content provided for {section} section",
                "job_description": job_description or "No specific job description provided"
            })
            
            return f"""## ✨ **Enhanced {section.title()} Section**

{enhanced_content}

---

**💡 Enhancement Features Applied:**
- ✅ Professional language and terminology
- ✅ Action-oriented and results-focused
- ✅ ATS-optimized keywords
- ✅ Industry best practices
{f'- ✅ Tailored to job requirements' if job_description else ''}

**📝 Next Steps:** Copy this enhanced content to update your resume section, or use it as inspiration for further improvements!"""
            
        except Exception as e:
            log.error(f"Error enhancing resume section: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while enhancing your {section} section: {str(e)}. Please try again."

    @tool
    async def create_resume_from_scratch(
        target_role: str,
        experience_level: str = "mid-level",
        industry: str = "",
        key_skills: str = ""
    ) -> str:
        """Create a complete professional resume from scratch based on your career goals.
        
        Args:
            target_role: The type of role you're targeting (e.g., "Software Engineer", "Product Manager")
            experience_level: Your experience level (entry-level, mid-level, senior, executive)
            industry: Target industry (optional)
            key_skills: Your key skills and technologies (optional)
        
        Returns:
            A complete, professional resume template tailored to your career goals
        """
        try:
            # Get user information
            user_info = f"Name: {user.first_name} {user.last_name}\nEmail: {user.email}"
            
            # Get any existing documents for context
            doc_result = await db.execute(
                select(Document).where(Document.user_id == user.id).order_by(Document.date_uploaded.desc())
            )
            documents = doc_result.scalars().all()
            
            context = user_info
            if documents:
                context += f"\nAvailable documents: {len(documents)} files"
                for doc in documents[:2]:  # Latest 2 documents
                    if doc.content and len(doc.content) > 100:
                        context += f"\n- {doc.name}: {doc.content[:300]}..."
            
            # Create resume generation chain
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are an expert career coach and resume writer. Create a complete, professional resume from scratch.

USER INFORMATION:
{context}

CAREER GOALS:
- Target Role: {target_role}
- Experience Level: {experience_level}
- Industry: {industry}
- Key Skills: {key_skills}

INSTRUCTIONS:
Create a comprehensive resume template that includes:

1. **Professional Summary** (3-4 lines highlighting value proposition for the target role)
2. **Core Skills** (organized by relevance to the target role)
3. **Professional Experience** (3-4 relevant positions with achievements)
4. **Education** (relevant degree and certifications)
5. **Additional Sections** (projects, certifications, languages as relevant)

REQUIREMENTS:
- Make it ATS-friendly with clear section headers
- Use industry-specific keywords and terminology
- Include quantifiable achievements and metrics
- Structure for the specified experience level
- Ensure it's tailored to the target role and industry
- Use professional language and strong action verbs
- Keep it concise but comprehensive (1-2 pages)

If the user has uploaded documents, incorporate relevant information from them. If not, create a professional template with placeholder content that they can customize.

Generate a complete, ready-to-customize resume that would be competitive in today's job market."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7
            )
            
            chain = prompt | llm | StrOutputParser()
            
            new_resume = await chain.ainvoke({
                "context": context,
                "target_role": target_role,
                "experience_level": experience_level,
                "industry": industry or "general",
                "key_skills": key_skills or "relevant to the target role"
            })
            
            # Save to database
            from uuid import uuid4
            new_resume_record = GeneratedCoverLetter(  # Reusing table
                id=str(uuid4()),
                user_id=user.id,
                content=new_resume
            )
            db.add(new_resume_record)
            await db.commit()
            
            return f"""## 📄 **Professional Resume Created Successfully!**

✅ **Your {experience_level} {target_role} resume is ready!**

{new_resume}

---

### 🎯 **Resume Features:**
- **Role-Specific**: Tailored for {target_role} positions
- **Experience-Appropriate**: Structured for {experience_level} professionals
- **ATS-Optimized**: Formatted to pass Applicant Tracking Systems
- **Industry-Relevant**: {f'Focused on {industry} industry' if industry else 'Adaptable across industries'}

### 📥 **Next Steps:**
1. **Review & Customize**: Personalize the template with your specific details
2. **Download PDF**: Use the download button for professional formatting
3. **Tailor Further**: Customize for specific job applications

*A download button should appear to get your resume in multiple professional PDF styles*

**💡 Pro Tip:** This is your foundation - customize it for each job application for best results!

<!-- content_id={new_resume_record.id} -->"""
            
        except Exception as e:
            log.error(f"Error creating resume from scratch: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while creating your resume: {str(e)}. Please try again with more specific details."

    @tool
    async def refine_cv_for_role(
        target_role: str = "AI Engineering",
        job_description: str = "",
        company_name: str = ""
    ) -> str:
        """Refine and enhance an existing CV/resume for specific roles or industries.
        This is the primary tool for CV refinement requests.
        
        Args:
            target_role: The role or industry to tailor the CV for (e.g., "AI Engineering", "Software Development")
            job_description: Specific job description to tailor against (optional)
            company_name: Target company name (optional)
        
        Returns:
            A refined, professionally tailored CV optimized for the target role
        """
        try:
            log.info(f"CV refinement requested for role: {target_role}")
            
            # Use the generate_tailored_resume tool internally
            # This ensures we use the modern, working system instead of the broken RAG
            result = await generate_tailored_resume(
                job_title=target_role,
                company_name=company_name,
                job_description=job_description or f"General {target_role} position requirements",
                user_skills=""
            )
            
            # Add refinement-specific messaging
            refinement_message = f"""## ✨ **CV Successfully Refined for {target_role} Roles!**

🎯 **Your CV has been professionally enhanced and optimized for {target_role} positions.**

{result}

---

### 🚀 **Refinement Features Applied:**
- **Role-Specific Optimization**: Tailored specifically for {target_role} positions
- **Modern Generation System**: Used our latest AI-powered tools (not the old system)
- **ATS Compatibility**: Optimized for Applicant Tracking Systems
- **Industry Keywords**: Relevant terminology and skills highlighted
- **Professional Formatting**: Clean, readable structure preferred by hiring managers

### 💡 **Pro Tips:**
- **Customize Further**: Feel free to edit specific sections for particular applications
- **Multiple Versions**: Create different versions for different types of {target_role} roles
- **Regular Updates**: Refine again as you gain new skills or target different companies

**🎉 No more delays - your refined CV is ready immediately!**"""
            
            return refinement_message
            
        except Exception as e:
            log.error(f"Error in CV refinement: {e}", exc_info=True)
            return f"""❌ **CV Refinement Error**

I encountered an issue while refining your CV: {str(e)}

**🔧 Alternative Options:**
1. **Try Direct Generation**: Ask me to "generate a tailored resume for {target_role} roles"
2. **Upload Fresh CV**: Upload your current CV and I'll process it with the modern system
3. **Build from Scratch**: I can create a new CV using "create resume from scratch for {target_role}"

The modern tools are much more reliable than the old system!"""

    @tool
    async def get_cv_best_practices(
        industry: str = "",
        experience_level: str = "mid-level",
        role_type: str = ""
    ) -> str:
        """Get comprehensive CV best practices, tips, and guidelines tailored to your industry and experience level.
        
        Args:
            industry: Target industry (e.g., "tech", "finance", "healthcare", "marketing")
            experience_level: Your experience level (entry-level, mid-level, senior, executive)
            role_type: Type of role (e.g., "technical", "management", "sales", "creative")
        
        Returns:
            Detailed CV best practices and actionable tips
        """
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are an expert career coach and CV writer. Provide comprehensive, actionable CV best practices.

TARGET PROFILE:
- Industry: {industry}
- Experience Level: {experience_level}
- Role Type: {role_type}

Provide detailed guidance covering:

## 📋 **CV Structure & Format**
- Optimal CV length and layout
- Section ordering and priorities
- Font, spacing, and visual guidelines
- ATS-friendly formatting tips

## 🎯 **Content Best Practices**
- How to write compelling professional summaries
- Quantifying achievements with metrics
- Using strong action verbs effectively
- Tailoring content for specific roles

## 🔍 **Industry-Specific Tips**
- Key skills and keywords for this industry
- Common requirements and expectations
- Portfolio/work samples considerations
- Certification and education priorities

## ⚠️ **Common Mistakes to Avoid**
- Red flags that hurt your chances
- Outdated practices to eliminate
- Length and content balance issues
- Contact information best practices

## 🚀 **Advanced Strategies**
- ATS optimization techniques
- Personal branding integration
- LinkedIn profile alignment
- Cover letter coordination

## 📊 **Success Metrics**
- How to track CV performance
- When and how to update your CV
- Multiple version strategies

Provide specific, actionable advice that someone can implement immediately."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.6
            )
            
            chain = prompt | llm | StrOutputParser()
            
            guidance = await chain.ainvoke({
                "industry": industry or "general",
                "experience_level": experience_level,
                "role_type": role_type or "general professional"
            })
            
            return f"""## 📚 **CV Best Practices Guide**

🎯 **Tailored for:** {experience_level} {role_type} professionals{f' in {industry}' if industry else ''}

{guidance}

---

**💡 Quick Action Items:**
1. **Review Your Current CV**: Use these guidelines to audit your existing CV
2. **Implement Top 3 Changes**: Start with the most impactful improvements
3. **Test ATS Compatibility**: Use online ATS checkers to validate formatting
4. **Get Feedback**: Have colleagues or mentors review using these criteria

**🔗 Related Commands:**
- `enhance my resume section [section_name]` - Improve specific sections
- `create resume from scratch` - Start fresh with best practices
- `analyze my skills gap` - Identify areas for improvement"""
            
        except Exception as e:
            log.error(f"Error getting CV best practices: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while getting CV best practices: {str(e)}. Please try again."

    @tool
    async def analyze_skills_gap(
        target_role: str,
        current_skills: str = "",
        job_description: str = ""
    ) -> str:
        """Analyze the skills gap between your current abilities and target role requirements.
        
        Args:
            target_role: The role you're targeting (e.g., "Senior Software Engineer", "Product Manager")
            current_skills: Your current skills (optional - will use profile if available)
            job_description: Specific job description to analyze against (optional)
        
        Returns:
            Comprehensive skills gap analysis with learning recommendations
        """
        try:
            # Get user's current skills from profile
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            db_resume = result.scalars().first()
            
            user_skills = current_skills
            if not user_skills and db_resume:
                resume_data = ResumeData(**db_resume.data)
                user_skills = ', '.join(resume_data.skills) if resume_data.skills else ""
            
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are a career development expert. Analyze the skills gap and provide actionable career development advice.

TARGET ROLE: {target_role}
CURRENT SKILLS: {current_skills}
JOB DESCRIPTION: {job_description}

Provide a comprehensive skills gap analysis:

## 🎯 **Role Requirements Analysis**
- Core technical skills needed
- Soft skills and competencies required
- Experience level expectations
- Industry-specific knowledge needed

## ✅ **Your Strengths**
- Skills you already have that match
- Transferable skills from your background
- Competitive advantages you possess
- Areas where you exceed requirements

## 📈 **Skills to Develop**
### High Priority (Essential)
- Critical missing skills for the role
- Skills that appear in most job postings
- Technical competencies to prioritize

### Medium Priority (Valuable)
- Nice-to-have skills that differentiate candidates
- Emerging technologies in the field
- Cross-functional competencies

### Low Priority (Future Growth)
- Advanced skills for career progression
- Specialized technologies or certifications
- Leadership and management capabilities

## 📚 **Learning Roadmap**
### Immediate (Next 1-3 months)
- Specific courses, certifications, or bootcamps
- Free resources and tutorials
- Practical projects to build skills

### Medium-term (3-6 months)
- More comprehensive training programs
- Professional certifications
- Portfolio development projects

### Long-term (6+ months)
- Advanced certifications or degrees
- Conference attendance and networking
- Thought leadership opportunities

## 💼 **CV Enhancement Strategy**
- How to present existing skills more effectively
- Projects to showcase during skill development
- Keywords to incorporate from target role
- Experience gaps to address

## 🎯 **Action Plan**
Provide specific, time-bound recommendations for skill development."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7
            )
            
            chain = prompt | llm | StrOutputParser()
            
            analysis = await chain.ainvoke({
                "target_role": target_role,
                "current_skills": user_skills or "No skills information provided",
                "job_description": job_description or "No specific job description provided"
            })
            
            return f"""## 🔍 **Skills Gap Analysis for {target_role}**

{analysis}

---

**🚀 Next Steps:**
1. **Prioritize Learning**: Focus on high-priority skills first
2. **Update Your CV**: Add new skills as you develop them
3. **Build Projects**: Create portfolio pieces demonstrating new skills
4. **Network Actively**: Connect with professionals in your target role
5. **Track Progress**: Regularly reassess your skill development

**🔗 Helpful Commands:**
- `search jobs for [role]` - Find specific requirements in current job postings
- `enhance my resume section skills` - Optimize your skills presentation
- `create learning plan for [skill]` - Get detailed learning resources"""
            
        except Exception as e:
            log.error(f"Error analyzing skills gap: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error during skills gap analysis: {str(e)}. Please try again."

    @tool
    async def get_ats_optimization_tips(
        file_format: str = "PDF",
        industry: str = ""
    ) -> str:
        """Get specific tips for optimizing your CV to pass Applicant Tracking Systems (ATS).
        
        Args:
            file_format: CV file format you're using (PDF, DOCX, TXT)
            industry: Target industry for specific ATS considerations
        
        Returns:
            Comprehensive ATS optimization guide with actionable tips
        """
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are an ATS optimization expert. Provide comprehensive, technical guidance for passing modern ATS systems.

TARGET CONTEXT:
- File Format: {file_format}
- Industry: {industry}

Provide detailed ATS optimization guidance:

## 🤖 **Understanding ATS Systems**
- How modern ATS systems work
- What ATS algorithms look for
- Common ATS software types and their quirks
- Industry-specific ATS considerations

## 📄 **File Format Optimization**
- Best practices for {file_format} format
- Formatting do's and don'ts
- Font and layout recommendations
- File naming conventions

## 🔍 **Keyword Optimization**
### Keyword Research
- How to identify relevant keywords
- Where to find industry-specific terms
- Balancing keyword density naturally
- Using variations and synonyms

### Keyword Placement
- Strategic locations for keywords
- Section headers and their importance
- Natural integration techniques
- Avoiding keyword stuffing

## 📋 **Structure & Formatting**
### Section Organization
- ATS-friendly section headers
- Optimal section ordering
- Contact information formatting
- Date formats that ATS systems prefer

### Content Formatting
- Bullet points vs. paragraphs
- Special characters to avoid
- Table and column usage
- Header and footer limitations

## ✅ **Technical Best Practices**
- Font choices that scan well
- Margins and spacing guidelines
- Graphics and images considerations
- Links and hypertext handling

## 🧪 **Testing Your CV**
- Free ATS testing tools
- How to interpret ATS scan results
- Common parsing errors to fix
- Quality assurance checklist

## 📊 **Tracking & Iteration**
- Metrics to monitor application success
- When and how to update your CV
- A/B testing different versions
- Industry benchmarks for response rates

Provide specific, technical advice that ensures maximum ATS compatibility."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.6
            )
            
            chain = prompt | llm | StrOutputParser()
            
            tips = await chain.ainvoke({
                "file_format": file_format,
                "industry": industry or "general"
            })
            
            return f"""## 🤖 **ATS Optimization Guide**

📁 **Format:** {file_format} | 🏢 **Industry:** {industry or 'General'}

{tips}

---

**🔧 Immediate Actions:**
1. **Test Your Current CV**: Use Jobscan or similar ATS checker tools
2. **Review Keywords**: Compare your CV against 2-3 target job postings
3. **Fix Formatting Issues**: Address any parsing problems identified
4. **Create ATS Version**: Keep a simplified version specifically for ATS systems

**⚠️ Quick Checklist:**
- ✅ Uses standard section headers (Experience, Education, Skills)
- ✅ No graphics, tables, or complex formatting
- ✅ Keywords appear naturally throughout content
- ✅ Consistent date formatting (MM/YYYY)
- ✅ Contact info in simple text format
- ✅ File saved with professional naming convention

**🔗 Related Tools:**
- `generate tailored resume` - Create ATS-optimized content
- `enhance my resume section` - Improve keyword density"""
            
        except Exception as e:
            log.error(f"Error getting ATS optimization tips: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while getting ATS tips: {str(e)}. Please try again."

    @tool
    async def get_interview_preparation_guide(
        job_title: str,
        company_name: str = "",
        interview_type: str = "general"
    ) -> str:
        """Get comprehensive interview preparation guidance based on your CV and target role.
        
        Args:
            job_title: Position you're interviewing for
            company_name: Target company (optional)
            interview_type: Type of interview (behavioral, technical, panel, phone, video)
        
        Returns:
            Personalized interview preparation guide with questions and strategies
        """
        try:
            # Get user's CV data for personalized prep
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            db_resume = result.scalars().first()
            
            user_context = f"User: {user.first_name} {user.last_name}"
            if db_resume:
                resume_data = ResumeData(**db_resume.data)
                user_context += f"\nBackground: {resume_data.personalInfo.summary or 'No summary available'}"
                user_context += f"\nKey Skills: {', '.join(resume_data.skills[:5]) if resume_data.skills else 'No skills listed'}"
                if resume_data.experience:
                    user_context += f"\nRecent Role: {resume_data.experience[0].jobTitle} at {resume_data.experience[0].company}"
            
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are an expert interview coach. Create a comprehensive, personalized interview preparation guide.

USER CONTEXT: {user_context}
TARGET ROLE: {job_title}
COMPANY: {company_name}
INTERVIEW TYPE: {interview_type}

Create a detailed interview preparation guide:

## 🎯 **Role-Specific Preparation**
### Key Competencies to Highlight
- Core skills most relevant to this role
- How to connect your background to role requirements
- Unique value propositions to emphasize
- Potential concerns to address proactively

### Industry Context
- Current trends and challenges in the industry
- Company-specific research points
- Market positioning and competitive landscape
- Recent news or developments to mention

## 💬 **Expected Interview Questions**
### Behavioral Questions (STAR Method)
- 5-7 likely behavioral questions for this role
- Frameworks for structuring responses
- How to use your CV experiences effectively
- Stories to prepare from your background

### Technical/Role-Specific Questions
- Technical skills assessments to expect
- Problem-solving scenarios relevant to the role
- Industry knowledge questions
- Portfolio or work sample discussions

### Situational Questions
- Hypothetical scenarios for this position
- Leadership and teamwork examples
- Conflict resolution situations
- Decision-making frameworks

## 🤝 **Company Research Strategy**
### Essential Research Areas
- Company mission, values, and culture
- Recent achievements and challenges
- Leadership team and organizational structure
- Products, services, and market position

### Research Sources
- Official company resources
- Industry publications and news
- Employee insights (LinkedIn, Glassdoor)
- Social media and recent announcements

## ❓ **Questions to Ask Them**
### Role and Responsibilities
- Thoughtful questions about the position
- Team dynamics and collaboration
- Success metrics and expectations
- Growth opportunities and career path

### Company and Culture
- Strategic questions about company direction
- Culture and work environment inquiries
- Professional development opportunities
- Industry challenges and opportunities

## 🎭 **Interview Performance Tips**
### Communication Strategies
- How to present your CV experiences compellingly
- Confidence-building techniques
- Body language and presentation tips
- Virtual interview best practices (if applicable)

### Common Pitfalls to Avoid
- Red flags that hurt candidates
- How to handle difficult questions
- Salary and compensation discussions
- Follow-up and next steps etiquette

## 📋 **Preparation Checklist**
### Before the Interview
- Documents and materials to prepare
- Questions and answers to practice
- Research tasks to complete
- Logistics and setup considerations

### Day of Interview
- Final preparation steps
- What to bring/have ready
- Timing and arrival guidelines
- Backup plans for technical issues

Provide specific, actionable advice tailored to this role and the user's background."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7
            )
            
            chain = prompt | llm | StrOutputParser()
            
            guide = await chain.ainvoke({
                "user_context": user_context,
                "job_title": job_title,
                "company_name": company_name or "the target company",
                "interview_type": interview_type
            })
            
            return f"""## 🎯 **Interview Preparation Guide**

**Role:** {job_title} | **Company:** {company_name or 'Target Company'} | **Type:** {interview_type.title()}

{guide}

---

**📅 Preparation Timeline:**
- **1 Week Before**: Complete company research and prepare STAR stories
- **3 Days Before**: Practice answers and finalize questions to ask
- **1 Day Before**: Review notes, prepare materials, test technology
- **Day Of**: Final review, arrive early, stay confident

**🎯 Success Metrics:**
- ✅ Can articulate your value proposition clearly
- ✅ Have 3-5 compelling STAR stories ready
- ✅ Know key company facts and recent developments  
- ✅ Have thoughtful questions prepared
- ✅ Feel confident about your qualifications

**🔗 Next Steps:**
- `enhance my resume section` - Align CV with interview talking points
- `generate cover letter` - Practice articulating your interest
- `get salary negotiation tips` - Prepare for compensation discussions"""
            
        except Exception as e:
            log.error(f"Error creating interview preparation guide: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while creating your interview guide: {str(e)}. Please try again."

    @tool
    async def get_salary_negotiation_advice(
        job_title: str,
        experience_level: str = "mid-level", 
        location: str = "",
        industry: str = ""
    ) -> str:
        """Get comprehensive salary negotiation strategies and market data insights.
        
        Args:
            job_title: Position you're negotiating for
            experience_level: Your experience level (entry-level, mid-level, senior, executive)
            location: Job location for market rate context
            industry: Industry for sector-specific advice
        
        Returns:
            Detailed salary negotiation guide with strategies and market insights
        """
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are a compensation and career negotiation expert. Provide comprehensive salary negotiation guidance.

NEGOTIATION CONTEXT:
- Job Title: {job_title}
- Experience Level: {experience_level}
- Location: {location}
- Industry: {industry}

Provide detailed negotiation strategy and advice:

## 💰 **Market Research & Benchmarking**
### Salary Research Sources
- Best websites and tools for salary data
- How to interpret salary ranges accurately
- Geographic and industry adjustments
- Experience level modifiers

### Compensation Package Components
- Base salary considerations
- Bonus and incentive structures
- Benefits and perquisites
- Equity and stock options
- Remote work and flexibility value

## 🎯 **Negotiation Strategy**
### Preparation Phase
- How to determine your target range
- Building your value proposition
- Documentation of achievements and impact
- Market rate justification techniques

### Timing Considerations
- When to bring up compensation
- How to respond to salary questions
- Negotiating after offer receipt
- Multiple offer leverage strategies

### Communication Tactics
- Scripts and language for negotiations
- How to present counter-offers professionally
- Negotiating non-salary benefits
- Handling objections and pushback

## 📋 **Negotiation Framework**
### Initial Offer Response
- How to buy time for consideration
- Expressing enthusiasm while negotiating
- Questions to ask about the offer
- Professional response templates

### Counter-Offer Strategy
- How to structure compelling counter-offers
- Supporting your requests with data
- Prioritizing different compensation elements
- Alternative proposals if budget is fixed

### Closing the Deal
- Finalizing agreed terms professionally
- Getting offers in writing
- Graceful acceptance or decline
- Maintaining relationships regardless of outcome

## 🎭 **Common Scenarios & Responses**
### Difficult Situations
- "Our budget is fixed" responses
- Geographic pay differences
- Internal equity concerns
- First-time negotiator anxiety

### Advanced Strategies
- Multiple offer negotiations
- Retention counter-offers
- Promotion and raise requests
- Contract vs. full-time considerations

## ⚠️ **Pitfalls to Avoid**
### Negotiation Mistakes
- Red flags that hurt your chances
- Overplaying your hand
- Burning bridges unnecessarily
- Focusing only on salary

### Professional Etiquette
- Maintaining positive relationships
- Respecting company constraints
- Being prepared to walk away
- Following up appropriately

## 📊 **Market Insights**
- Typical salary ranges for {experience_level} {job_title} roles
- Industry-specific compensation trends
- Geographic variations and cost of living
- Emerging benefits and perks trends
- Economic factors affecting compensation

Provide specific, actionable negotiation advice with realistic expectations."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7
            )
            
            chain = prompt | llm | StrOutputParser()
            
            advice = await chain.ainvoke({
                "job_title": job_title,
                "experience_level": experience_level,
                "location": location or "general market",
                "industry": industry or "general"
            })
            
            return f"""## 💰 **Salary Negotiation Strategy Guide**

**Role:** {job_title} | **Level:** {experience_level} | **Market:** {location or 'General'}

{advice}

---

**🚀 Action Plan:**
1. **Research Phase** (Before applying): Gather market data and set target range
2. **Application Phase**: Avoid early salary discussions, focus on fit
3. **Interview Phase**: Demonstrate value, delay compensation talks
4. **Offer Phase**: Evaluate total package, prepare counter-offer
5. **Negotiation Phase**: Present professional counter with justification
6. **Decision Phase**: Make informed choice aligned with career goals

**📊 Negotiation Checklist:**
- ✅ Researched market rates from multiple sources
- ✅ Calculated total compensation package value
- ✅ Prepared specific examples of your value/impact
- ✅ Determined acceptable range and walk-away point
- ✅ Practiced negotiation conversations
- ✅ Ready to discuss non-salary benefits

**⚡ Key Reminders:**
- **Be Professional**: Maintain positive tone throughout
- **Focus on Value**: Emphasize what you bring to the role
- **Consider Total Package**: Look beyond just base salary
- **Know Your Worth**: But be realistic about market conditions
- **Have Alternatives**: Negotiate from position of choice, not desperation

**🔗 Related Tools:**
- `search jobs for [role]` - Research current market opportunities
- `get interview preparation guide` - Prepare to demonstrate value"""
            
        except Exception as e:
            log.error(f"Error getting salary negotiation advice: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while getting negotiation advice: {str(e)}. Please try again."

    @tool
    async def create_career_development_plan(
        current_role: str = "",
        target_role: str = "",
        timeline: str = "2 years"
    ) -> str:
        """Create a comprehensive career development plan with specific steps and milestones.
        
        Args:
            current_role: Your current position/role
            target_role: Where you want to be in your career
            timeline: Timeframe for achieving your goal (e.g., "1 year", "3 years", "5 years")
        
        Returns:
            Detailed career development roadmap with actionable steps
        """
        try:
            # Get user context from resume
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            db_resume = result.scalars().first()
            
            user_context = f"User: {user.first_name} {user.last_name}"
            if db_resume:
                resume_data = ResumeData(**db_resume.data)
                user_context += f"\nCurrent Background: {resume_data.personalInfo.summary or 'No summary available'}"
                user_context += f"\nSkills: {', '.join(resume_data.skills[:8]) if resume_data.skills else 'No skills listed'}"
                if resume_data.experience:
                    user_context += f"\nCurrent Role: {resume_data.experience[0].jobTitle} at {resume_data.experience[0].company}"
            
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are a senior career strategist and executive coach. Create a comprehensive, actionable career development plan.

USER CONTEXT: {user_context}
CURRENT ROLE: {current_role}
TARGET ROLE: {target_role}
TIMELINE: {timeline}

Create a detailed career development roadmap:

## 🎯 **Career Vision & Goals**
### Target Role Analysis
- Detailed breakdown of target role requirements
- Skills, experience, and qualifications needed
- Typical career progression path to this role
- Market demand and growth outlook

### Gap Analysis
- Current state vs. target state assessment
- Critical skills and experience gaps
- Knowledge areas requiring development
- Network and relationship gaps

## 🗓️ **Timeline & Milestones**
### Phase 1: Foundation Building (Months 1-{timeline_first_third})
- Immediate skill development priorities
- Quick wins and early achievements
- Network building initiatives
- Performance optimization in current role

### Phase 2: Growth & Expansion (Months {timeline_middle})
- Advanced skill acquisition
- Leadership development activities
- Strategic project involvement
- External visibility building

### Phase 3: Positioning & Transition (Final phase)
- Final preparation for target role
- Strategic job search activities
- Interview and positioning preparation
- Offer negotiation and transition planning

## 📚 **Learning & Development Strategy**
### Technical Skills Development
- Specific courses, certifications, and training
- Online learning platforms and resources
- Hands-on projects and applications
- Skill assessment and validation methods

### Soft Skills Enhancement
- Leadership and management capabilities
- Communication and presentation skills
- Strategic thinking and business acumen
- Industry knowledge and market awareness

### Formal Education & Certifications
- Professional certifications to pursue
- Advanced degree considerations
- Industry-specific credentials
- Cost-benefit analysis of educational investments

## 🤝 **Networking & Relationship Building**
### Professional Network Expansion
- Industry conferences and events to attend
- Professional associations to join
- LinkedIn strategy and online presence
- Informational interview targets

### Mentorship & Sponsorship
- Identifying potential mentors
- Building sponsor relationships
- Peer learning groups and communities
- Reverse mentoring opportunities

### Internal Relationship Building
- Stakeholder mapping in current organization
- Cross-functional collaboration opportunities
- Visibility projects and high-impact initiatives
- Leadership team exposure strategies

## 💼 **Experience & Exposure Plan**
### Current Role Optimization
- Ways to enhance current role impact
- Additional responsibilities to seek
- Performance metrics to improve
- Success stories to develop

### Strategic Project Involvement
- High-visibility projects to pursue
- Cross-functional team leadership
- Innovation and change initiatives
- Customer or client-facing opportunities

### External Experience Building
- Volunteer leadership roles
- Industry speaking opportunities
- Writing and thought leadership
- Board or committee service

## 📊 **Progress Tracking & Measurement**
### Key Performance Indicators
- Specific metrics to track progress
- Milestone achievement criteria
- Skills assessment benchmarks
- Network growth measurements

### Regular Review Process
- Monthly progress check-ins
- Quarterly goal adjustments
- Annual plan reviews and updates
- Feedback collection and integration

### Course Correction Strategies
- How to adapt plan based on market changes
- Pivoting strategies if goals change
- Accelerating progress when opportunities arise
- Managing setbacks and delays

## 🚀 **Action Plan & Next Steps**
### Immediate Actions (Next 30 days)
- Specific tasks to start immediately
- Resources to gather and review
- Conversations to initiate
- Systems to put in place

### Short-term Priorities (Next 90 days)
- Major initiatives to launch
- Skills development to begin
- Relationships to build
- Opportunities to pursue

Provide specific, time-bound, measurable actions that create a clear path to the target role."""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7
            )
            
            chain = prompt | llm | StrOutputParser()
            
            # Calculate timeline phases for the prompt
            timeline_months = 24  # Default to 2 years
            if "1 year" in timeline.lower():
                timeline_months = 12
            elif "3 year" in timeline.lower():
                timeline_months = 36
            elif "5 year" in timeline.lower():
                timeline_months = 60
            
            first_third = timeline_months // 3
            middle = f"{first_third + 1}-{timeline_months * 2 // 3}"
            
            plan = await chain.ainvoke({
                "user_context": user_context,
                "current_role": current_role or "current position",
                "target_role": target_role or "target career goal",
                "timeline": timeline,
                "timeline_first_third": first_third,
                "timeline_middle": middle
            })
            
            return f"""## 🚀 **Career Development Plan**

**Journey:** {current_role or 'Current Role'} → {target_role or 'Target Role'} | **Timeline:** {timeline}

{plan}

---

**📋 Implementation Checklist:**
- ✅ Schedule monthly career development review meetings
- ✅ Create learning and development budget
- ✅ Identify and reach out to potential mentors
- ✅ Set up skill assessment baseline measurements
- ✅ Begin networking activities and relationship building
- ✅ Start first priority learning initiative

**⚡ Success Factors:**
- **Consistency**: Regular, dedicated effort toward goals
- **Flexibility**: Adapt plan based on opportunities and market changes
- **Accountability**: Regular progress reviews and adjustments
- **Network**: Strong professional relationships for guidance and opportunities
- **Measurement**: Clear metrics to track progress and success

**🔄 Review Schedule:**
- **Weekly**: Progress on immediate actions and priorities
- **Monthly**: Overall plan progress and milestone achievement
- **Quarterly**: Goals adjustment and strategy refinement
- **Annually**: Comprehensive plan review and major updates

**🔗 Supporting Tools:**
- `analyze my skills gap` - Regular skills assessment
- `get interview preparation guide` - Practice for target role
- `enhance my resume section` - Update CV as you grow"""
            
        except Exception as e:
            log.error(f"Error creating career development plan: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while creating your career plan: {str(e)}. Please try again."

    # Add the new tools to the tools list
    tools = [
        search_jobs_tool,
        update_personal_information,
        add_work_experience,
        add_education,
        set_skills,
        list_documents,
        read_document,
        search_jobs_with_browser,
        generate_cover_letter_from_url,
        generate_cover_letter,
        generate_resume_pdf,
        show_resume_download_options,  # New CV/Resume download center
        get_document_insights,  # New enhanced document insights tool
        analyze_specific_document,  # New specific document analysis tool
        enhanced_document_search,  # New enhanced document search tool
        generate_tailored_resume,  # New tailored resume generation tool
        enhance_resume_section,  # New resume section enhancement tool
        create_resume_from_scratch,  # New resume creation from scratch tool
        refine_cv_for_role,  # New CV refinement tool that routes to modern systems
        get_cv_best_practices,  # New comprehensive CV guidance tool
        analyze_skills_gap,  # New skills gap analysis tool
        get_ats_optimization_tips,  # New ATS optimization guide
        get_interview_preparation_guide,  # New interview prep tool
        get_salary_negotiation_advice,  # New salary negotiation guide
        create_career_development_plan,  # New career planning tool
    ]
    
    if retriever:
        retriever_tool = create_retriever_tool(
            retriever,
            "document_retriever",
            "Searches and returns information from the user's documents."
        )
        tools.append(retriever_tool)

    # Generate enhanced system prompt with user learning context
    try:
        if memory_manager:
            enhanced_system_prompt = await memory_manager.get_contextual_system_prompt_safe()
            master_agent = create_master_agent(tools, user_documents, enhanced_system_prompt)
            log.info(f"Created master agent with enhanced memory for user {user.id}")
        else:
            master_agent = create_master_agent(tools, user_documents)
            log.info(f"Created basic master agent for user {user.id}")
    except Exception as e:
        log.warning(f"Failed to create enhanced memory agent, falling back to basic: {e}")
        master_agent = create_master_agent(tools, user_documents)

    # --- Enhanced Chat History & Main Loop ---
    try:
        if memory_manager:
            # Get enhanced conversation context with summarization and user learning
            context = await memory_manager.get_enhanced_conversation_context_safe()
            
            # Convert recent messages to LangChain format
            current_chat_history = []
            for msg_data in context.recent_messages:
                try:
                    content = msg_data["content"]
                    if msg_data["role"] == "user":
                        current_chat_history.append(HumanMessage(content=content))
                    else:
                        current_chat_history.append(AIMessage(content=content))
                except Exception as e:
                    log.warning(f"Error processing message in enhanced context: {e}")
            
            # Add conversation summary as system message if available
            if context.summary and context.conversation_length > memory_manager.summary_trigger_length:
                summary_message = HumanMessage(content=f"[Conversation Summary: {context.summary}]")
                current_chat_history.insert(0, summary_message)
            
            log.info(f"Loaded enhanced chat history: {len(current_chat_history)} messages, summary available: {bool(context.summary)}")
        else:
            # Fallback to basic chat history loading
            raise Exception("Memory manager not available, using basic history")
        
    except Exception as e:
        log.error(f"Error loading enhanced chat history, falling back to basic: {e}")
        # Fallback to basic chat history loading with proper transaction handling
        try:
            await db.rollback()  # Ensure clean transaction state
            history_records = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.user_id == user.id)
                .where(ChatMessage.page_id.is_(None))
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
        except Exception as fallback_error:
            log.error(f"Failed to load basic chat history: {fallback_error}")
            current_chat_history = []  # Start with empty history if all fails

    # Track the currently loaded page to avoid reloading
    current_loaded_page_id = None

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
                    current_loaded_page_id = None
                    log.info(f"Chat context cleared for user {user.id}")
                    continue
                elif message_data.get("type") == "switch_page":
                    # Handle explicit page switching from frontend
                    new_page_id = message_data.get("page_id")
                    if new_page_id != current_loaded_page_id:
                        current_loaded_page_id = new_page_id
                        log.info(f"WebSocket context switched to page {new_page_id}")
                    continue
                elif message_data.get("type") == "regenerate":
                    # Extract page_id for regeneration from message data
                    regenerate_page_id = message_data.get("page_id")
                    
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
                        
                        # Save AI message with page context (use the page_id from regeneration request)
                        try:
                            ai_message_id = str(uuid.uuid4())
                            db.add(ChatMessage(
                                id=ai_message_id,
                                user_id=user.id,
                                page_id=regenerate_page_id,  # Use page_id from regeneration request
                                message=result,
                                is_user_message=False
                            ))
                            await db.commit()
                            log.info(f"Saved regenerated AI message {ai_message_id} with page_id: {regenerate_page_id}")
                        except Exception as save_error:
                            log.error(f"Failed to save AI message: {save_error}")
                            await db.rollback()
                            ai_message_id = str(uuid.uuid4())  # Generate new ID for retry
                        
                        current_chat_history.append(AIMessage(id=ai_message_id, content=result))
                    continue
                elif "content" in message_data:
                    # New format with page context
                    message_content = message_data["content"]
                    page_id = message_data.get("page_id")
                    
                    # Only load page history if WebSocket context isn't already set for this page
                    # Frontend is responsible for loading messages via API, WebSocket just tracks context
                    if page_id != current_loaded_page_id:
                        if page_id:
                            # Load conversation history for AI context only (don't send to frontend)
                            try:
                                page_history = await db.execute(
                                    select(ChatMessage)
                                    .where(ChatMessage.user_id == user.id)
                                    .where(ChatMessage.page_id == page_id)
                                    .order_by(ChatMessage.created_at)
                                )
                                
                                # Build chat history for AI context
                                new_chat_history = []
                                for r in page_history.scalars().all():
                                    try:
                                        content = json.loads(r.message)
                                    except (json.JSONDecodeError, TypeError):
                                        content = r.message
                                    
                                    if r.is_user_message:
                                        new_chat_history.append(HumanMessage(id=r.id, content=content if isinstance(content, str) else json.dumps(content)))
                                    else:
                                        new_chat_history.append(AIMessage(id=r.id, content=content if isinstance(content, str) else json.dumps(content)))
                                
                                current_chat_history = new_chat_history
                                current_loaded_page_id = page_id
                                log.info(f"WebSocket context loaded {len(current_chat_history)} messages for page {page_id}")
                            except Exception as page_error:
                                log.error(f"Failed to load page history for WebSocket context {page_id}: {page_error}")
                                await db.rollback()
                                current_chat_history = []
                        else:
                            # New conversation - clear context
                            current_chat_history = []
                            current_loaded_page_id = None
                            log.info("WebSocket context switched to new conversation")
                
            except json.JSONDecodeError:
                # It's a regular text message (legacy format)
                pass
            
            # Save user message with page context
            try:
                user_message_id = str(uuid.uuid4())
                db.add(ChatMessage(
                    id=user_message_id,
                    user_id=user.id,
                    page_id=page_id,
                    message=message_content,
                    is_user_message=True
                ))
                await db.commit()
                log.info(f"Saved user message {user_message_id} with page_id: {page_id}")
            except Exception as save_error:
                log.error(f"Failed to save user message: {save_error}")
                await db.rollback()
                user_message_id = str(uuid.uuid4())  # Generate new ID for retry
            
            current_chat_history.append(HumanMessage(id=user_message_id, content=message_content))

            # Track user message behavior
            if memory_manager:
                try:
                    await memory_manager.save_user_behavior_safe(
                        action_type="chat_message",
                        context={
                            "message_length": len(message_content),
                            "page_id": page_id,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        success=True
                    )
                except Exception as e:
                    log.warning(f"Failed to save user behavior: {e}")

            # Pass message to our agent with enhanced context
            try:
                response = await master_agent.ainvoke({
                    "input": message_content,
                    "chat_history": current_chat_history,
                })
                result = response.get("output", "I'm sorry, I encountered an issue.")
                
                # Track successful agent response
                if memory_manager:
                    await memory_manager.save_user_behavior_safe(
                        action_type="agent_response",
                        context={
                            "response_length": len(result),
                            "input_length": len(message_content),
                            "page_id": page_id
                        },
                        success=True
                    )
                
            except Exception as e:
                log.error(f"Error in agent processing: {e}")
                result = "I'm sorry, I encountered an issue processing your request. Please try again."
                
                # Track failed agent response
                if memory_manager:
                    try:
                        await memory_manager.save_user_behavior_safe(
                            action_type="agent_response",
                            context={
                                "error": str(e),
                                "input_length": len(message_content),
                                "page_id": page_id
                            },
                            success=False
                        )
                    except Exception:
                        pass
            
            await websocket.send_text(result)
            
            # Save AI message with page context
            try:
                ai_message_id = str(uuid.uuid4())
                db.add(ChatMessage(
                    id=ai_message_id,
                    user_id=user.id,
                    page_id=page_id,
                    message=result,
                    is_user_message=False
                ))
                await db.commit()
                log.info(f"Saved AI message {ai_message_id} with page_id: {page_id}")
            except Exception as save_error:
                log.error(f"Failed to save AI message: {save_error}")
                await db.rollback()
                ai_message_id = str(uuid.uuid4())  # Generate new ID for retry
            
            current_chat_history.append(AIMessage(id=ai_message_id, content=result))
            
    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        log.error(f"WebSocket error for user {user.id}: {e}")
        try:
            await websocket.send_text(f"An error occurred: {str(e)}")
        except Exception:
            pass  # WebSocket might be closed 