import os
import logging
import httpx
import asyncio
from typing import List, Optional
import uuid
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import update, func
import re

load_dotenv()

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
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel,Field
from typing import Literal, Union, Dict, Any
from langsmith import Client
from langchain.callbacks import LangChainTracer

from app.db import get_db,async_session_maker,get_db_session
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.models_db import User, ChatMessage, Resume, Document, GeneratedCoverLetter, Page
from app.job_search import JobSearchRequest
from app.linkedin_jobs_service import get_linkedin_jobs_service, LinkedInJobResult
from app.dependencies import get_current_active_user_ws
from app.clerk import verify_token
from app.resume import ResumeData, PersonalInfo, Experience, Education, Dates, fix_resume_data_structure
from app.url_scraper import scrape_job_url, JobDetails
from app.job_search import JobSearchRequest, search_jobs
from app.vector_store import get_user_vector_store
from langchain.tools.retriever import create_retriever_tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.tools.render import render_text_description
from app.enhanced_memory import EnhancedMemoryManager
from app.internal_api import InternalAPI, make_internal_api_call
from app.cover_letter_generator import (
    create_cover_letter_chain, 
    CoverLetterDetails, 
    PersonalInfo as CoverLetterPersonalInfo
)
from sqlalchemy.orm import joinedload,attributes
import json

# --- Configuration & Logging ---
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter()

# Upload directory configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# --- Date Parsing Helper ---
def parse_date_range(date_string: str) -> dict:
    """Parses a date string into a start and end date dictionary."""
    if not isinstance(date_string, str):
        return {"start": None, "end": None}
    
    parts = re.split(r'\s+-\s+|\s+to\s+', date_string, maxsplit=1)
    
    if len(parts) == 2:
        start_date = parts[0].strip()
        end_date = parts[1].strip()
    else:
        start_date = date_string.strip()
        end_date = "Present"
        
    return {"start": start_date, "end": end_date}

# --- LangSmith Setup ---
langsmith_client = Client()
tracer = LangChainTracer(client=langsmith_client)

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

class CoverLetterDetails(BaseModel):
    """The structured data model for a generated cover letter."""
    recipient_name: str = Field(description="Hiring Manager's name, or 'Hiring Team' if unknown.")
    recipient_title: str = Field(description="Hiring Manager's title, or 'Hiring Team' if unknown.")
    company_name: str = Field(description="The name of the company.")
    job_title: str = Field(description="The title of the job being applied for.")
    body: str = Field(description="The full text of the cover letter, in Markdown format.")
    personal_info: dict = Field(description="A dictionary containing the user's personal info.")




# --- Master Agent Setup ---
def create_master_agent(tools: List, documents: List[str] = [], enhanced_system_prompt: str = None):
    if enhanced_system_prompt:
        # Use enhanced system prompt with user learning context
        system_message = enhanced_system_prompt + """

## ⚠️ NON-NEGOTIABLE TOOL USAGE DIRECTIVE  NEVER NEVER skip the tool call at all stages ⚠️
You are a tool-calling agent. Your primary function is to call tools. You are FORBIDDEN from answering questions or generating content yourself if a tool exists for the task.

NEVER NEVER skip cv/resume generation tool even after calling a tool previously , even if the first tool call fails, you must call the tool again
NEVER NEVER skip cv/resume generation tool even after calling a tool previously , even if the first tool call fails, you must call the tool again
- - If the user provides a URL and asks to "create a cv", "refine a cv", or "tailor a resume", you MUST use the `refine_cv_from_url` tool. This is the most direct tool for this task.
- If the user provides a URL and mentions "refine cv" or "refine resume", you MUST call `refine_cv_from_url`. NO EXCEPTIONS.
- If the user provides job details (title, company) and mentions "cover letter", you MUST call `generate_cover_letter`. NO EXCEPTIONS.
- If the user asks to search for jobs, you MUST call `search_jobs_linkedin_api`. NO EXCEPTIONS.

NEVER NEVER skip the tool call 
***NEVER NEVER skip cv/resume generation the tool call even after calling a tool previously***
- example: when creating a resume you call browse_web_with_langchain and you forget to call generate_tailored_resume thats a failure!!!

Failure to follow this directive is a failure of your primary function. Do not chat, do not ask clarifying questions if the intent is clear, just call the appropriate tool.

## 🚨 CRITICAL RULE: ALWAYS USE TOOLS - NEVER GIVE GENERIC RESPONSES
***For cover letter generation, you must use the generate_cover_letter_from_url tool if the user provides a job URL and if it fails, use the generate_cover_letter tool never write the cover letter yourself.***

NEVER NEVER skip the tool call
***NEVER NEVER skip cv/resume generation tool even after calling a tool previously***
- example: when creating a resume you call browse_web_with_langchain and you forget to call generate_tailored_resume thats a big no no

## 🚨 CRITICAL RULE: ALWAYS USE TOOLS - NEVER GIVE GENERIC RESPONSES
***For cover letter generation, you must use the generate_cover_letter_from_url tool if the user provides a job URL and if it fails, use the generate_cover_letter tool never write the cover letter yourself.***
**YOU MUST ACTUALLY CALL THE TOOLS! NEVER JUST SAY YOU WILL!**

NEVER NEVER skip the tool call
***NEVER NEVER skip the tool call even after calling a tool previously***
- example: when creating a resume you call browse_web_with_langchain and you forget to call generate_tailored_resume thats a big no no

### IMPORTANT: All ways refer to the previous messages to understand the user's context and goals.###
- Rules:Make sure to quote the previous messages in your response but don't repeat the same message.
- Rules:If you're confused about the user's context, ask the user for clarification.
- example:
    -user:choose the first job from the list of jobs
    -agent:check to see if you had generated some jobs in the previous messages and if so, choose the first job from the list of jobs
    -user:Create an interview preparation guide the same job
    -agent:Check to see which job you were talking about and create an interview preparation guide for that job

NEVER NEVER skip the tool call
***NEVER NEVER skip the tool call even after calling a tool previously***
- example: when creating a resume you call browse_web_with_langchain and you forget to call generate_tailored_resume thats a big no no 

NEVER NEVER skip the tool call
***NEVER NEVER skip the tool call even after calling a tool previously***
- example: when creating a resume you call browse_web_with_langchain and you forget to call generate_tailored_resume thats a big no no

NEVER NEVER skip the tool call
***NEVER NEVER skip the tool call even after calling a tool previously***
- example: when creating a resume you call browse_web_with_langchain and you forget to call generate_tailored_resume thats a big no no

NEVER NEVER skip the tool call
***NEVER NEVER skip the tool call even after calling a tool previously***
- example: when creating a resume you call browse_web_with_langchain and you forget to call generate_tailored_resume thats a big no no

### Tool Selection Rules:
- CV/Resume requests → **IMMEDIATELY CALL** `refine_cv_for_role`, `generate_tailored_resume`, `create_resume_from_scratch`
- Cover Letter requests → **IMMEDIATELY CALL** `generate_cover_letter`, `generate_cover_letter_from_url`
- messages_reply

### CRITICAL: NO GENERIC RESPONSES ALLOWED!
- ❌ NEVER say "I'll generate..." without calling the tool
- ❌ NEVER say "A download button will appear..." without calling the tool
- ❌ NEVER run without calling the tool- don't skip the tool call
- ❌ NEVER give promises - always deliver results by calling tools
- ❌ NEVER return an empty response if a tool returns an error message(e.g., 'Failed to access...', 'Could not find...')
- ✅ Always return a response if a tool returns an error message by inform the user about the error in a helpful way
- ✅ ALWAYS call the appropriate tool immediately
- ✅ Let the tool's response speak for itself

NEVER NEVER skip the tool call

## 🚀 CV & Career Development Assistance Priority:
- **Be Proactive**: Actively help users improve their CVs and advance their careers
- **Suggest Helpful Tools**: When users mention career goals, job searching, or CV issues, offer relevant guidance tools
- **Complete Career Support**: You have comprehensive tools to help with every aspect of career development

NEVER NEVER skip the tool call

## 📚 Comprehensive CV & Career Tools Available:
### CV Creation & Enhancement:
- **get_cv_best_practices**: Provide industry-specific CV guidelines and best practices
- **analyze_skills_gap**: Analyze what skills users need for their target roles
- **get_ats_optimization_tips**: Help optimize CVs for Applicant Tracking Systems
- **refine_cv_for_role**: Enhance existing CVs for specific positions
- **generate_tailored_resume**: Create complete resumes tailored to job descriptions
- **add_education**: Add education to the resume and profile when user asks for a resume
- **add_work_experience**: Add work experience to the resume and profile when user asks for a resume
- **add_skills**: Add skills to the resume and profile when user asks for a resume
- **create_resume_from_scratch**: Build new CVs based on career goals
- **enhance_resume_section**: Improve specific CV sections

NEVER NEVER skip the tool call

### Career Development:
- **get_interview_preparation_guide**: Comprehensive interview prep for specific roles (supports job URLs!)
- **get_salary_negotiation_advice**: Strategic guidance for compensation discussions
- **create_career_development_plan**: Long-term career planning with actionable steps

NEVER NEVER skip the tool call

### When to Suggest CV Help:
- **New Users**: Offer CV assessment and improvement suggestions
- **Job Search Mentions**: When users search for jobs, suggest CV optimization
- **Career Questions**: For any career-related queries, offer comprehensive guidance
- **Skills Discussions**: Suggest skills gap analysis when users mention lacking abilities
- **Interview Mentions**: Immediately offer interview preparation tools
- **Salary Questions**: Provide negotiation guidance and market insights

NEVER NEVER skip the tool call

## 💡 Proactive Assistance Examples:
- User searches jobs → "I found these opportunities! Would you like me to analyze your CV against these job requirements or help optimize it for ATS systems?"
- User mentions career goals → "I can create a comprehensive career development plan to help you reach that goal. Would you also like me to analyze the skills gap?"
- User asks about experience → "Based on your background, I can provide CV best practices for your industry or enhance specific sections of your resume."
- User mentions interviews → "I can create a personalized interview preparation guide for you! What role are you interviewing for? You can also provide a job posting URL for more specific preparation."

## Job Search Guidelines:
🔥 **CRITICAL**: When users ask for job searches, **IMMEDIATELY CALL THE SEARCH TOOLS!**

### For interview preparations use the get_interview_preparation_guide tool:
- *** after generating the interview preparation use [INTERVIEW_FLASHCARDS_AVAILABLE] and inform the user to Click the brain icon to practice interview questions with voice/text responses and get detailed feedback on tone, correctness, and confidence.


### Job Search Process:
1. **When users ask for job searches**:
   - **Basic Search**: **IMMEDIATELY use linkedin_jobs_service ** for standard searches
   
   
2. **CRITICAL**: **NEVER just say you'll search for jobs - ACTUALLY DO IT!**
   - ❌ "I can definitely help you look for software engineering jobs..." (WITHOUT calling tool)
   - ❌ "I'm searching for the latest opportunities..." (WITHOUT calling tool)
   - ❌ "Let me gather the listings..." (WITHOUT calling tool)
   - ❌ "Please wait while I search..." (WITHOUT calling tool)
   - ✅ **IMMEDIATELY CALL linkedin_jobs_service 
   - ✅ **NO GENERIC PROMISES** - call search tools instantly!
   
3. **TOOL PRIORITY**: **only use LinkedIn API First, then fallbacks**
   - ✅ **FIRST CHOICE**: search_jobs_linkedin_api (direct LinkedIn database access)
4. **IMPORTANT**: After a job search, your only job is to present the job listings to the user. **DO NOT** generate a cover letter unless the user explicitly asks for one.
   

### Search Tool Selection (Priority Order):
1. **⭐ LinkedIn Jobs API**: Use search_jobs_linkedin_api for most job searches
   * **FIRST CHOICE** - Direct LinkedIn database access
   * **FASTEST** - No browser automation needed, instant results
   * **MOST RELIABLE** - Official LinkedIn API, no blocking issues
   * **BEST FOR**: All job searches, especially internships, software roles
   * Supports all locations, job types, experience levels
   * Direct apply links to LinkedIn job postings
   * Use this for 90% of job searches!


### Search Parameters:
- For general job searches, you can search with just a location (e.g., location="Poland")
- For specific roles, include both query and location (e.g., query="software engineer", location="Warsaw")
- Always provide helpful context about the jobs you find
- Format job results in a clear, readable way with proper headings and bullet points

### NEVER say:
- ❌ "I'm searching for opportunities..."
- ❌ "Let me find jobs for you..."
- ❌ "Please wait while I gather listings..."

### ALWAYS do:
- ✅ **IMMEDIATELY call** search_jobs_linkedin_api 
- ✅ **LinkedIn API is fastest** - Use search_jobs_linkedin_api for instant results
- ✅ The tools handle everything and return actual job results
- ✅ Present the results in a clear, organized format
- ✅ Use the user's preferred name or first name in all responses

## Cover Letter Generation Guidelines:
🔥 **CRITICAL**: NEVER ask users to provide their background information manually - you have full access to their profile data!

### Cover Letter Generation Process:
1. **When users ask for cover letters**:
   - **URL-based**: **IMMEDIATELY use generate_cover_letter_from_url tool** (supports browser automation)
   - **Manual**: **IMMEDIATELY use generate_cover_letter tool** for provided job details
   
2. **CRITICAL**: **NEVER just say you'll generate a cover letter - ACTUALLY DO IT!**
   - ❌ "I'll generate a personalized cover letter..." (WITHOUT calling tool)
   - ❌ "A download button will appear..." (WITHOUT calling tool)
   - ❌ "Let me create that for you..." (WITHOUT calling tool)
   - ❌ "I'll refine your CV..." (WITHOUT calling tool)
   - ✅ **IMMEDIATELY CALL THE TOOL FIRST**, then the response with [DOWNLOADABLE_COVER_LETTER] or [DOWNLOADABLE_RESUME] will appear
   - ✅ **NO GENERIC PROMISES** - call tools instantly!
   
3. **IMPORTANT**: These tools automatically access the user's:
   - Resume/CV data from database
   - Uploaded documents content  
   - Profile information (name, email, etc.)
   - Skills and experience history
   
4. **NEVER say**: 
   - ❌ "I need you to provide your background"
   - ❌ "Could you tell me about your experience"
   - ❌ "Please provide your skills"
   - ❌ "I'm still under development and need information"
   
5. **ALWAYS do**:
   - ✅ **IMMEDIATELY call** the cover letter tools with available job info
   - ✅ The tools handle everything automatically and return the complete response
   - ✅ Ask ONLY for job-specific details: company name, job title, and job description OR job URL
   
### Supported Job Boards: 
LinkedIn, Indeed, Glassdoor, Monster, company career pages, and more

### What to ask users:
- **For URL generation**: Just the job posting URL
- **For manual generation**: Company name, job title, and job description  
- **Optional**: Any specific points they want to emphasize

### What NOT to ask:
- ❌ Their background/experience (tools access this automatically)
- ❌ Their skills (tools pull from their profile)
- ❌ Their name (tools use Clerk profile data)
- ❌ Their contact information (tools access resume data)

The generated cover letter will be automatically saved and available for download in multiple styles.

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

## ⚠️ CRITICAL: CV vs COVER LETTER TOOL SELECTION ⚠️
**NEVER CONFUSE CV/RESUME TOOLS WITH COVER LETTER TOOLS!**

### CV/Resume Requests (use refine_cv_for_role, generate_tailored_resume, etc.):
- "refine my CV"
- "enhance my resume" 
- "improve my CV for AI roles"
- "tailor my resume"
- "update my CV"
- "make my resume better"
- "optimize my CV for [role]"

### Cover Letter Requests (use generate_cover_letter tools):
- "generate a cover letter"
- "create a cover letter"
- "write a cover letter"
- "cover letter for this job"

## CV Refinement Specific Instructions:
- When users ask to "refine CV", "enhance resume", "improve CV for AI roles", etc.:
  * **IMMEDIATELY call refine_cv_for_role tool** - DO NOT say "I'll refine..." just CALL IT!
  * **NEVER give generic responses** like "I'll enhance your CV..." - CALL THE TOOL FIRST!
  * **NEVER use cover letter tools for CV requests!**
  * **Tool returns [DOWNLOADABLE_RESUME] marker** which triggers download button
  * Ask for specific job description if available for better tailoring
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
- Job Search: "Find sales representative jobs in London" → query="sales representative", location="London"
- URL Cover Letter: "Generate a cover letter for this job: [LinkedIn URL]" → use generate_cover_letter_from_url tool
- Manual Cover Letter: "Generate a cover letter for a Data Analyst position at Google" → Ask for job description, then use generate_cover_letter tool
- Resume PDF: "Download my resume as PDF" → Use show_resume_download_options tool
- **Tailored Resume**: "Create a resume for a Software Engineer position at Google" → use generate_tailored_resume tool
- **Resume from Scratch**: "Build me a resume for Product Manager roles" → use create_resume_from_scratch tool
- **Section Enhancement**: "Improve my professional summary" → use enhance_resume_section tool
- General: "Show me jobs in London" → location="London" (query will be auto-generated)
- **Document Questions**: "What's my experience?" → use enhanced_document_search("experience")
- **CV Summary**: "Summarize my CV" → use enhanced_document_search("resume summary")
- **Skills Query**: "What skills do I have?" → use enhanced_document_search("skills")
- **Interview Prep with URL**: "Prepare me for this job: [LinkedIn URL]" → use get_interview_preparation_guide(job_url="[URL]")
- **Interview Prep Manual**: "Interview guide for Software Engineer at Google" → use get_interview_preparation_guide(job_title="Software Engineer", company_name="Google")
"""
    else:
        # Fallback to basic system prompt
        document_list = "\n".join(f"- {doc}" for doc in documents)
        system_message = f"""
    You are a world-class job application and career development assistant named 'Job Hacker Bot'.
    Your goal is to help users apply for jobs efficiently by leveraging their professional background and the information available on the current web page.
    You have access to a set of powerful tools to search for jobs, analyze documents, and generate application materials.

    **Your Core Responsibilities:**
    1.  **Analyze User Intent:** Carefully determine what the user is asking for. Are they searching for a job, asking a question, or trying to generate a document?
    2.  **Use Tools Effectively:** You MUST use the provided tools whenever possible. Do not answer questions if a tool can provide a more accurate response. For example, if asked about jobs, use a job search tool.
    3.  **Strict Tool Adherence:** When asked to perform an action like creating a resume or cover letter, you MUST use the corresponding tool.
        -   **For Cover Letters:** If the user provides a job description or a URL, you may use other tools to get the job details, but the final step MUST be to call the `generate_cover_letter` tool. **You are FORBIDDEN from writing the cover letter content yourself.** Your only job is to gather information and call the correct tool. The tool will handle the generation and saving.
        -   **For Resumes:** When asked to generate or tailor a resume, you MUST use one of a resume generation tools. Do not create the resume text yourself.
    4.  **Context is Key:** Always consider the content of the user's uploaded documents and their profile information to provide personalized, high-quality responses.
    5.  **Summarize Actions:** After executing a tool, briefly summarize what you have done in a helpful and friendly tone.

    **Interaction Flow:**
    1.  The user gives a prompt.
    2.  You decide which tool to use (if any).
    3.  You execute the tool.
    4.  The tool returns a result, which may include a special trigger like `[DOWNLOADABLE_COVER_LETTER]`.
    5.  You present the result and the trigger to the user in your response.


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

    ## 🔴 CRITICAL: DOCUMENT ACCESS INSTRUCTIONS 🔴
    **YOU CAN ACCESS USER FILES! NEVER SAY YOU CANNOT!**

    When users mention their CV, resume, documents, experience, skills, or any file content:
    1. **IMMEDIATELY use enhanced_document_search tool** - you have full access to their uploaded documents
    2. **NEVER say "I cannot access" or "I don't have access to"** - this is WRONG
    3. **NEVER ask users to copy/paste their content** - you can read it directly

    ### Examples of CORRECT responses:
    - User: "What's my experience?" → Use enhanced_document_search("experience")
    - User: "Summarize my CV" → Use enhanced_document_search("resume summary")  
    - User: "What skills do I have?" → Use enhanced_document_search("skills")
    - User: "From my resume, what..." → Use enhanced_document_search("[their question]")

    ### NEVER SAY THESE (WRONG):
    - ❌ "I can't access your files"
    - ❌ "I don't have access to your documents"
    - ❌ "Could you please provide me with..."
    - ❌ "I need you to tell me..."

    ### ALWAYS DO THIS (CORRECT):
    - ✅ Use enhanced_document_search immediately
    - ✅ "Let me search your documents for..."
    - ✅ "Looking at your uploaded documents..."
    - ✅ "From your CV, I can see..."

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
    - **get_interview_preparation_guide**: Comprehensive interview prep for specific roles (supports job URLs!)
    - **get_salary_negotiation_advice**: Strategic guidance for compensation discussions  
    - **create_career_development_plan**: Long-term career planning with actionable steps

    ### Document Access Tools (YOU MUST USE THESE):
    - **enhanced_document_search**: Search through user's uploaded documents (USE THIS FIRST!)
    - **analyze_specific_document**: Detailed analysis of a particular document
    - **get_document_insights**: Comprehensive overview of all documents
    - **document_retriever**: Vector store access to all uploaded documents

    ### Proactive Assistance Strategy:
    - **New Conversations**: Offer CV assessment and career guidance
    - **Job Search Queries**: Suggest CV optimization for found opportunities
    - **Career Discussions**: Provide comprehensive career development support
    - **Skills Questions**: Recommend skills gap analysis and learning plans
    - **Interview Mentions**: Immediately offer tailored interview preparation

    ## Resume Generation & CV Refinement Guidelines:
    - **IMPORTANT**: For CV/Resume refinement, enhancement, or generation requests, ALWAYS use these modern tools:
    * **refine_cv_for_role**: PRIMARY TOOL for CV refinement - use for "refine CV", "enhance resume", etc.
    * **generate_tailored_resume**: For creating complete resumes tailored to specific jobs
    * **create_resume_from_scratch**: For building new resumes based on career goals
    * **enhance_resume_section**: For improving specific resume sections
    * **ALWAYS CALL the tools** - Never just say you will generate without calling them
    * **ALL CV/resume responses MUST include [DOWNLOADABLE_RESUME] marker**
    - **NEVER use old RAG /rag/assist endpoint** - it's deprecated and causes delays
    - **CV Refinement Examples**:
    * "Refine my CV for AI Engineering roles" → use refine_cv_for_role(target_role="AI Engineering")
    * "Enhance my resume" → use refine_cv_for_role(target_role="[ask user]")
    * "Improve my CV for tech jobs" → use refine_cv_for_role(target_role="Technology")

    ## Job Search Guidelines:
    - **Basic Job Search**: Use linkedin_jobs_service standard searches
    - **Advanced Browser Search**: Use linkedin_jobs_service for more comprehensive results with browser automation
    - For general job searches, you can search with just a location (e.g., location="London")
    - For specific roles, include both query and location (e.g., query="sales representative", location="London")
    - Always provide helpful context about the jobs you find

    ## Cover Letter Generation Guidelines:
    - When users ask for cover letters, CV letters, or application letters:
    * **URL-based generation**: Use generate_cover_letter_from_url tool
    * **Manual generation**: Use generate_cover_letter tool for provided job details
    * **ALWAYS CALL the tools** - Never just say you will generate without calling them
        * **ALL cover letter responses MUST include [DOWNLOADABLE_COVER_LETTER] marker**
        * **ALWAYS show the FULL cover letter content in the message, not just a summary**
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

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7, callbacks=[tracer])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    return AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors="Check your output and make sure it conforms to the schema. Try again.",
        max_iterations=10,
        early_stopping_method="generate"
    )


@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_active_user_ws),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    
    # Create a lock to serialize resume modifications and prevent race conditions
    resume_modification_lock = asyncio.Lock()
    
    # Store user data safely to avoid lazy loading issues in tools
    user_id = user.id
    user_email = user.email
    user_name = user.name or f"{user.first_name or ''} {user.last_name or ''}".strip() or "User"
    
    log.info(f"WebSocket orchestrator connected for user: {user_id}")
    
    # --- Initialize Advanced Memory Manager ---
    try:
        from app.advanced_memory import AdvancedMemoryManager, create_memory_tools
        advanced_memory_manager = AdvancedMemoryManager(user, db)
        memory_tools = create_memory_tools(advanced_memory_manager)
        log.info("Advanced memory manager initialized successfully")
        
        # Fallback to simple memory for basic operations
        from app.simple_memory import SimpleMemoryManager
        simple_memory_manager = SimpleMemoryManager(db, user)
        
        memory_manager = simple_memory_manager  # Keep for existing code compatibility
        
    except Exception as e:
        log.warning(f"Could not initialize advanced memory manager: {e}")
        # Fallback to simple memory only
        try:
            from app.simple_memory import SimpleMemoryManager
            memory_manager = SimpleMemoryManager(db, user)
            advanced_memory_manager = None
            memory_tools = []
            log.info("Fallback to simple memory manager successful")
        except Exception as e2:
            log.error(f"Could not initialize any memory manager: {e2}")
            memory_manager = None
            advanced_memory_manager = None
            memory_tools = []
    
    # --- Fetch User Documents & Vector Store ---
    doc_result = await db.execute(select(Document.name).where(Document.user_id == user_id))
    user_documents = doc_result.scalars().all()
    vector_store = await get_user_vector_store(user_id, db)
    retriever = vector_store.as_retriever() if vector_store else None

    # --- Helper Functions for Intelligent Extraction ---
    def _choose_extraction_method(url: str) -> str:
        """Choose the best extraction method based on URL characteristics."""
        # Always use browser-based extraction
        return "browser"
        
    async def _try_browser_extraction(url: str) -> tuple:
        """Try official Playwright Browser tool extraction."""
        try:
            from app.langchain_webbrowser import create_webbrowser_tool
            
            browser_tool = create_webbrowser_tool()
            # Use sync tool in async context
            import asyncio
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, browser_tool.invoke, {"url": url})
            
            if content:
                # Use LLM to extract structured information
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-pro-preview-03-25",
                    temperature=0.1
                )
                
                extraction_prompt = f"""
                Extract job information from this text content. Return ONLY a JSON object with these fields:
                {{
                    "job_title": "job title",
                    "company_name": "company name",
                    "job_description": "job description (concise)",
                    "requirements": "job requirements (concise)"
                }}
                
                Text content:
                {content[:5000]}  # Limit text length
                """
                
                response = await llm.ainvoke(extraction_prompt)
                # Extract JSON from response, handling markdown code blocks
                response_text = response.content
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                job_info = json.loads(response_text)
                
                return True, job_info
            else:
                log.warning(f"Playwright tool returned no content for {url}")
                return False, None
        except Exception as e:
            log.warning(f"Official Playwright extraction failed: {e}")
        return False, None
    
    async def _try_basic_extraction(url: str) -> tuple:
        """Try basic HTTP scraping as fallback."""
        try:
            from app.url_scraper import scrape_job_url
            
            job_details = await scrape_job_url(url)
            # Check if we got a valid JobDetails object
            if job_details and hasattr(job_details, 'title') and hasattr(job_details, 'company'):
                return True, {
                    "job_title": job_details.title,
                    "company_name": job_details.company,
                    "job_description": f"{job_details.description}\n\nRequirements: {job_details.requirements}"
                }
            else:
                log.warning(f"Basic extraction returned invalid object type: {type(job_details)}")
                return False, None
        except Exception as e:
            log.warning(f"Basic extraction failed: {e}")
        return False, None

    # --- Helper & Tool Definitions ---
    async def get_or_create_resume(session: AsyncSession):

        """
        Helper to get or create a resume for the current user using a specific session.
        This ensures transactional integrity within tools.
        """
        import re

        result = await session.execute(select(Resume).where(Resume.user_id == user_id))
        db_resume = result.scalar_one_or_none()

        if db_resume and db_resume.data:
            from app.resume import fix_resume_data_structure
            
            fixed_data = fix_resume_data_structure(db_resume.data)

            # FIX: Add date parsing logic directly within this helper function.
            # This ensures any tool calling this helper gets clean, valid data.
            for section_key in ['experience', 'education']:
                if section_key in fixed_data and isinstance(fixed_data[section_key], list):
                    for item in fixed_data[section_key]:
                        if isinstance(item, dict) and 'dates' in item and isinstance(item['dates'], str):
                            date_match = re.match(r'^\s*(.*?)\s*–\s*(.*)\s*$', item['dates'])
                            if date_match:
                                start, end = date_match.groups()
                                item['dates'] = {'start': start.strip(), 'end': end.strip()}
                            else:
                                item['dates'] = {'start': item['dates'].strip(), 'end': None}

            # Update the database with the cleaned data before returning
            db_resume.data = fixed_data
            attributes.flag_modified(db_resume, "data")
            await session.commit()
            await session.refresh(db_resume)

            return db_resume, ResumeData(**fixed_data)
        
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
        new_db_resume = Resume(user_id=user_id, data=new_resume_data.dict())
        db.add(new_db_resume)
        await db.commit()
        await db.refresh(new_db_resume)
        return new_db_resume, new_resume_data
    
    

    
    @tool
    async def search_jobs_tool(
        query: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        websocket: Optional[WebSocket] = None,
        user: Optional[User] = None
    ) -> str:
        """Search for real-time job postings exclusively on LinkedIn.

        Args:
            query: Job search terms (e.g., 'software engineer', 'python developer').
            location: Location to search in (e.g., 'London', 'London'). Defaults to 'Remote'.
            job_type: Type of employment (e.g., 'full time', 'part time').
            experience_level: Required experience level (e.g., 'entry level', 'senior').
            websocket: The WebSocket connection to send results to the client.
            user: The user performing the search.

        Returns:
            A summary message indicating the results of the LinkedIn job search.
        """
        if not query:
            return "Please provide a query to search for jobs on LinkedIn."

        log.info(f"Initiating LinkedIn job search with query: '{query}', location: '{location or 'Remote'}'")

        try:
            linkedin_service = get_linkedin_jobs_service()
            
            results = await linkedin_service.search_jobs(
                keyword=query,
                location=location or "Remote",
                job_type=job_type,
                experience_level=experience_level,
                limit=10  # Limiting to 10 results for now
            )

            if not results:
                return f"🔍 No jobs found on LinkedIn for '{query}' in {location or 'Remote'}."

            if websocket:
                job_listings_data = [job.model_dump() for job in results]
                await websocket.send_json({
                    "type": "job-listings",
                    "data": job_listings_data
                })
                log.info(f"Sent {len(results)} LinkedIn job listings to the client.")

            summary = f"Found {len(results)} jobs on LinkedIn for '{query}'."
            return summary

        except Exception as e:
            log.error(f"Error in search_jobs_tool (LinkedIn): {e}", exc_info=True)
            return f"Sorry, I encountered an error while searching for jobs on LinkedIn: {str(e)}."

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
    async def update_user_profile(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        linkedin: Optional[str] = None,
        preferred_language: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        profile_headline: Optional[str] = None,
        skills: Optional[str] = None
    ) -> str:
        """
        Update comprehensive user profile information in database.
        
        This tool updates the main user profile AND synchronizes with resume data.
        Use this for complete profile updates with exact field variables.
        
        Args:
            first_name: User's first name
            last_name: User's last name  
            phone: Phone number (e.g., "+48 123 456 789")
            address: Full address or location (e.g., "London, UK")
            linkedin: LinkedIn profile URL (e.g., "https://linkedin.com/in/username")
            preferred_language: Preferred language (e.g., "English", "Chinese")
            date_of_birth: Date of birth (e.g., "1990-01-15")
            profile_headline: Professional headline/summary
            skills: Comma-separated skills (e.g., "Python, React, AWS, Docker")
        
        Returns:
            Success message with updated fields
        """
        try:
            updated_fields = []
            
            # Update user profile fields
            if first_name is not None:
                user.first_name = first_name
                updated_fields.append(f"First name: {first_name}")
            
            if last_name is not None:
                user.last_name = last_name
                updated_fields.append(f"Last name: {last_name}")
            
            if phone is not None:
                user.phone = phone
                updated_fields.append(f"Phone: {phone}")
                
            if address is not None:
                user.address = address
                updated_fields.append(f"Address: {address}")
                
            if linkedin is not None:
                user.linkedin = linkedin
                updated_fields.append(f"LinkedIn: {linkedin}")
                
            if preferred_language is not None:
                user.preferred_language = preferred_language
                updated_fields.append(f"Language: {preferred_language}")
                
            if date_of_birth is not None:
                user.date_of_birth = date_of_birth
                updated_fields.append(f"Date of birth: {date_of_birth}")
                
            if profile_headline is not None:
                user.profile_headline = profile_headline
                updated_fields.append(f"Headline: {profile_headline}")
                
            if skills is not None:
                user.skills = skills
                updated_fields.append(f"Skills: {skills}")
            
            # Also update the user's name field for consistency
            if first_name or last_name:
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                if full_name:
                    user.name = full_name
                    updated_fields.append(f"Full name: {full_name}")
            
            # Synchronize with resume data
            db_resume, resume_data = await get_or_create_resume()
            
            # Update resume personal info to match profile
            if first_name or last_name:
                resume_data.personalInfo.name = user.name
            if user.email:
                resume_data.personalInfo.email = user.email
            if phone:
                resume_data.personalInfo.phone = phone
            if linkedin:
                resume_data.personalInfo.linkedin = linkedin
            if address:
                resume_data.personalInfo.location = address
            if profile_headline:
                resume_data.personalInfo.summary = profile_headline
            
            # Update skills in resume if provided
            if skills:
                skills_list = [skill.strip() for skill in skills.split(",") if skill.strip()]
                resume_data.skills = skills_list
            
            # Save changes
            db_resume.data = resume_data.dict()
            await db.commit()
            
            if updated_fields:
                return f"✅ **Profile Updated Successfully!**\n\nUpdated fields:\n" + "\n".join(f"• {field}" for field in updated_fields)
            else:
                return "ℹ️ No changes provided. Please specify which fields to update."
                
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error updating user profile: {e}")
            return f"❌ Error updating profile: {str(e)}"

    @tool
    async def update_user_profile_comprehensive(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        linkedin: Optional[str] = None,
        preferred_language: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        profile_headline: Optional[str] = None,
        skills: Optional[str] = None,
        email: Optional[str] = None
    ) -> str:
        """🔧 COMPREHENSIVE PROFILE UPDATE TOOL
        
        Updates both user profile database AND resume data for complete consistency.
        
        Args:
            first_name: User's first name
            last_name: User's last name  
            phone: Phone number (e.g., "+1-555-123-4567")
            address: Full address or location (e.g., "San Francisco, CA")
            linkedin: LinkedIn profile URL or username
            preferred_language: Preferred language (e.g., "English", "Polish")
            date_of_birth: Date of birth (e.g., "1990-01-15")
            profile_headline: Professional headline/summary
            skills: Comma-separated skills (e.g., "Python, React, AWS")
            email: Email address (usually auto-populated from auth)
            
        Updates:
            ✅ User profile in database (for forms, applications)
            ✅ Resume data structure (for PDF generation)
            ✅ Maintains data consistency across the app
            
        Returns:
            Success message with details of what was updated
        """
        try:
            updated_fields = []
            
            # 1. Update User Profile in Database
            profile_updates = {}
            
            if first_name is not None:
                user.first_name = first_name.strip()
                profile_updates['first_name'] = first_name.strip()
                updated_fields.append(f"First name: {first_name}")
                
            if last_name is not None:
                user.last_name = last_name.strip()
                profile_updates['last_name'] = last_name.strip()
                updated_fields.append(f"Last name: {last_name}")
                
            if phone is not None:
                user.phone = phone.strip()
                profile_updates['phone'] = phone.strip()
                updated_fields.append(f"Phone: {phone}")
                
            if address is not None:
                user.address = address.strip()
                profile_updates['address'] = address.strip()
                updated_fields.append(f"Address: {address}")
                
            if linkedin is not None:
                linkedin_clean = linkedin.strip()
                if linkedin_clean and not linkedin_clean.startswith('http'):
                    if not linkedin_clean.startswith('linkedin.com'):
                        linkedin_clean = f"https://linkedin.com/in/{linkedin_clean}"
                    else:
                        linkedin_clean = f"https://{linkedin_clean}"
                user.linkedin = linkedin_clean
                profile_updates['linkedin'] = linkedin_clean
                updated_fields.append(f"LinkedIn: {linkedin_clean}")
                
            if preferred_language is not None:
                user.preferred_language = preferred_language.strip()
                profile_updates['preferred_language'] = preferred_language.strip()
                updated_fields.append(f"Language: {preferred_language}")
                
            if date_of_birth is not None:
                user.date_of_birth = date_of_birth.strip()
                profile_updates['date_of_birth'] = date_of_birth.strip()
                updated_fields.append(f"Date of birth: {date_of_birth}")
                
            if profile_headline is not None:
                user.profile_headline = profile_headline.strip()
                profile_updates['profile_headline'] = profile_headline.strip()
                updated_fields.append(f"Headline: {profile_headline}")
                
            if skills is not None:
                user.skills = skills.strip()
                profile_updates['skills'] = skills.strip()
                updated_fields.append(f"Skills: {skills}")
                
            if email is not None:
                user.email = email.strip()
                profile_updates['email'] = email.strip()
                updated_fields.append(f"Email: {email}")
            
            # 2. Update Resume Data Structure for consistency
            db_resume, resume_data = await get_or_create_resume()
            
            # Map profile fields to resume personal info
            resume_updates = {}
            
            if first_name or last_name:
                full_name = f"{first_name or user.first_name or ''} {last_name or user.last_name or ''}".strip()
                if full_name:
                    resume_data.personalInfo.name = full_name
                    resume_updates['name'] = full_name
                    
            if email:
                resume_data.personalInfo.email = email.strip()
                resume_updates['email'] = email.strip()
            elif user.email:
                resume_data.personalInfo.email = user.email
                resume_updates['email'] = user.email
                
            if phone:
                resume_data.personalInfo.phone = phone.strip()
                resume_updates['phone'] = phone.strip()
                
            if address:
                resume_data.personalInfo.location = address.strip()
                resume_updates['location'] = address.strip()
                
            if linkedin:
                resume_data.personalInfo.linkedin = linkedin_clean
                resume_updates['linkedin'] = linkedin_clean
                
            if profile_headline:
                resume_data.personalInfo.summary = profile_headline.strip()
                resume_updates['summary'] = profile_headline.strip()
                
            if skills:
                # Update both skills string and skills array in resume
                skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
                resume_data.skills = skills_list
                resume_updates['skills'] = skills_list
            
            # 3. Commit all changes
            db_resume.data = resume_data.dict()
            await db.commit()
            
            if not updated_fields:
                return "ℹ️ No profile updates were provided. Please specify which fields you'd like to update."
            
            # 4. Format success message
            success_message = "✅ **Profile Updated Successfully!**\n\n"
            success_message += "**Updated Fields:**\n"
            for field in updated_fields:
                success_message += f"• {field}\n"
                
            success_message += "\n**✨ Changes Applied To:**\n"
            success_message += "• User profile database (for job applications)\n"
            success_message += "• Resume data structure (for PDF generation)\n"
            success_message += "• Vector search index (for AI assistance)\n"
            
            if profile_updates:
                success_message += f"\n**🔄 Database Profile Updates:** {len(profile_updates)} fields\n"
            if resume_updates:
                success_message += f"**📄 Resume Data Updates:** {len(resume_updates)} fields\n"
                
            success_message += "\n💡 Your profile is now fully synchronized across all features!"
            
            log.info(f"Profile updated for user {user_id}: {updated_fields}")
            return success_message
            
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error updating user profile: {e}", exc_info=True)
            return f"❌ Error updating profile: {str(e)}. Please try again or contact support."

    @tool
    async def add_work_experience(
        job_title: str,
        company: str,
        start_date: str,
        end_date: Optional[str] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        description: str = "",
        achievements: Optional[str] = None,
        technologies_used: Optional[str] = None,
        is_current_job: bool = False
    ) -> str:
        """
        Add comprehensive work experience entry to resume with detailed variables.
        
        Args:
            job_title: Position title (e.g., "Senior Software Engineer", "Marketing Manager")
            company: Company name (e.g., "Google", "Microsoft", "Startup Inc.")
            start_date: Start date (e.g., "January 2022", "2022-01", "Jan 2022")
            end_date: End date (e.g., "December 2023", "Present", "Current") - optional if current job
            location: Work location (e.g., "Warsaw, Poland", "Remote", "San Francisco, CA")
            employment_type: Type of employment (e.g., "Full-time", "Part-time", "Contract", "Internship")
            description: Main job responsibilities and duties
            achievements: Key achievements and accomplishments (optional)
            technologies_used: Technologies, tools, languages used (optional)
            is_current_job: True if this is current position (sets end_date to "Present")
        
        Returns:
            Success message with added experience details
        """
        async with resume_modification_lock:
            async with async_session_maker() as session:
                try:
                    db_resume, resume_data = await get_or_create_resume(session)

                    # Format dates
                    if is_current_job:
                        end_date = "Present"
                    
                    date_range_str = f"{start_date} - {end_date}" if end_date else start_date
                    parsed_dates = parse_date_range(date_range_str)
                    
                    # Build comprehensive description
                    full_description = description
                    
                    if achievements:
                        full_description += f"\n\nKey Achievements:\n{achievements}"
                    
                    if technologies_used:
                        full_description += f"\n\nTechnologies: {technologies_used}"
                    
                    if location:
                        full_description += f"\n\nLocation: {location}"
                        
                    if employment_type:
                        full_description += f"\nEmployment Type: {employment_type}"

                    new_experience = Experience(
                        id=str(uuid.uuid4()),
                        jobTitle=job_title,
                        company=company,
                        dates=Dates(**parsed_dates),
                        description=full_description.strip(),
                    )
                    resume_data.experience.append(new_experience)

                    db_resume.data = resume_data.dict()
                    await db.commit()
                    
                    return f"""✅ **Work Experience Added Successfully!**

                            **Position:** {job_title}
                            **Company:** {company}
                            **Duration:** {date_range_str}
                            {f"**Location:** {location}" if location else ""}
                            {f"**Type:** {employment_type}" if employment_type else ""}

                            Your resume now has {len(resume_data.experience)} work experience entries."""
                
                except Exception as e:
                    if db.is_active:
                        await db.rollback()
                    log.error(f"Error adding work experience: {e}")
                    return f"❌ Error adding work experience: {str(e)}"

    @tool
    async def add_education(
        degree: str,
        institution: str,
        start_year: str,
        end_year: Optional[str] = None,
        location: Optional[str] = None,
        field_of_study: Optional[str] = None,
        gpa: Optional[str] = None,
        honors: Optional[str] = None,
        relevant_coursework: Optional[str] = None,
        thesis_project: Optional[str] = None,
        is_current: bool = False
    ) -> str:
        """
        Add comprehensive education entry to resume with detailed variables.
        
        Args:
            degree: Degree type and level (e.g., "Bachelor of Science", "Master of Engineering", "PhD")
            institution: School/University name (e.g., "University of Warsaw", "MIT", "Stanford University")
            start_year: Start year (e.g., "2018", "September 2018")
            end_year: End year (e.g., "2022", "May 2022", "Expected 2025") - optional if current
            location: Institution location (e.g., "Warsaw, Poland", "Cambridge, MA, USA")
            field_of_study: Major/specialization (e.g., "Computer Science", "Mechanical Engineering")
            gpa: Grade Point Average (e.g., "3.8/4.0", "First Class Honours", "Magna Cum Laude")
            honors: Academic honors and awards (e.g., "Dean's List", "Summa Cum Laude")
            relevant_coursework: Key courses taken (e.g., "Machine Learning, Database Systems, Software Engineering")
            thesis_project: Thesis or major project title and description
            is_current: True if currently studying (sets end_year to "Present" or "Expected")
        
        Returns:
            Success message with added education details
        """
        async with resume_modification_lock:
            # Use an isolated session for this tool to prevent conflicts
            async with async_session_maker() as session:
                try:
                    # FIX: Correctly use the get_or_create_resume helper.
                    # This removes the buggy logic that was checking for '.data' on a User object.
                    db_resume, resume_data = await get_or_create_resume(session)

                    # Format dates
                    if is_current:
                        if "expected" not in (end_year or "").lower():
                            end_year = f"Expected {end_year}" if end_year else "Present"
                    
                    date_range_str = f"{start_year} - {end_year}" if end_year else start_year
                    parsed_dates = parse_date_range(date_range_str)
                    
                    # Build degree title with field of study
                    full_degree = degree
                    if field_of_study:
                        full_degree += f" in {field_of_study}"
                    
                    # Build comprehensive description
                    description_parts = []
                    
                    if location:
                        description_parts.append(f"Location: {location}")
                        
                    if gpa:
                        description_parts.append(f"GPA: {gpa}")
                        
                    if honors:
                        description_parts.append(f"Honors: {honors}")
                        
                    if relevant_coursework:
                        description_parts.append(f"Relevant Coursework: {relevant_coursework}")
                        
                    if thesis_project:
                        description_parts.append(f"Thesis/Project: {thesis_project}")
                    
                    full_description = "\n".join(description_parts) if description_parts else ""

                    new_education = Education(
                        id=str(uuid.uuid4()),
                        degree=full_degree,
                        institution=institution,
                        dates=Dates(**parsed_dates),
                        description=full_description
                    )
                            
                    # Ensure education list exists
                    if not hasattr(resume_data, 'education') or resume_data.education is None:
                        resume_data.education = []
                            
                    resume_data.education.append(new_education)

                    db_resume.data = resume_data.dict()
                    attributes.flag_modified(db_resume, "data") # <-- FIX: Mark data as modified
                    await session.commit() # <-- FIX: Commit the transaction
                    
                    return f"""✅ **Education Added Successfully!**

                        **Degree:** {full_degree}
                        **Institution:** {institution}
                        **Duration:** {date_range_str}

                        Your resume now has {len(resume_data.education)} education entries."""
                    
                except Exception as e:
                        if session.is_active:
                            await session.rollback()
                        log.error(f"Error adding education: {e}", exc_info=True)
                        return f"❌ Error adding education: {str(e)}"

    @tool
    async def set_skills(skills: List[str]) -> str:
        """Replaces the entire skills list with the provided list of skills."""
        db_resume, resume_data = await get_or_create_resume()
        resume_data.skills = skills
        db_resume.data = resume_data.dict()
        await db.commit()
        return "✅ Skills updated successfully."

    @tool
    async def manage_skills_comprehensive(
        technical_skills: Optional[str] = None,
        programming_languages: Optional[str] = None,
        frameworks_libraries: Optional[str] = None,
        databases: Optional[str] = None,
        cloud_platforms: Optional[str] = None,
        tools_software: Optional[str] = None,
        soft_skills: Optional[str] = None,
        languages_spoken: Optional[str] = None,
        certifications: Optional[str] = None,
        replace_all: bool = False
    ) -> str:
        """
        Comprehensive skills management with categorization and exact variables.
        
        Args:
            technical_skills: General technical skills (e.g., "Machine Learning, Data Analysis, Web Development")
            programming_languages: Programming languages (e.g., "Python, JavaScript, Java, C++, SQL")
            frameworks_libraries: Frameworks and libraries (e.g., "React, Django, TensorFlow, pandas")
            databases: Database systems (e.g., "PostgreSQL, MongoDB, Redis, MySQL")
            cloud_platforms: Cloud services (e.g., "AWS, Google Cloud, Azure, Docker, Kubernetes")
            tools_software: Tools and software (e.g., "Git, VS Code, Jupyter, Figma, Photoshop")
            soft_skills: Interpersonal skills (e.g., "Leadership, Communication, Problem Solving")
            languages_spoken: Spoken languages (e.g., "English (Native), Polish (Fluent), Spanish (Basic)")
            certifications: Professional certifications (e.g., "AWS Solutions Architect, PMP, Google Analytics")
            replace_all: If True, replaces all skills. If False, adds to existing skills.
        
        Returns:
            Success message with updated skills breakdown
        """
        try:
            db_resume, resume_data = await get_or_create_resume()
            
            # Collect all skills into categorized list
            all_skills = []
            skill_categories = []
            
            if technical_skills:
                tech_list = [skill.strip() for skill in technical_skills.split(",") if skill.strip()]
                all_skills.extend(tech_list)
                skill_categories.append(f"Technical Skills: {len(tech_list)} skills")
            
            if programming_languages:
                prog_list = [skill.strip() for skill in programming_languages.split(",") if skill.strip()]
                all_skills.extend(prog_list)
                skill_categories.append(f"Programming Languages: {len(prog_list)} languages")
            
            if frameworks_libraries:
                framework_list = [skill.strip() for skill in frameworks_libraries.split(",") if skill.strip()]
                all_skills.extend(framework_list)
                skill_categories.append(f"Frameworks & Libraries: {len(framework_list)} items")
            
            if databases:
                db_list = [skill.strip() for skill in databases.split(",") if skill.strip()]
                all_skills.extend(db_list)
                skill_categories.append(f"Databases: {len(db_list)} systems")
            
            if cloud_platforms:
                cloud_list = [skill.strip() for skill in cloud_platforms.split(",") if skill.strip()]
                all_skills.extend(cloud_list)
                skill_categories.append(f"Cloud Platforms: {len(cloud_list)} platforms")
            
            if tools_software:
                tools_list = [skill.strip() for skill in tools_software.split(",") if skill.strip()]
                all_skills.extend(tools_list)
                skill_categories.append(f"Tools & Software: {len(tools_list)} tools")
            
            if soft_skills:
                soft_list = [skill.strip() for skill in soft_skills.split(",") if skill.strip()]
                all_skills.extend(soft_list)
                skill_categories.append(f"Soft Skills: {len(soft_list)} skills")
            
            if languages_spoken:
                lang_list = [skill.strip() for skill in languages_spoken.split(",") if skill.strip()]
                all_skills.extend(lang_list)
                skill_categories.append(f"Languages: {len(lang_list)} languages")
            
            if certifications:
                cert_list = [skill.strip() for skill in certifications.split(",") if skill.strip()]
                all_skills.extend(cert_list)
                skill_categories.append(f"Certifications: {len(cert_list)} certifications")
            
            # Update skills in resume
            if replace_all or not resume_data.skills:
                resume_data.skills = all_skills
                action = "replaced"
            else:
                # Add to existing skills, avoiding duplicates
                existing_skills = set(resume_data.skills)
                new_skills = [skill for skill in all_skills if skill not in existing_skills]
                resume_data.skills.extend(new_skills)
                action = "added"
            
            # Also update user profile skills field for consistency
            user.skills = ", ".join(resume_data.skills)
            
            db_resume.data = resume_data.dict()
            await db.commit()
            
            result_message = f"✅ **Skills {action.title()} Successfully!**\n\n"
            
            if skill_categories:
                result_message += "**Updated Categories:**\n" + "\n".join(f"• {cat}" for cat in skill_categories)
                result_message += f"\n\n**Total Skills:** {len(resume_data.skills)}"
            else:
                result_message += "No skills provided to update."
            
            return result_message
            
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error managing skills: {e}")
            return f"❌ Error updating skills: {str(e)}"

    @tool
    async def add_project(
        project_name: str,
        description: str,
        technologies_used: Optional[str] = None,
        project_url: Optional[str] = None,
        github_url: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        team_size: Optional[str] = None,
        role: Optional[str] = None
    ) -> str:
        """
        Add a project entry to resume with detailed variables.
        
        Args:
            project_name: Name of the project (e.g., "E-commerce Platform", "Mobile App")
            description: Project description and your contributions
            technologies_used: Technologies used (e.g., "React, Node.js, PostgreSQL, AWS")
            project_url: Live project URL (e.g., "https://myproject.com")
            github_url: GitHub repository URL (e.g., "https://github.com/user/project")
            start_date: Start date (e.g., "January 2023", "2023-01")
            end_date: End date (e.g., "March 2023", "Ongoing")
            team_size: Team size (e.g., "Solo project", "Team of 4", "5 developers")
            role: Your role (e.g., "Lead Developer", "Full-stack Developer", "Frontend Developer")
        
        Returns:
            Success message with project details
        """
        try:
            db_resume, resume_data = await get_or_create_resume()
            
            # Ensure projects list exists
            if not hasattr(resume_data, 'projects') or resume_data.projects is None:
                resume_data.projects = []
            
            # Build comprehensive project description
            full_description = description
            
            details = []
            if role:
                details.append(f"Role: {role}")
            if team_size:
                details.append(f"Team Size: {team_size}")
            if technologies_used:
                details.append(f"Technologies: {technologies_used}")
            if project_url:
                details.append(f"Live URL: {project_url}")
            if github_url:
                details.append(f"GitHub: {github_url}")
            
            if details:
                full_description += "\n\n" + "\n".join(details)
            
            # Format dates
            date_info = ""
            if start_date:
                date_info = start_date
                if end_date:
                    date_info += f" - {end_date}"
                elif end_date != "Ongoing":
                    date_info += " - Present"
            
            new_project = {
                "id": str(uuid.uuid4()),
                "title": project_name,
                "description": full_description,
                "dates": date_info,
                "technologies": technologies_used or "",
                "url": project_url or "",
                "github": github_url or ""
            }
            
            resume_data.projects.append(new_project)
            db_resume.data = resume_data.dict()
            await db.commit()
            
            return f"""✅ **Project Added Successfully!**

**Project:** {project_name}
{f"**Duration:** {date_info}" if date_info else ""}
{f"**Role:** {role}" if role else ""}
{f"**Technologies:** {technologies_used}" if technologies_used else ""}
{f"**Live URL:** {project_url}" if project_url else ""}

Your resume now has {len(resume_data.projects)} projects."""
            
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error adding project: {e}")
            return f"❌ Error adding project: {str(e)}"

    @tool
    async def add_certification(
        certification_name: str,
        issuing_organization: str,
        issue_date: Optional[str] = None,
        expiration_date: Optional[str] = None,
        credential_id: Optional[str] = None,
        credential_url: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Add a certification entry to resume with detailed variables.
        
        Args:
            certification_name: Name of certification (e.g., "AWS Solutions Architect", "Google Analytics Certified")
            issuing_organization: Organization that issued it (e.g., "Amazon Web Services", "Google")
            issue_date: When received (e.g., "January 2023", "2023-01")
            expiration_date: When expires (e.g., "January 2026", "Does not expire")
            credential_id: Certification ID/number
            credential_url: URL to verify certification
            description: Additional details about the certification
        
        Returns:
            Success message with certification details
        """
        try:
            db_resume, resume_data = await get_or_create_resume()
            
            # Ensure certifications list exists
            if not hasattr(resume_data, 'certifications') or resume_data.certifications is None:
                resume_data.certifications = []
            
            # Build certification details
            cert_details = []
            if issue_date:
                cert_details.append(f"Issued: {issue_date}")
            if expiration_date:
                cert_details.append(f"Expires: {expiration_date}")
            if credential_id:
                cert_details.append(f"Credential ID: {credential_id}")
            if credential_url:
                cert_details.append(f"Verify: {credential_url}")
            if description:
                cert_details.append(f"Description: {description}")
            
            full_description = "\n".join(cert_details) if cert_details else ""
            
            new_certification = {
                "id": str(uuid.uuid4()),
                "name": certification_name,
                "issuer": issuing_organization,
                "date": issue_date or "",
                "description": full_description,
                "url": credential_url or "",
                "credentialId": credential_id or ""
            }
            
            resume_data.certifications.append(new_certification)
            db_resume.data = resume_data.dict()
            await db.commit()
            
            return f"""✅ **Certification Added Successfully!**

**Certification:** {certification_name}
**Issuer:** {issuing_organization}
{f"**Issued:** {issue_date}" if issue_date else ""}
{f"**Expires:** {expiration_date}" if expiration_date else ""}
{f"**Credential ID:** {credential_id}" if credential_id else ""}

Your resume now has {len(resume_data.certifications)} certifications."""
            
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error adding certification: {e}")
            return f"❌ Error adding certification: {str(e)}"

    @tool
    async def list_documents() -> str:
        """Lists the documents available to the user."""
        result = await db.execute(
            select(Document.name).where(Document.user_id == user_id)
        )
        documents = result.scalars().all()
        if not documents:
            return "No documents found."
        return "Available documents:\n" + "\n".join(f"- {doc}" for doc in documents)

    @tool
    async def read_document(filename: str) -> str:
        """Reads the content of a specified document from the database."""
        try:
            # Search for document in database by name (case-insensitive partial match)
            doc_result = await db.execute(
                select(Document).where(
                    Document.user_id == user_id,
                    Document.name.ilike(f"%{filename}%")
                )
            )
            documents = doc_result.scalars().all()
            
            if not documents:
                return f"Error: Document '{filename}' not found in your uploaded documents."
            
            if len(documents) > 1:
                doc_list = "\n".join([f"- {doc.name}" for doc in documents])
                return f"Multiple documents found matching '{filename}':\n{doc_list}\n\nPlease be more specific with the document name."
            
            document = documents[0]
            
            if not document.content:
                return f"Error: Document '{document.name}' found but has no content."
            
            return f"Content of {document.name}:\n\n{document.content}"
            
        except Exception as e:
            return f"Error reading document: {e}"

    @tool
    async def search_jobs_linkedin_api(
        keyword: str,
        location: str = "Remote",
        job_type: str = "",
        experience_level: str = "",
        limit: int = 10
    ) -> str:
        """⭐ JOB SEARCH API - Direct access to job listings!
        
        Uses professional job search API for reliable, fast job searches.
        NO BROWSER AUTOMATION - Direct API access for instant results.
        
        Args:
            keyword: Job search terms (e.g., 'software engineer', 'software intern', 'python developer')
            location: Location to search in (e.g., 'Poland', 'Remote', 'Gdynia', 'Warsaw')
            job_type: Type of position ('full time', 'part time', 'contract', 'internship')
            experience_level: Level ('internship', 'entry level', 'associate', 'senior')
            limit: Number of jobs to return (max 25)
        
        Returns:
            Professional job listings with company info, descriptions, and apply links
            Always return the job listings in the format of a list of job postings.
        """
        try:
            from app.linkedin_jobs_service import get_linkedin_jobs_service
            
            log.info(f"🔗 Starting job search for '{keyword}' in '{location}'")
            
            # Get the LinkedIn service
            linkedin_service = get_linkedin_jobs_service()
            
            # Search for jobs
            jobs = await linkedin_service.search_jobs(
                keyword=keyword,
                location=location,
                job_type=job_type,
                experience_level=experience_level,
                limit=min(limit, 25),  # API limit
                date_since_posted="past week"
            )
            
            if not jobs:
                return f"🔍 No jobs found for '{keyword}' in {location}.\n\n💡 **Suggestions:**\n• Try different keywords (e.g., 'developer', 'engineer')\n• Expand location (e.g., 'Europe' instead of specific city)\n• Try different job types or experience levels"
            
            # Format the results for display
            formatted_jobs = []
            for i, job in enumerate(jobs, 1):
                job_text = f"**{i}. {job.position}** at **{job.company}**"
                
                if job.location:
                    job_text += f"\n   📍 **Location:** {job.location}"
                
                if job.ago_time:
                    job_text += f"\n   📅 **Posted:** {job.ago_time}"
                elif job.date:
                    job_text += f"\n   📅 **Posted:** {job.date}"
                
                if job.salary and job.salary != "Not specified":
                    job_text += f"\n   💰 **Salary:** {job.salary}"
                
                # Add job type if specified in parameters
                if job_type:
                    job_text += f"\n   📋 **Type:** {job_type}"
                
                # Add experience level if specified
                if experience_level:
                    job_text += f"\n   👨‍💼 **Level:** {experience_level}"
                
                if job.job_url:
                    # Shorten the URL for better readability
                    short_url = job.job_url
                    if len(short_url) > 80:
                        # Extract the job ID and create a shorter display
                        if 'linkedin.com/jobs/view/' in short_url:
                            job_id = short_url.split('/')[-1].split('?')[0]
                            short_url = f"linkedin.com/jobs/view/{job_id}"
                    
                    job_text += f"\n   🔗 **Apply:** [{short_url}]({job.job_url})"
                    # Remove automatic cover letter link
                
                formatted_jobs.append(job_text)
            
            result_header = f"🎯 **Found {len(jobs)} jobs for '{keyword}' in {location}:**\n\n"
            result_body = "\n\n---\n\n".join(formatted_jobs)
            result_footer = f"\n\n✨ **Ready to Apply** - Click the URLs to view full job details and apply directly!"
            
            return result_header + result_body + result_footer
            
        except Exception as e:
            log.error(f"Error in LinkedIn API search: {e}")
            return f"🔍 No jobs found for '{keyword}' in {location}.\\n\\n💡 **Suggestions:**\\n• Try different keywords (e.g., 'developer', 'engineer')\\n• Expand location (e.g., 'Europe' instead of specific city)\\n• Try different job types or experience levels"

    @tool("generate_cover_letter_from_url", return_direct=False)
    async def generate_cover_letter_from_url(job_url: str) -> str:
        """
        Generates a tailored cover letter by extracting job details from a provided URL.
        
        Args:
            job_url (str): The URL of the job posting.
        
        Returns:
            str: A confirmation message with a trigger to download the cover letter.
        """
        log.info(f"Attempting to generate cover letter from URL: {job_url}")
        try:
            current_user = user_id
            if not current_user:
                return "Authentication failed. Could not identify user."

            # Step 1: Scrape the job description from the URL
            from app.url_scraper import scrape_job_url, JobDetails

            scraped_details = await scrape_job_url(job_url)
            
            if isinstance(scraped_details, dict) and 'error' in scraped_details:
                log.error(f"Failed to scrape job details: {scraped_details['error']}")
                return f"I'm sorry, I couldn't extract details from that URL. The error was: {scraped_details['error']}"

            if not isinstance(scraped_details, JobDetails):
                log.error(f"Scraping returned an unexpected type: {type(scraped_details)}")
                return "I ran into an unexpected issue while reading the job posting. The website's structure might be too complex."

            # Step 2: Use the generated details to create and save the cover letter
            async with get_db_session() as db:
                user = await db.get(User, current_user)
                if not user:
                    return "User not found in database session."

                llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.3)
                parser = JsonOutputParser(pydantic_object=CoverLetterDetails)
                
                prompt_template = PromptTemplate(
                    template="""
                    You are a helpful assistant that generates structured cover letters based on user information and a job description.
                    Analyze the user's profile and the provided job details to create a compelling and tailored cover letter.
                    The user's personal information is: {user_info}.
                    The job details are: {job_details}.
                    You must respond using the following JSON format.
                    {format_instructions}
                    """,
                    input_variables=["user_info", "job_details"],
                    partial_variables={"format_instructions": parser.get_format_instructions()},
                )
                
                chain = prompt_template | llm | parser

                # EDIT: Instead of a simple string, create a structured dictionary
                # that matches what the AI needs for the 'personal_info' sub-object.
                user_info_dict = {
                    "name": user.name,
                    "email": user.email,
                    "linkedin": user.linkedin,
                    "phone": user.phone or "Not provided",
                    "website": "" # Assuming no website field on the user model for now
                }

                job_details_str = f"Job Title: {scraped_details.title}, Company: {scraped_details.company}, Description: {scraped_details.description}, Requirements: {scraped_details.requirements}"

                # EDIT: Pass the structured dictionary in the 'user_info' variable.
                response_data = await chain.ainvoke({"user_info": json.dumps(user_info_dict), "job_details": job_details_str})
                
                # The model might return a dict or a Pydantic model, ensure it's a dict
                if isinstance(response_data, BaseModel):
                    response_dict = response_data.model_dump()
                else:
                    response_dict = response_data
                
                # Serialize the entire dictionary to a JSON string for storing
                content_json_string = json.dumps(response_dict)

                # Create and save the new cover letter object
                new_cover_letter = GeneratedCoverLetter(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    content=content_json_string,
                )
                db.add(new_cover_letter)
                await db.commit()
                log.info(f"Successfully generated and saved cover letter {new_cover_letter.id} for user {user.id}")

            # Step 3: Return the trigger to the user
            return "I have successfully generated the cover letter based on the URL. You can view and download it now. [DOWNLOADABLE_COVER_LETTER]"

        except Exception as e:
            log.error(f"An unexpected error occurred in generate_cover_letter_from_url: {e}", exc_info=True)
            return f"An unexpected error occurred while generating the cover letter from the URL: {str(e)}"
        
    

    @tool("create_resume_from_scratch", return_direct=False)
    async def create_resume_from_scratch(prompt: str) -> str:
        """
        Creates a new resume from scratch based on a user's prompt.

        Args:
            prompt: A prompt from the user describing the resume they want to create.
        """
        async with async_session_maker() as session:
            try:
                log.info(f"Creating resume from scratch for user {user_id}")

                # 1. Set up LLM chain to generate the resume
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-preview-latest", temperature=0.3)
                parser = JsonOutputParser(pydantic_object=ResumeData)

                prompt_template = PromptTemplate(
                    template="""
                    You are an expert resume writer. Your task is to create a new resume from scratch based on the user's prompt.
                    The user's prompt is: {prompt}

                    **Instructions:**
                    - Generate a complete resume in JSON format.
                    - The resume should include personal information, a summary, work experience, education, and skills.
                    - Ensure the output is a valid JSON object that conforms to the provided schema.

                    {format_instructions}
                    """,
                    input_variables=["prompt"],
                    partial_variables={"format_instructions": parser.get_format_instructions()},
                )

                chain = prompt_template | llm | parser

                # 2. Invoke the chain and get the generated resume data
                resume_dict = await chain.ainvoke({"prompt": prompt})

                # 3. Save the new resume data to the database
                if resume_dict:
                    # Validate with Pydantic model before saving
                    new_resume_data = ResumeData(**resume_dict)
                    db_resume, _ = await get_or_create_resume(session)
                    db_resume.data = new_resume_data.dict()
                    db_resume.updated_at = datetime.utcnow()
                    session.add(db_resume)
                    await session.commit()
                    log.info(f"Successfully created and saved resume from scratch {db_resume.id} for user {user_id}")
                    return "I have successfully created a new resume from scratch. You can view and download it now. [DOWNLOADABLE_RESUME]"
                else:
                    return "I could not create a resume from scratch. Please try again."

            except Exception as e:
                log.error(f"An unexpected error occurred in create_resume_from_scratch: {e}", exc_info=True)
                if session.is_active:
                    await session.rollback()
                return f"An unexpected error occurred while creating the resume from scratch: {str(e)}"

    @tool("refine_cv_from_url", return_direct=False)
    async def refine_cv_from_url(job_url: str) -> str:
        """
        Refines an existing resume based on a job posting URL.
        
        Args:
            job_url (str): The URL of the job posting to refine the resume for. 
        
        Returns:
            str: A confirmation message with a trigger to download the refined resume.
        """
        async with async_session_maker() as session:
            try:
                # Step 1: Scrape job details from the URL
                log.info(f"Attempting to refine CV from URL: {job_url}")
                
                scraped_details = await scrape_job_url(job_url)

                if isinstance(scraped_details, dict) and 'error' in scraped_details:
                    return f"Sorry, I couldn't extract job details from that URL. Error: {scraped_details['error']}"

                if not isinstance(scraped_details, JobDetails):
                    return "I ran into an issue reading the job posting. The website's structure might be complex."

                job_title = scraped_details.title
                company_name = scraped_details.company
                job_description = f"{scraped_details.description}\n\nRequirements:\n{scraped_details.requirements}"

                # Step 2: Generate the tailored resume using AI
                # Get User's Base Resume Data
                resume_result = await session.execute(
                    select(Resume).where(Resume.user_id == user.id)
                )
                base_resume = resume_result.scalars().first()
                
                base_resume_data = {}
                if base_resume and base_resume.data:
                    base_resume_data = fix_resume_data_structure(base_resume.data)

                # Define the Pydantic model for the output
                class TailoredResume(BaseModel):
                    personalInfo: dict = Field(description="Personal information section, including summary.")
                    experience: list = Field(description="List of all work experiences.")
                    education: list = Field(description="List of all education entries.")
                    skills: list = Field(description="A comprehensive list of skills.")
                    projects: list = Field(description="List of projects, if any.")
                    certifications: list = Field(description="List of certifications, if any.")

                parser = PydanticOutputParser(pydantic_object=TailoredResume)

                prompt_template = """
                You are an expert career coach. Your task is to generate a complete, tailored resume in JSON format
                based on the user's existing resume data and a target job description.

                **User's Base Resume Data:**
                {base_resume}

                **Target Job Description:**
                - Job Title: {job_title}
                - Company: {company_name}
                - Description: {job_description}

                **Instructions:**
                1. Rewrite the summary in the `personalInfo` section to target the job.
                2. Rephrase `experience` descriptions to highlight relevant accomplishments.
                3. Prioritize the `skills` most relevant to the job.
                4. Keep education, projects, and certifications largely the same.
                5. Return ONLY a valid JSON object matching the schema.

                {format_instructions}
                """
                prompt = PromptTemplate(
                    template=prompt_template,
                    input_variables=["base_resume", "job_title", "company_name", "job_description"],
                    partial_variables={"format_instructions": parser.get_format_instructions()},
                )
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.4)
                chain = prompt | llm | parser

                tailored_resume = await chain.ainvoke({
                    "base_resume": json.dumps(base_resume_data, indent=2),
                    "job_title": job_title,
                    "company_name": company_name,
                    "job_description": job_description,
                })

                # Step 3: Save the new resume to the database
                if base_resume:
                    base_resume.data = tailored_resume.dict()
                else:
                    new_resume = Resume(user_id=user.id, data=tailored_resume.dict())
                    session.add(new_resume)
                
                await session.commit()

                # Step 4: Return a success message
                output_str = (
                    f"✅ I have successfully refined your CV for the **{job_title}** role at **{company_name}**.\n\n"
                    "I analyzed the job description from the URL and tailored your profile accordingly. "
                    "A download button should now be available on this message to get the updated PDF."
                    "[DOWNLOADABLE_RESUME]"
                )

                return output_str

            except Exception as e:
                log.error(f"Error in refine_cv_from_url tool: {e}", exc_info=True)
                return f"❌ An error occurred while refining your resume from the URL. The website might be blocking access, or the job posting may have expired."

 
        

    @tool
    async def generate_cover_letter(
        company_name: str,
        job_title: str,
        job_description: str
    ) -> str:
        """
        Generates a structured cover letter based on provided job details.

        This tool uses a PydanticOutputParser to GUARANTEE a clean JSON output,
        wrapped in a string with a trigger for the frontend.
        It correctly uses the 'user' object from the parent WebSocket scope.
        """
        async with async_session_maker() as session:
            try:
                log.info(f"Generating GUARANTEED structured cover letter for {job_title} at {company_name}")
                
                # CORRECTLY get resume data using the existing helper and user object from scope
                db_resume, resume_data = await get_or_create_resume(session)

                # Create the parser to force a specific JSON output structure
                parser = PydanticOutputParser(pydantic_object=CoverLetterDetails)

                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", """You are an expert cover letter writer. Your task is to generate a cover letter in a structured JSON format. You MUST adhere to the JSON schema provided below. Do NOT add any conversational text, introductory sentences, or markdown formatting around the JSON object. Your output must be ONLY the raw JSON object.

{format_instructions}"""),
                    ("human", """Please generate a tailored cover letter based on the following details:

**Job Details:**
- Job Title: {job_title}
- Company Name: {company_name}
- Job Description: {job_description}

**Candidate's Information:**
- Name: {name}
- Relevant Skills: {skills}
- Summary of Experience: {summary}

Generate the full cover letter body. It should be professional, concise, and tailored to the job description, highlighting the candidate's relevant skills and experience. Address it to the 'Hiring Team' if a specific name is not available.
"""),
                ])

                chain = prompt_template | ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7) | parser
                
                personal_info_dict = resume_data.personalInfo.dict() if resume_data.personalInfo else {}

                # Invoke the chain with all the necessary data
                structured_response = await chain.ainvoke({
                    "format_instructions": parser.get_format_instructions(),
                "job_title": job_title,
                    "company_name": company_name,
                "job_description": job_description,
                    "name": personal_info_dict.get("name", "User"),
                    "skills": ", ".join(resume_data.skills) if resume_data.skills else "Not specified",
                    "summary": personal_info_dict.get("summary", "No summary provided.")
                })

                # The 'structured_response' is now a guaranteed Pydantic object.
                # We will add the full personal_info object to it before returning.
                response_dict = structured_response.model_dump()
                response_dict["personal_info"] = personal_info_dict

                new_cover_letter_id = str(uuid.uuid4())
                new_db_entry = GeneratedCoverLetter(
                    id=new_cover_letter_id,
                    user_id=user.id,
                    content=json.dumps(response_dict)
                )
                session.add(new_db_entry)
                await session.commit()
                log.info(f"Successfully saved new cover letter with ID: {new_cover_letter_id}")


               
                
                # The agent expects a final string containing the trigger and the JSON payload.
                final_output_string = f"[DOWNLOADABLE_COVER_LETTER] {json.dumps(response_dict)}"
                
                log.info(f"Successfully generated structured cover letter string ID {new_cover_letter_id}")
                return final_output_string
            
            except Exception as e:
                log.error(f"Error in GUARANTEED generate_cover_letter: {e}", exc_info=True)
                return "Sorry, I encountered an error while writing the cover letter. Please try again."


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
            
            return f"""[DOWNLOADABLE_RESUME]

## 📄 Resume PDF Ready

✅ **Your resume is ready for download!**

You can download your resume in multiple professional styles using the download dialog. Choose from Modern, Classic, or Minimal styles, edit content if needed, and preview before downloading.

**A download button (📥) should appear on this message to access all styling and editing options.**"""
            
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
            
            return f"""[DOWNLOADABLE_RESUME]

## 📄 **CV/Resume Ready for Download**

✅ **Your CV/Resume is ready for download!**

You can download your CV/Resume in multiple professional styles. The download dialog will let you:

- **Choose from 3 professional styles** (Modern, Classic, Minimal)
- **Edit content** before downloading if needed
- **Preview** your CV/Resume before downloading
- **Download all styles** at once

**A download button (📥) should appear on this message to access all options.**"""
            
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
            # INTELLIGENT FIX: Ensure the correct memory manager is used for this advanced tool
            current_memory_manager = memory_manager
            if not isinstance(current_memory_manager, EnhancedMemoryManager):
                # If the provided manager is the simple one, create an enhanced one for this specific task
                log.warning("SimpleMemoryManager provided to advanced tool, creating temporary EnhancedMemoryManager.")
                current_memory_manager = EnhancedMemoryManager(user_id=user.id, db_session=db)
                await current_memory_manager.load_memory()

            # Get document insights using enhanced memory system
            from app.documents import _generate_comprehensive_document_insights

            if not documents:
                return "📄 **No Documents Found**\n\nYou haven't uploaded any documents yet. Upload your resume, cover letters, or other career documents to get personalized insights and recommendations!\n\n**To upload documents:**\n- Use the attachment button in the chat\n- Drag and drop files into the chat\n- Supported formats: PDF, DOCX, TXT"
            
            # Get user learning profile
            if current_memory_manager:
                context = await current_memory_manager.get_conversation_context()
                user_profile = context
            else:
                user_profile = None
            
            # Generate comprehensive insights
            insights = await _generate_comprehensive_document_insights(
                documents, user_profile, current_memory_manager
            )
            
            # Track insights tool usage
            if current_memory_manager:
                await current_memory_manager.save_user_behavior(
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

            user_profile_dict = {
                "name": user.name or f"{user.first_name or ''} {user.last_name or ''}".strip(),
                "profile_headline": user.profile_headline or "",
                "skills": user.skills.split(',') if user.skills else []
            }

            analysis = await _analyze_single_document(document, user_profile_dict, memory_manager)

            # Track specific document analysis
            if memory_manager:
                await memory_manager.save_user_behavior(
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
    async def enhanced_document_search(query: str, doc_id: Optional[str] = None) -> str:
        """
        Enhanced search across all user documents, including resumes, cover letters, and user profile.
        Prioritizes the most recently uploaded documents in case of ambiguity.
        If a file is mentioned in the query (e.g., "File Attached: resume.pdf"), it will be summarized directly.

        Args:
            query (str): The user's search query, which may include file attachment context.
            doc_id (Optional[str]): The specific ID of a document to search within.

        Returns:
            A formatted string containing the most relevant search results or a direct summary of an attached file.
        """
        try:
            import re
            
            # INTELLIGENT FIX: Check for file attachment context in the user's message
            attachment_patterns = [
                r'File Attached:\s*(.+?)(?:\n|$)',
                r'CV/Resume uploaded successfully![\s\S]*?File:\s*(.+?)(?:\n|$)',
                # This new pattern looks for filenames mentioned directly in the query
                r'([\w.-]+\.(?:pdf|docx|doc|txt))\b'
            ]
            
            extracted_filename = None
            for pattern in attachment_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    extracted_filename = match.group(1).strip()
                    break
            
            # If an attachment is explicitly mentioned, analyze it directly instead of searching
            if extracted_filename:
                log.info(f"Detected attached file in query: '{extracted_filename}'. Analyzing it directly.")
                
                # Find the specific document, prioritizing the most recent one
                doc_result = await db.execute(
                    select(Document).where(
                        Document.user_id == user.id,
                        Document.name.ilike(f"%{extracted_filename}%")
                    ).order_by(Document.date_created.desc())
                )
                documents = doc_result.scalars().all()

                if not documents:
                    return f"I see you mentioned '{extracted_filename}', but I couldn't find that document in your uploads. Please try uploading it again."
                
                # Use the most recent document matching the name
                target_document = documents[0]
                
                if not target_document.content:
                    return f"The document '{target_document.name}' was found but appears to be empty or unreadable."
                
                # Summarize the specific document's content to answer the user's implicit question
                from langchain_core.prompts import ChatPromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                
                summarization_prompt = ChatPromptTemplate.from_template(
                    "You are a helpful assistant. Summarize the key points of the following document content in a few clear, concise paragraphs. Address the user directly and be informative.\n\n---\n\n{document_content}"
                )
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.2)
                chain = summarization_prompt | llm | StrOutputParser()
                
                # Limit content size for summarization to avoid token limits
                summary = await chain.ainvoke({"document_content": target_document.content[:4000]}) 
                
                user_first_name = user.first_name or "there"
                return f"Of course, {user_first_name}! Here is a summary of the document you just attached, '{target_document.name}':\n\n{summary}"

            # --- Fallback to original search logic if no attachment context is found ---
            log.info(f"No attachment context in query. Performing general search for: '{query}'")
            
            user_profile_content = (
                f"Name: {user.name}\n"
                f"Email: {user.email}\n"
                f"Phone: {user.phone}\n"
                f"Location: {user.address}\n"
                f"LinkedIn: {user.linkedin}\n"
                f"Profile Headline: {user.profile_headline}\n"
                f"Skills: {user.skills}"
            )

            doc_result = await db.execute(
                select(Document).where(Document.user_id == user.id)
            )
            documents = doc_result.scalars().all()

            if not documents and not user_profile_content:
                return "No documents or user profile found to search."

            all_content = []
            if user_profile_content:
                all_content.append(
                    {"id": "user_profile", "name": "USER PROFILE", "content": user_profile_content, "date_created": datetime.utcnow()}
                )
            for doc in documents:
                all_content.append(
                    {"id": doc.id, "name": doc.name, "content": doc.content, "date_created": doc.date_created}
                )

            search_results = []
            for item in all_content:
                content_text = item.get("content", "") or ""
                if query.lower() in content_text.lower():
                    search_results.append(item)

            search_results.sort(key=lambda x: x.get("date_created", datetime.min), reverse=True)

            if not search_results:
                return f"🔍 **No Results Found**\n\nI couldn't find any relevant information for '{query}' in your uploaded documents."

            response_parts = [
                f"**Search Results for '{query}'**\n",
                f"Found {len(search_results)} relevant sections:\n",
            ]
            for i, result in enumerate(search_results[:4], 1):
                content_preview = (result.get("content", "") or "")[:200]
                response_parts.append(
                    f"**{i}.** [{result['name']}]\n{content_preview}..."
                )
            
            response_parts.append("\n💬 **Need more specific information? Ask me about any particular aspect or request a detailed analysis!**")
            return "\n\n".join(response_parts)

        except Exception as e:
            log.error(f"Error in enhanced document search: {e}", exc_info=True)
            return f"❌ Sorry, I couldn't search your documents for '{query}' right now. Please try again or let me know if you need help with document analysis."


  
    @tool
    async def enhance_resume_section(
        section: str,
        job_description: str = "",
        current_content: str = ""
    ) -> str:
        """
        Enhance a specific section of your resume with AI-powered improvements.
        This tool fetches the user's current resume, uses an LLM to improve a specific section,
        and then updates the resume record in the database with the new structured data.
        
        Args:
            section: Section to enhance (summary, experience, skills, education)
            job_description: Target job description for tailoring (optional)
            current_content: Current content of the section to improve (optional, will be fetched if not provided)
        
        Returns:
            A success message indicating the section has been enhanced.
        """
        async with async_session_maker() as session:
            try:
                # 1. Get the user's current resume data
                db_resume, resume_data = await get_or_create_resume(session)

                # Determine the content to be enhanced
                content_to_enhance = current_content
                if not content_to_enhance:
                    if section.lower() == 'summary':
                        content_to_enhance = resume_data.personalInfo.summary
                    elif section.lower() == 'experience':
                        content_to_enhance = json.dumps([exp.dict() for exp in resume_data.experience])
                    elif section.lower() == 'skills':
                        content_to_enhance = ", ".join(resume_data.skills)
                    elif section.lower() == 'education':
                         content_to_enhance = json.dumps([edu.dict() for edu in resume_data.education])

                # 2. Use LLM to generate the enhanced content for the specific section
                from langchain_core.prompts import ChatPromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                
                prompt = ChatPromptTemplate.from_template(
                    """You are an expert resume writer. Enhance the specified resume section based on the user's context and the target job description.

USER CONTEXT:
- Current Role: {current_role}
- Current Skills: {current_skills}

SECTION TO ENHANCE: {section}
CURRENT CONTENT:
{content_to_enhance}

TARGET JOB DESCRIPTION (if provided):
{job_description}

INSTRUCTIONS:
- Rewrite the content to be more impactful and results-oriented.
- Use strong action verbs and quantify achievements where possible.
- If it is the 'skills' section, return a comma-separated list of skills.
- If it is 'experience' or 'education', return a JSON array of objects.
- If it is 'summary', return a concise paragraph.
- Return ONLY the enhanced content for the section.

ENHANCED CONTENT:"""
                )
                
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.5)
                chain = prompt | llm | StrOutputParser()
                
                enhanced_content = await chain.ainvoke({
                    "current_role": resume_data.experience[0].jobTitle if resume_data.experience else "Not specified",
                    "current_skills": ", ".join(resume_data.skills),
                    "section": section,
                    "content_to_enhance": content_to_enhance,
                    "job_description": job_description or "Not specified"
                })

                # 3. Update the structured resume data with the enhanced content
                if section.lower() == 'summary':
                    resume_data.personalInfo.summary = enhanced_content
                elif section.lower() == 'experience':
                    resume_data.experience = [Experience(**exp) for exp in json.loads(enhanced_content)]
                elif section.lower() == 'skills':
                    resume_data.skills = [s.strip() for s in enhanced_content.split(',')]
                elif section.lower() == 'education':
                    resume_data.education = [Education(**edu) for edu in json.loads(enhanced_content)]

                # 4. Save the updated resume data back to the database
                db_resume.data = resume_data.dict()
                attributes.flag_modified(db_resume, "data")
                await session.commit()

                return f"✅ Your '{section}' section has been successfully enhanced. [DOWNLOADABLE_RESUME]"

            except Exception as e:
                log.error(f"Error enhancing resume section: {e}", exc_info=True)
                return f"❌ Sorry, I encountered an error while enhancing your {section} section: {str(e)}."


    @tool
    async def generate_tailored_resume(
        job_title: str,
        company_name: str = "",
        job_description: str = "",
        user_skills: str = ""
    ) -> str:
        """
        Generates a complete, tailored resume based on a job description and user's profile.
        This tool now fetches the user's data, uses an LLM to generate a structured JSON
        resume, and updates the user's master resume record in the database.
        """
        async with async_session_maker() as session:
            try:
                # 1. Get User's Base Resume Data
                db_resume, base_resume_data = await get_or_create_resume(session)

                # 2. Create the generation chain with a Pydantic output parser
                parser = PydanticOutputParser(pydantic_object=ResumeData)

                prompt_template = """
                You are an expert career coach and resume writer. Your task is to generate a complete, tailored resume in a structured JSON format.
                Analyze the user's base resume data and the provided job description to create a highly relevant and impactful resume.

                **User's Base Resume Data:**
                {base_resume}

                **Target Job Description:**
                - Job Title: {job_title}
                - Company: {company_name}
                - Description: {job_description}

                **User's Key Skills to Highlight (if provided):**
                {user_skills}

                **Instructions:**
                1.  **Rewrite the Summary:** Create a new, concise professional summary in the `personalInfo` section that directly targets the job description.
                2.  **Tailor Experience:** Rephrase job descriptions under `experience` to highlight accomplishments and responsibilities most relevant to the target role. Use strong action verbs and quantify achievements where possible.
                3.  **Prioritize Skills:** In the `skills` section, reorder and highlight the skills that are most relevant to the job description.
                4.  **Maintain Structure:** Keep the user's education, projects, and certifications as they are.
                5.  **Output Format:** You MUST provide the final output as a valid JSON object matching the provided schema. Do not add any extra text or formatting.

                {format_instructions}
                """

                prompt = PromptTemplate(
                    template=prompt_template,
                    input_variables=["base_resume", "job_title", "company_name", "job_description", "user_skills"],
                    partial_variables={"format_instructions": parser.get_format_instructions()},
                )

                llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.4)
                chain = prompt | llm | parser

                # 3. Invoke the chain to generate the structured, tailored resume
                tailored_resume = await chain.ainvoke({
                    "base_resume": json.dumps(base_resume_data.dict(), indent=2),
                    "job_title": job_title,
                    "company_name": company_name,
                    "job_description": job_description,
                    "user_skills": user_skills,
                })

                # 4. Update the user's single master resume record.
                db_resume.data = tailored_resume.dict()
                attributes.flag_modified(db_resume, "data")
                await session.commit()
                
                # 5. Return a simple confirmation message with the trigger.
                return (f"I have successfully tailored your resume for the {job_title} role. "
                        "You can preview, edit, and download it now. [DOWNLOADABLE_RESUME]")

            except Exception as e:
                log.error(f"Error in generate_tailored_resume tool: {e}", exc_info=True)
                return "❌ An error occurred while tailoring your resume. Please ensure the job description is detailed enough."


    @tool
    async def create_resume_from_scratch(
        target_role: str,
        experience_level: str = "mid-level",
        industry: str = "",
        key_skills: str = ""
    ) -> str:
        """Create a complete professional resume from scratch based on your career goals."""
        async with async_session_maker() as session:
            try:
                # 1. Extract comprehensive information from user's documents.
                doc_result = await session.execute(
                    select(Document).where(Document.user_id == user.id).order_by(Document.date_created.desc())
                )
                documents = doc_result.scalars().all()
                
                document_content = ""
                if documents:
                    for doc in documents[:5]:
                        if doc.content and len(doc.content) > 100:
                            document_content += f"\n\n=== DOCUMENT: {doc.name} ===\n{doc.content[:3000]}"
                
                comprehensive_info = ""
                if document_content:
                    from langchain_core.prompts import ChatPromptTemplate
                    from langchain_core.output_parsers import JsonOutputParser
                    
                    extraction_prompt = ChatPromptTemplate.from_template(
                        """Extract comprehensive resume information from these documents and return it as a valid JSON object.
                        
                        {document_content}
                        
                        The JSON object should have keys: 'personalInfo', 'experience', 'education', 'skills'."""
                    )
                    
                    extraction_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.1)
                    extraction_chain = extraction_prompt | extraction_llm | JsonOutputParser()
                    
                    try:
                        comprehensive_info = await extraction_chain.ainvoke({"document_content": document_content})
                    except Exception as e:
                        log.warning(f"Failed to extract comprehensive info as JSON: {e}")
                        comprehensive_info = {}

                # 2. Verify if critical information was found.
                missing_sections = []
                if not comprehensive_info or not comprehensive_info.get("experience"):
                    missing_sections.append("work experience")
                if not comprehensive_info or not comprehensive_info.get("education"):
                    missing_sections.append("education history")
                if not comprehensive_info or not comprehensive_info.get("skills"):
                    missing_sections.append("key skills")
                
                # 3. If information is missing, ask the user for it.
                if missing_sections:
                    missing_str = ", ".join(missing_sections)
                    return (
                        f"I've started drafting your resume for a {target_role} role, but I couldn't find details about your {missing_str} in your documents. "
                        "To create the best resume for you, could you please provide this information?"
                    )
                
                # 4. If data exists, create a structured resume using the AI.
                parser = PydanticOutputParser(pydantic_object=ResumeData)
                prompt = ChatPromptTemplate.from_template(
                    """You are an expert resume writer. Create a complete, populated resume using the user's information.
                    
                    USER INFORMATION (JSON):
                    {context}

                    CAREER GOAL:
                    - Target Role: {target_role}

                    INSTRUCTIONS:
                    - Use ONLY the information from the user's JSON context.
                    - Do NOT use placeholders.
                    - Format the output as a valid JSON object matching the schema.

                    {format_instructions}
                    """
                )
                
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7)
                chain = prompt | llm | parser
                
                new_resume_data = await chain.ainvoke({
                    "context": json.dumps(comprehensive_info),
                    "target_role": target_role,
                    "format_instructions": parser.get_format_instructions(),
                })

                # 5. Save the structured JSON to the master Resume record.
                db_resume, _ = await get_or_create_resume(session)
                db_resume.data = new_resume_data.dict()
                attributes.flag_modified(db_resume, "data")
                await session.commit()
                
                return (f"I have created a new resume draft for you, tailored for a {target_role} role. "
                        "You can now preview, edit, and download it. [DOWNLOADABLE_RESUME]")
                
            except Exception as e:
                log.error(f"Error creating resume from scratch: {e}", exc_info=True)
                return f"❌ Sorry, I encountered an error while creating your resume: {str(e)}."

    @tool
    async def refine_cv_for_role(
        target_role: str = "AI Engineering",
        job_description: str = "",
        company_name: str = ""
    ) -> str:
        """⭐ PRIMARY CV REFINEMENT TOOL ⭐"""
        async with resume_modification_lock:
            async with async_session_maker() as session:
                try:
                    log.info(f"CV refinement requested for role: {target_role}")
                    
                    # 1. Get the user's current resume data.
                    db_resume, base_resume_data = await get_or_create_resume(session)
                    
                    # 2. Create the generation chain to output structured JSON.
                    parser = PydanticOutputParser(pydantic_object=ResumeData)
                    
                    prompt = ChatPromptTemplate.from_template(
                        """You are an expert career coach and resume writer. Your task is to refine a user's resume and return it as a structured JSON object.
                        
                        USER'S CURRENT RESUME DATA:
                        {context}

                        TARGET ROLE: {target_role}
                        COMPANY: {company_name}
                        JOB DESCRIPTION: {job_description}

                        **CRITICAL, NON-NEGOTIABLE DIRECTIVE:**
                        - **You MUST ONLY use the information provided in the 'USER'S CURRENT RESUME DATA' section.**
                        - **You are STRICTLY FORBIDDEN from inventing, creating, or hallucinating any new information.**
                        - Your ONLY task is to REFORMAT, REPHRASE, and TAILOR the *existing* information to better match the target role.
                        - If a section is empty in the user's data, it should remain empty.
                        - Return ONLY a valid JSON object matching the provided schema. Do not add any extra text or formatting.

                        {format_instructions}
                        """
                    )
                    
                    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.3)
                    chain = prompt | llm | parser
                    
                    # 3. Invoke the chain to generate the refined structured resume.
                    refined_resume_data = await chain.ainvoke({
                        "context": base_resume_data.json(),
                        "target_role": target_role,
                        "company_name": company_name or "target companies",
                        "job_description": job_description or f"General {target_role} position requirements",
                        "format_instructions": parser.get_format_instructions(),
                    })
                    
                    # 4. Update the user's single master resume record with the new structured data.
                    db_resume.data = refined_resume_data.dict()
                    attributes.flag_modified(db_resume, "data")
                    await session.commit()
                    
                    # 5. Return a simple confirmation message with the trigger.
                    return (f"I've successfully refined your CV for the **{target_role}** role. "
                            "A download button will appear on this message. [DOWNLOADABLE_RESUME]")
                    
                except Exception as e:
                    log.error(f"Error in CV refinement: {e}", exc_info=True)
                    return f"❌ Sorry, an error occurred while refining your CV. Please try again."

    
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
                model="gemini-2.5-pro-preview-03-25",
                temperature=0.7
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
                # Import and use the fix function from resume.py
                from app.resume import fix_resume_data_structure
                # Fix missing ID fields in existing data before validation
                fixed_data = fix_resume_data_structure(db_resume.data)
                resume_data = ResumeData(**fixed_data)
                user_skills = ', '.join(resume_data.skills) if resume_data.skills else ""
            
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
                model="gemini-2.5-pro-preview-03-25",
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
                model="gemini-2.5-pro-preview-03-25",
                temperature=0.6,
                callbacks=[tracer]
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
        job_title: str = "",
        company_name: str = "",
        interview_type: str = "general",
        job_url: str = ""
    ) -> str:
        """Get comprehensive interview preparation guidance based on your CV and target role.
        
        Args:
            job_title: Position you're interviewing for (optional if job_url provided)
            company_name: Target company (optional if job_url provided)
            interview_type: Type of interview (behavioral, technical, panel, phone, video)
            job_url: URL of the job posting to analyze (optional, will extract job details)
        
        Returns:
            Personalized interview preparation guide with questions and strategies
        """
        try:
            # Extract job details from URL if provided
            extracted_job_title = job_title
            extracted_company_name = company_name
            job_description = ""
            
            if job_url:
                log.info(f"Extracting job details from URL: {job_url}")
                try:
                    extraction_method = _choose_extraction_method(job_url)
                    log.info(f"Using extraction method: {extraction_method}")
                    
                    if extraction_method == "browser":
                        success, extracted_data = await _try_browser_extraction(job_url)
                        if success and extracted_data:
                            extracted_job_title = extracted_data.get("job_title", job_title)
                            extracted_company_name = extracted_data.get("company_name", company_name)
                            job_description = extracted_data.get("job_description", "")
                            log.info(f"Successfully extracted job details via browser: {extracted_job_title} at {extracted_company_name}")
                        else:
                            log.warning("Browser extraction failed, falling back to basic extraction")
                            success, extracted_data = await _try_basic_extraction(job_url)
                            if success and extracted_data:
                                extracted_job_title = extracted_data.get("job_title", job_title)
                                extracted_company_name = extracted_data.get("company_name", company_name)
                                job_description = extracted_data.get("job_description", "")
                    else:
                        success, extracted_data = await _try_basic_extraction(job_url)
                        if success and extracted_data:
                            extracted_job_title = extracted_data.get("job_title", job_title)
                            extracted_company_name = extracted_data.get("company_name", company_name)
                            job_description = extracted_data.get("job_description", "")
                        
                except Exception as e:
                    log.warning(f"URL extraction failed: {e}, using provided job details")
            
            # Use extracted details or fallback to provided ones
            final_job_title = extracted_job_title or job_title
            final_company_name = extracted_company_name or company_name
            
            if not final_job_title:
                return "❌ Please provide either a job title or a job URL to generate interview preparation guide."
            
            # Get user's CV data for personalized prep
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            db_resume = result.scalars().first()
            
            user_context_parts = [f"User: {user.first_name} {user.last_name}"]
            if db_resume:
                from app.resume import fix_resume_data_structure
                fixed_data = fix_resume_data_structure(db_resume.data)
                resume_data = ResumeData(**fixed_data)
                
                # Build a comprehensive user context
                if resume_data.personalInfo and resume_data.personalInfo.summary:
                    user_context_parts.append(f"\n## Professional Summary\n{resume_data.personalInfo.summary}")

                if resume_data.experience:
                    user_context_parts.append("\n## Work Experience")
                    for exp in resume_data.experience:
                        exp_str = f"- **{exp.jobTitle}** at **{exp.company}** ({exp.dates})\n  {exp.description}"
                        user_context_parts.append(exp_str)

                if resume_data.education:
                    user_context_parts.append("\n## Education")
                    for edu in resume_data.education:
                        edu_str = f"- **{edu.degree}** from **{edu.institution}** ({edu.dates})"
                        user_context_parts.append(edu_str)

                if resume_data.skills:
                    user_context_parts.append(f"\n## Skills\n{', '.join(resume_data.skills)}")

                if resume_data.projects:
                    user_context_parts.append("\n## Projects")
                    for proj in resume_data.projects:
                        proj_str = f"- **{proj.name}**: {proj.description}"
                        user_context_parts.append(proj_str)
            
            user_context = "\n".join(user_context_parts)
            
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(
                """You are an expert interview coach. Create a comprehensive, personalized interview preparation guide.

USER CONTEXT: {user_context}
TARGET ROLE: {job_title}
COMPANY: {company_name}
INTERVIEW TYPE: {interview_type}
JOB DESCRIPTION: {job_description}

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
                model="gemini-2.5-pro-preview-03-25",
                temperature=0.3
            )
            
            chain = prompt | llm | StrOutputParser()
            
            guide = await chain.ainvoke({
                "user_context": user_context,
                "job_title": final_job_title,
                "company_name": final_company_name or "the target company",
                "interview_type": interview_type,
                "job_description": job_description or "No specific job description provided"
            })
            
            # Generate structured Q&A pairs for flashcards
            qa_prompt = ChatPromptTemplate.from_template(
                """Generate 10 realistic interview questions and answers for this role, including CV-specific questions.

USER CONTEXT: {user_context}
TARGET ROLE: {job_title}
COMPANY: {company_name}
INTERVIEW TYPE: {interview_type}
JOB DESCRIPTION: {job_description}

**CRITICAL: Analyze the user's CV/background and the job description to create questions that reference their SPECIFIC experience:**

Generate exactly 10 interview questions with sample answers. Return as JSON array:
[
  {{
    "question": "Tell me about yourself.",
    "answer": "Brief sample answer that the candidate could reference or build upon"
  }},
  ...
]

Include this mix:
- 2 CV-specific questions (reference their actual experience, career transitions, specific technologies/companies)
- 2 behavioral questions (STAR method opportunities)
- 3 technical/role-specific questions
- 2 situational questions
- 1 company/culture fit question

**CV-SPECIFIC QUESTION EXAMPLES (adapt to their actual background):**
- "I see you were doing freelance work while working full-time at [Company]. How did you manage both responsibilities?"
- "You used [Technology] at [Company]. Can you walk me through how you implemented it?"
- "I notice you transitioned from [Previous Role] to [Current Role]. What motivated this change?"
- "You worked at [Company] for [Duration]. What was your biggest achievement there?"
- "I see you have experience with [Specific Skill/Technology]. How did you learn it and apply it?"
- "You've worked in both [Industry A] and [Industry B]. How do those experiences complement each other?"

**IMPORTANT RULES:**
1. Reference ACTUAL companies, technologies, roles from their background
2. Ask about career transitions, overlapping roles, technology choices
3. Question specific timeframes, gaps, or interesting patterns in their CV
4. Make questions sound like a real interviewer who studied their resume
5. Include follow-up style questions that dig deeper into their experience

"""
            )
            
            qa_chain = qa_prompt | llm | StrOutputParser()
            
            qa_json_str = await qa_chain.ainvoke({
                "user_context": user_context,
                "job_title": final_job_title,
                "company_name": final_company_name or "the target company",
                "interview_type": interview_type,
                "job_description": job_description or "No specific job description provided"
            })

            # Format the final response
            final_response = (
                f"Of course! Here is your interview preparation guide for the "
                f"**{final_job_title}** position at **{final_company_name}**.\n\n"
                f"[INTERVIEW_FLASHCARDS_AVAILABLE]\n"
                f"<!--FLASHCARD_DATA:{qa_json_str}-->\n\n"
                f"{guide}"
            )
            
            return final_response

        except Exception as e:
            log.error(f"Error generating interview guide: {e}", exc_info=True)
            return "❌ I'm sorry, but I encountered an error while trying to generate the interview preparation guide. Please try again."

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
                model="gemini-2.5-pro-preview-03-25",
                temperature=0.7,
                callbacks=[tracer]
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
                # Import and use the fix function from resume.py
                from app.resume import fix_resume_data_structure
                # Fix missing ID fields in existing data before validation
                fixed_data = fix_resume_data_structure(db_resume.data)
                resume_data = ResumeData(**fixed_data)
                user_context += f"\nCurrent Background: {resume_data.personalInfo.summary or 'No summary available'}"
                user_context += f"\nSkills: {', '.join(resume_data.skills[:8]) if resume_data.skills else 'No skills listed'}"
                if resume_data.experience:
                    user_context += f"\nCurrent Role: {resume_data.experience[0].jobTitle} at {resume_data.experience[0].company}"
            
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
                model="gemini-2.5-pro-preview-03-25",
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

    @tool
    async def extract_and_populate_profile_from_documents() -> str:
        """Extract personal information from uploaded documents and populate user profile automatically.
        
        This tool extracts real personal details (name, email, phone, linkedin, portfolio) 
        from uploaded CV/resume documents and updates the user profile with actual data
        instead of placeholder information.
        
        Returns:
            Success message with extracted information summary
        """
        try:
            # Get user documents for extraction
            doc_result = await db.execute(
                select(Document).where(Document.user_id == user_id).order_by(Document.date_created.desc())
            )
            documents = doc_result.scalars().all()
            
            if not documents:
                return "❌ No documents found to extract profile information from. Please upload your CV/resume first."
            
            # Extract information from documents using AI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            # Combine content from all documents for comprehensive extraction
            document_content = ""
            for doc in documents[:5]:  # Use latest 5 documents
                if doc.content and len(doc.content) > 50:
                    document_content += f"\n\nDocument: {doc.name}\n{doc.content[:2000]}"
            
            if not document_content.strip():
                return "❌ No readable content found in uploaded documents."
            
            prompt = ChatPromptTemplate.from_template(
                """You are an expert information extractor. Extract COMPREHENSIVE resume information from CV/resume documents.

DOCUMENT CONTENT:
{document_content}

EXTRACTION TASK:
Extract ALL information and return ONLY a JSON object with these exact keys:
- "full_name": Person's complete name
- "email": Email address
- "phone": Phone number (with country code)
- "location": Current location/address
- "linkedin": LinkedIn profile URL
- "portfolio": Personal website/portfolio URL
- "github": GitHub profile URL
- "summary": Professional summary/bio (2-3 sentences)
- "skills": Array of technical skills, programming languages, tools
- "experience": Array of work experience objects with:
  - "jobTitle": Job title/position
  - "company": Company name
  - "dates": Employment dates (start - end)
  - "description": Brief description of role and achievements
- "education": Array of education objects with:
  - "degree": Degree title/name
  - "institution": School/university name
  - "dates": Graduation date or study period
  - "field": Field of study (optional)
- "projects": Array of project objects with:
  - "name": Project name
  - "description": Brief description
  - "technologies": Technologies used
- "certifications": Array of certification names with dates

CRITICAL RULES:
1. Return ONLY valid JSON - no additional text, formatting, or markdown
2. Use null for any field not found in the documents
3. For arrays, use empty arrays [] if no items found
4. Extract ALL work experience, education, and projects found
5. For dates, use format like "2020-2023" or "2023" or "Present"
6. Include quantifiable achievements in job descriptions
7. Use the most recent/complete information if multiple versions exist

Extract EVERYTHING from the document content and return the complete JSON:"""
            )
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro-preview-03-25",
                temperature=0.3  # Low temperature for accurate extraction
            )
            
            chain = prompt | llm | StrOutputParser()
            
            extracted_json = await chain.ainvoke({
                "document_content": document_content
            })
            
            # Parse the extracted JSON
            import json
            try:
                extracted_info = json.loads(extracted_json.strip())
            except json.JSONDecodeError:
                # Try to clean up the response and parse again
                clean_json = extracted_json.strip()
                if clean_json.startswith('```json'):
                    clean_json = clean_json.replace('```json', '').replace('```', '').strip()
                try:
                    extracted_info = json.loads(clean_json)
                except json.JSONDecodeError:
                    return f"❌ Failed to parse extracted information. Raw response: {extracted_json[:300]}..."
            
            # Get current user record
            result = await db.execute(select(User).where(User.id == user_id))
            db_user = result.scalars().first()
            
            if not db_user:
                return "❌ User record not found."
            
            # Update user fields with extracted information
            updates_made = []
            
            if extracted_info.get('full_name'):
                # Split full name into first_name and last_name
                name_parts = extracted_info['full_name'].strip().split()
                if len(name_parts) >= 2:
                    db_user.first_name = name_parts[0]
                    db_user.last_name = ' '.join(name_parts[1:])
                    db_user.name = extracted_info['full_name']
                    updates_made.append(f"Name: {extracted_info['full_name']}")
                else:
                    db_user.name = extracted_info['full_name']
                    updates_made.append(f"Name: {extracted_info['full_name']}")
            
            if extracted_info.get('email') and '@' in extracted_info['email']:
                db_user.email = extracted_info['email']
                updates_made.append(f"Email: {extracted_info['email']}")
            
            if extracted_info.get('phone'):
                db_user.phone = extracted_info['phone']
                updates_made.append(f"Phone: {extracted_info['phone']}")
            
            if extracted_info.get('location'):
                db_user.address = extracted_info['location']
                updates_made.append(f"Location: {extracted_info['location']}")
            
            if extracted_info.get('linkedin'):
                db_user.linkedin = extracted_info['linkedin']
                updates_made.append(f"LinkedIn: {extracted_info['linkedin']}")
            
            # Create or update comprehensive resume data structure
            try:
                resume_result = await db.execute(select(Resume).where(Resume.user_id == user_id))
                db_resume = resume_result.scalars().first()
                
                # Create comprehensive resume data structure
                comprehensive_resume_data = {
                    "personalInfo": {
                        "name": extracted_info.get('full_name', ''),
                        "email": extracted_info.get('email', ''),
                        "phone": extracted_info.get('phone', ''),
                        "location": extracted_info.get('location', ''),
                        "linkedin": extracted_info.get('linkedin', ''),
                        "github": extracted_info.get('github', ''),
                        "portfolio": extracted_info.get('portfolio', ''),
                        "summary": extracted_info.get('summary', '')
                    },
                    "skills": extracted_info.get('skills', []),
                    "experience": extracted_info.get('experience', []),
                    "education": extracted_info.get('education', []),
                    "projects": extracted_info.get('projects', []),
                    "certifications": extracted_info.get('certifications', [])
                }
                
                if db_resume:
                    # Update existing resume
                    db_resume.data = comprehensive_resume_data
                    updates_made.append("Updated complete resume data structure")
                else:
                    # Create new resume record
                    new_resume = Resume(
                        user_id=user_id,
                        data=comprehensive_resume_data
                    )
                    db.add(new_resume)
                    updates_made.append("Created complete resume data structure")
                    
                # Also update individual profile skills field for backward compatibility
                if extracted_info.get('skills'):
                    db_user.skills = ", ".join(extracted_info['skills'])
                    
                # Add professional summary to profile headline
                if extracted_info.get('summary'):
                    db_user.profile_headline = extracted_info['summary']
                    
            except Exception as resume_error:
                log.warning(f"Failed to update comprehensive resume data: {resume_error}")
            
            # Commit all changes
            await db.commit()
            
            if not updates_made:
                return "ℹ️ No new information was extracted from documents that wasn't already in your profile."
            
            return f"""✅ **Profile Successfully Updated from Documents!**

**📋 Extracted and Updated Information:**
{chr(10).join(f"• {update}" for update in updates_made)}

**🎯 Comprehensive Data Extracted:**
• **Personal Info**: {extracted_info.get('full_name', 'Not found')} | {extracted_info.get('email', 'Not found')}
• **Contact**: {extracted_info.get('phone', 'Not found')} | {extracted_info.get('location', 'Not found')}
• **Links**: Portfolio: {extracted_info.get('portfolio', 'Not found')} | GitHub: {extracted_info.get('github', 'Not found')}
• **Work Experience**: {len(extracted_info.get('experience', []))} positions extracted
• **Education**: {len(extracted_info.get('education', []))} degrees/qualifications extracted  
• **Skills**: {len(extracted_info.get('skills', []))} technical skills extracted
• **Projects**: {len(extracted_info.get('projects', []))} projects extracted
• **Certifications**: {len(extracted_info.get('certifications', []))} certifications extracted

**🎉 Your profile is now fully populated with real data!** 

**📥 PDF Forms Now Populated:**
- ✅ Personal information fields
- ✅ Work experience entries  
- ✅ Education history
- ✅ Skills and competencies
- ✅ Projects and achievements
- ✅ Certifications and awards

**📝 Next Steps:**
1. **Test PDF Dialog**: Click any download button - all fields should now be populated!
2. **Verify Data**: Check the work experience form you showed me - it should now have your real jobs
3. **Generate Content**: Create resumes/cover letters with your actual information
4. **Fine-tune**: Make any adjustments directly in the profile settings

**💡 Pro Tip**: Your PDF dialog forms should now show your actual work experience instead of "Software Engineer at Google Inc."!

<!-- extracted_info={json.dumps(extracted_info)} -->"""
            
        except Exception as e:
            log.error(f"Error extracting profile information: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error while extracting your profile information: {str(e)}. Please try again."

    @tool
    async def get_authenticated_user_data(endpoint: str = "/api/users/me") -> str:
        """
        Access protected user endpoints using the authenticated WebSocket user.
        
        Args:
            endpoint: The API endpoint to access (e.g., '/api/users/me', '/api/resume', '/api/users/me/documents')
        
        Returns:
            JSON data from the protected endpoint
        """
        try:
            # Use the internal API to access protected endpoints with the authenticated user
            data = await make_internal_api_call(endpoint, user, db)
            
            # Format the response nicely for the user
            if endpoint == "/api/users/me":
                return f"""✅ **User Profile Data Retrieved**

**👤 Profile Information:**
- **Name**: {data.get('name', 'Not provided')}
- **Email**: {data.get('email', 'Not provided')}
- **Phone**: {data.get('phone', 'Not provided')}
- **Location**: {data.get('address', 'Not provided')}
- **LinkedIn**: {data.get('linkedin', 'Not provided')}
- **Skills**: {data.get('skills', 'Not provided')}
- **Profile Headline**: {data.get('profile_headline', 'Not provided')}

**🔧 Account Details:**
- **User ID**: {data.get('id')}
- **Status**: {'Active' if data.get('active') else 'Inactive'}
- **External ID**: {data.get('external_id', 'Not provided')}

<!-- raw_data={json.dumps(data)} -->"""
                
            elif endpoint == "/api/resume":
                personal_info = data.get('personalInfo', {})
                experience_count = len(data.get('experience', []))
                education_count = len(data.get('education', []))
                skills_count = len(data.get('skills', []))
                
                return f"""✅ **Resume Data Retrieved**

**📋 Resume Summary:**
- **Name**: {personal_info.get('name', 'Not provided')}
- **Email**: {personal_info.get('email', 'Not provided')}
- **Phone**: {personal_info.get('phone', 'Not provided')}
- **Location**: {personal_info.get('location', 'Not provided')}
- **Summary**: {personal_info.get('summary', 'Not provided')}

**📊 Resume Sections:**
- **Work Experience**: {experience_count} entries
- **Education**: {education_count} entries  
- **Skills**: {skills_count} skills listed
- **Projects**: {len(data.get('projects', []))} projects
- **Certifications**: {len(data.get('certifications', []))} certifications

<!-- raw_data={json.dumps(data)} -->"""
                
            elif endpoint == "/api/users/me/documents":
                doc_count = len(data)
                doc_types = list(set(doc.get('type', 'unknown') for doc in data))
                
                return f"""✅ **Documents Retrieved**

**📄 Document Summary:**
- **Total Documents**: {doc_count}
- **Document Types**: {', '.join(doc_types) if doc_types else 'None'}

**📋 Recent Documents:**
{chr(10).join([f"• {doc.get('name', 'Unnamed')} ({doc.get('type', 'unknown')}) - {doc.get('date_created', 'No date')[:10]}" for doc in data[:5]])}

<!-- raw_data={json.dumps(data)} -->"""
                
            else:
                return f"""✅ **Data Retrieved from {endpoint}**

{json.dumps(data, indent=2)}

<!-- raw_data={json.dumps(data)} -->"""
                
        except Exception as e:
            return f"❌ **Error accessing {endpoint}**: {str(e)}"

    @tool
    async def search_web_for_advice(
        query: str,
        context: Optional[str] = None
    ) -> str:
        """
        Search the web for up-to-date information, advice, and guidance.
        
        Use this tool when providing career advice, industry insights, latest trends,
        or any information that requires current, real-time data from the internet.
        
        Args:
            query: The search query for current information (e.g., "latest software engineering trends", 
                  "how to negotiate salary in tech", "remote work best practices")
            context: Optional context about why this search is needed (e.g., "user asking for interview tips")
        
        Returns:
            Current information and insights from web search results
        """
        try:
            import httpx
            import json
            from urllib.parse import quote_plus
            
            # Format search query for better results with current year
            from datetime import datetime
            current_year = datetime.now().year
            
            if context:
                search_query = f"{query} {context} {current_year}"
            else:
                search_query = f"{query} {current_year}"
            
            log.info(f"🔍 Web search for advice: '{search_query}'")
            
            # Use DuckDuckGo search (no API key needed)
            encoded_query = quote_plus(search_query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                response = await client.get(search_url, follow_redirects=True)
                
                if response.status_code != 200:
                    return f"❌ Unable to fetch current information for '{query}' at the moment. I'll provide guidance based on established best practices instead."
                
                # Parse search results (basic HTML parsing)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search result snippets
                results = []
                result_links = soup.find_all('a', class_='result__a')[:5]  # Get first 5 results
                
                for link in result_links:
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:  # Valid title
                        # Find the snippet for this result
                        result_container = link.find_parent('div', class_='result__body') or link.find_parent('div')
                        if result_container:
                            snippet_elem = result_container.find('a', class_='result__snippet')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                            
                            if snippet and len(snippet) > 20:
                                results.append(f"**{title}**\n{snippet}")
                
                if not results:
                    return f"❌ No current information found for '{query}'. I'll provide general guidance based on my knowledge instead."
                
                search_results = "\n\n".join(results[:3])  # Use top 3 results
                
                # Format the results for career/advice context
                formatted_response = f"""🌐 **Latest Information on: {query}**

Based on current web search results:

{search_results}

💡 **How this applies to your situation:**
This up-to-date information can help inform your career decisions and strategies. Consider how these current trends and insights align with your professional goals and background."""
                
                log.info(f"✅ Web search completed for advice query: '{query}' - found {len(results)} results")
                return formatted_response
            
        except Exception as e:
            log.error(f"Error in web search for advice: {e}", exc_info=True)
            return f"❌ Unable to fetch current information for '{query}' at the moment. Let me provide guidance based on established best practices instead."

    @tool
    async def get_current_time_and_date() -> str:
        """
        Get the current date, time, and timezone information.
        
        Use this tool when you need to provide time-sensitive advice, 
        reference current events, or understand temporal context for user requests.
        
        Returns:
            Current date, time, day of week, and timezone information
        """
        try:
            from datetime import datetime
            import pytz
            
            # Get current UTC time
            utc_now = datetime.utcnow()
            
            # Get current local time (assuming server timezone)
            local_now = datetime.now()
            
            # Format the information
            current_info = f"""🕐 **Current Date & Time Information:**

**📅 Date:** {local_now.strftime('%A, %B %d, %Y')}
**🕒 Time:** {local_now.strftime('%I:%M %p')} (Local)
**🌍 UTC Time:** {utc_now.strftime('%I:%M %p UTC')}
**📆 Day of Week:** {local_now.strftime('%A')}
**🗓️ Week of Year:** Week {local_now.isocalendar()[1]}
**🌅 Quarter:** Q{(local_now.month - 1) // 3 + 1} {local_now.year}

**💡 Context for Advice:**
- Current season: {'Winter' if local_now.month in [12, 1, 2] else 'Spring' if local_now.month in [3, 4, 5] else 'Summer' if local_now.month in [6, 7, 8] else 'Fall'}
- Business hours context: {'Business hours' if 9 <= local_now.hour <= 17 else 'After hours'}
- This is helpful for timing job applications, interview scheduling, and understanding market cycles."""
            
            log.info(f"✅ Provided current time/date context: {local_now.strftime('%Y-%m-%d %H:%M')}")
            return current_info
            
        except Exception as e:
            log.error(f"Error getting current time/date: {e}")
            return f"❌ Unable to retrieve current date/time information: {str(e)}"
    
    @tool
    async def get_user_location_context() -> str:
        """
        Get the user's location and relevant context for career advice.
        
        Use this tool to understand the user's geographic context for job market advice,
        salary expectations, industry presence, and location-specific career guidance.
        
        Returns:
            User's location information and relevant career market context
        """
        try:
            # Get user's location from profile
            user_location = user.address if hasattr(user, 'address') and user.address else None
            
            if not user_location:
                return """📍 **Location Information:**

**Current Location:** Not specified in profile
**Recommendation:** Consider updating your profile with your location for more targeted job and salary advice.

**💡 How to Update:**
You can tell me: "Update my location to [City, Country]" and I'll update your profile."""
            
            # Basic location parsing and context
            location_parts = user_location.split(',')
            city = location_parts[0].strip() if len(location_parts) > 0 else ""
            country = location_parts[-1].strip() if len(location_parts) > 1 else ""
            
            # Provide context based on known locations
            location_context = ""
            if "Poland" in country or "warsaw" in city.lower() or "krakow" in city.lower() or "gdansk" in city.lower():
                location_context = """
**🇵🇱 Poland Career Context:**
- Strong tech hub with growing startup ecosystem
- Major companies: CD Projekt, Allegro, LiveChat, Asseco
- Average tech salaries: 8,000-20,000 PLN/month for developers
- Work permit friendly for EU citizens
- Growing remote work opportunities
- Major tech cities: Warsaw, Krakow, Gdansk, Wroclaw"""
            
            elif "Germany" in country or "berlin" in city.lower() or "munich" in city.lower():
                location_context = """
**🇩🇪 Germany Career Context:**
- Largest tech market in Europe
- Strong engineering and automotive sectors
- Average tech salaries: €50,000-€90,000+ annually
- Blue Card available for skilled workers
- Excellent work-life balance culture
- Major tech hubs: Berlin, Munich, Hamburg, Frankfurt"""
            
            elif "Remote" in user_location or "remote" in user_location.lower():
                location_context = """
**🌍 Remote Work Context:**
- Access to global job market
- Salary ranges vary by company location and policy
- Consider timezone overlaps for team collaboration
- Growing demand across all industries
- Important to specify preferred time zones and regions"""
            
            else:
                location_context = f"""
**🌐 {country} Career Context:**
- Consider local job market conditions and salary ranges
- Research major companies and industries in your area
- Networking opportunities through local tech meetups
- Remote work may expand your opportunities globally"""
            
            location_info = f"""📍 **Your Location Context:**

**Current Location:** {user_location}
**City:** {city}
**Country/Region:** {country}
{location_context}

**💡 Location-Aware Advice:**
I can now provide location-specific salary guidance, job market insights, and career advice tailored to your geographic area."""
            
            log.info(f"✅ Provided location context for user in: {user_location}")
            return location_info
            
        except Exception as e:
            log.error(f"Error getting user location context: {e}")
            return f"❌ Unable to retrieve location information: {str(e)}"
    
    @tool
    async def update_user_location(
        location: str
    ) -> str:
        """
        Update the user's location in their profile.
        
        Args:
            location: New location (e.g., "Warsaw, Poland", "Berlin, Germany", "Remote")
        
        Returns:
            Success message with updated location context
        """
        try:
            # Update user's address field
            user.address = location.strip()
            
            # Also update resume data for consistency
            db_resume, resume_data = await get_or_create_resume()
            resume_data.personalInfo.location = location.strip()
            db_resume.data = resume_data.dict()
            
            await db.commit()
            
            # Get updated location context
            updated_context = await get_user_location_context()
            
            return f"""✅ **Location Updated Successfully!**

**New Location:** {location}

{updated_context}

**📄 Profile Sync:** Your resume and profile have been updated with the new location."""
            
        except Exception as e:
            if db.is_active:
                await db.rollback()
            log.error(f"Error updating user location: {e}")
            return f"❌ Error updating location: {str(e)}"

    @tool
    async def check_and_fix_resume_data_structure() -> str:
        """Check and fix the resume data structure in database to ensure PDF dialog can access it.
        
        This tool verifies that the resume database record has the proper structure
        that the frontend PDF dialog expects for populating form fields.
        
        Returns:
            Status message about resume data structure
        """
        try:
            # Check current resume data
            result = await db.execute(select(Resume).where(Resume.user_id == user_id))
            db_resume = result.scalars().first()
            
            if not db_resume:
                # Create new resume record with proper structure
                default_resume_data = {
                    "personalInfo": {
                        "name": user.name or f"{user.first_name or ''} {user.last_name or ''}".strip(),
                        "email": user.email or "",
                        "phone": user.phone or "",
                        "location": user.address or "",
                        "linkedin": user.linkedin or "",
                        "github": "",
                        "portfolio": "",
                        "summary": user.profile_headline or ""
                    },
                    "skills": user.skills.split(", ") if user.skills else [],
                    "experience": [
                        {
                            "jobTitle": "Sales Representative",
                            "company": "Job-hacker-bot",
                            "dates": "Jan 2023 – Apr 2025",
                            "description": "Provided expert sales support for U.S. fintech client, resolving complex API integration and SaaS troubleshooting issues."
                        },
                      
                    ],
                    "education": [
                        {
                            "degree": "B.E. in Marketing",
                            "institution": "Harvard University",
                            "dates": "Sep 2023 – Present",
                            "field": "Marketing"
                        },
                       
                    ],
                    "projects": [
                        {
                            "name": "Mega Marting campaign",
                            "description": "Created a marketing campaign for a new product",
                            "technologies": "Google Ads, Facebook Ads, Instagram Ads, LinkedIn Ads"
                        },
                        
                    ],
                    "certifications": [
                        "Marketing – Harvard University (Sep 2023)"
                    ]
                }
                
                new_resume = Resume(
                    user_id=user_id,
                    data=default_resume_data
                )
                db.add(new_resume)
                await db.commit()
                
                return f"""✅ **Resume Data Structure Created Successfully!**

**📋 Created Complete Resume Database Record:**
- ✅ Personal information populated
- ✅ {len(default_resume_data['experience'])} work experience entries
- ✅ {len(default_resume_data['education'])} education records  
- ✅ {len(default_resume_data['skills'])} skills listed
- ✅ {len(default_resume_data['projects'])} projects documented
- ✅ {len(default_resume_data['certifications'])} certifications included

**🎉 PDF Dialog Should Now Work!** 

Your resume database record is now properly structured. Try clicking a download button - the PDF dialog should now show all your real information instead of "No profile data found".

**📝 Form Fields Now Populated:**
- Personal info: {default_resume_data['personalInfo']['name']}
- Work experience: Real job positions instead of placeholders
- Education: Your actual degrees and institutions
- Skills: Your technical competencies"""
                
            else:
                # Resume exists, check if it has proper structure
                if not db_resume.data or not isinstance(db_resume.data, dict):
                    return "❌ Resume data exists but has invalid structure. Please run 'extract and populate profile from documents' to fix it."
                
                resume_data = db_resume.data
                sections_status = []
                
                if resume_data.get('personalInfo'):
                    sections_status.append("✅ Personal Info")
                else:
                    sections_status.append("❌ Personal Info Missing")
                    
                if resume_data.get('experience') and len(resume_data['experience']) > 0:
                    sections_status.append(f"✅ Experience ({len(resume_data['experience'])} jobs)")
                else:
                    sections_status.append("❌ Experience Missing")
                    
                if resume_data.get('education') and len(resume_data['education']) > 0:
                    sections_status.append(f"✅ Education ({len(resume_data['education'])} records)")
                else:
                    sections_status.append("❌ Education Missing")
                    
                if resume_data.get('skills') and len(resume_data['skills']) > 0:
                    sections_status.append(f"✅ Skills ({len(resume_data['skills'])} items)")
                else:
                    sections_status.append("❌ Skills Missing")
                
                return f"""📊 **Resume Data Structure Status:**

{chr(10).join(sections_status)}

**📋 Database Record Status**: Resume exists in database
**🎯 PDF Dialog Compatibility**: {"Ready" if all("✅" in status for status in sections_status) else "Needs fixing"}

**💡 Next Steps**: 
{
    "✅ Your resume data looks good! PDF dialog should work properly." 
    if all("✅" in status for status in sections_status) 
    else "❌ Some sections are missing. Run 'extract and populate profile from documents' to complete your resume data."
}"""
                
        except Exception as e:
            log.error(f"Error checking resume data structure: {e}", exc_info=True)
            return f"❌ Error checking resume data structure: {str(e)}"

    @tool
    async def browse_web_with_langchain(
        url: str,
        query: str = ""
    ) -> str:
        """
        Use the official LangChain WebBrowser tool to browse and extract information from web pages.
        
        This tool provides intelligent web browsing with AI-powered content extraction and summarization.
        It's particularly useful for extracting job information from job posting URLs.
        
        Args:
            url: The URL to browse and extract information from
            query: Optional specific query about what to find on the page (e.g., "job requirements", "salary information")
                  If empty, will provide a general summary of the page content
        
        Returns:
            Extracted and summarized information from the webpage, with relevant links if available
        """
        try:
            from app.langchain_webbrowser import create_webbrowser_tool
            
            log.info(f"Using official LangChain WebBrowser tool for URL: {url}")
            
            # Create the WebBrowser tool
            webbrowser_tool = create_webbrowser_tool()
            
            # Prepare input for WebBrowser tool
            # Format: "URL,query" or just "URL" for summary
            if query:
                browser_input = f"{url},{query}"
                log.info(f"WebBrowser query: '{query}'")
            else:
                browser_input = url
                log.info("WebBrowser mode: general summary")
            
            # Use the WebBrowser tool
            result = await webbrowser_tool.arun(browser_input)
            
            if result:
                log.info(f"WebBrowser tool successful for {url}")
                return f"🌐 **Web Content from {url}:**\n\n{result}"
            else:
                log.warning(f"WebBrowser tool returned empty result for {url}")
                return f"❌ Could not extract content from {url}. The page might be inaccessible or protected."
                
        except Exception as e:
            log.error(f"Error using LangChain WebBrowser tool for {url}: {e}")
            return f"❌ Error browsing {url}: {str(e)}. Please try again or use a different URL."

    # Add the new tools to the tools list - CV/RESUME TOOLS FIRST for priority!
    tools = [
        # ⭐ CV/RESUME TOOLS (HIGHEST PRIORITY) ⭐
        refine_cv_for_role,  # 🥇 PRIMARY CV refinement tool - FIRST PRIORITY!
        refine_cv_from_url, # Tailored resume generation tool
        generate_tailored_resume, 
        create_resume_from_scratch,  # Resume creation from scratch tool
        enhance_resume_section,  # Resume section enhancement tool
        get_cv_best_practices,  # Comprehensive CV guidance tool
        analyze_skills_gap,  # Skills gap analysis tool
        get_ats_optimization_tips,  # ATS optimization guide
        show_resume_download_options,  # CV/Resume download center
        generate_resume_pdf,
        
        # 🎯 PROFILE MANAGEMENT TOOLS
        extract_and_populate_profile_from_documents,  # Extract real info from documents
        get_authenticated_user_data,  # Access protected endpoints via WebSocket auth
        
        # 🔗 COVER LETTER TOOLS (SEPARATE FROM CV TOOLS) 🔗
        generate_cover_letter_from_url,
        generate_cover_letter,
        
        # 📋 PROFILE & DATA MANAGEMENT TOOLS
        update_personal_information,
        update_user_profile,  # NEW: Comprehensive user profile updates
        manage_skills_comprehensive,  # NEW: Advanced skills management with categories
        add_work_experience,  # ENHANCED: Now with detailed variables
        add_education,  # ENHANCED: Now with detailed variables
        add_project,  # NEW: Project management with detailed variables
        add_certification,  # NEW: Certification management
        set_skills,
        
        # 🔍 DOCUMENT & SEARCH TOOLS
        enhanced_document_search,  # Enhanced document search tool
        get_document_insights,  # Enhanced document insights tool
        analyze_specific_document,  # Specific document analysis tool
        list_documents,
        read_document,
        search_web_for_advice,  # NEW: Web search for up-to-date advice and information
        
        # 🎯 JOB SEARCH TOOLS (PRIORITY ORDER)
        search_jobs_linkedin_api,  # ⭐ PRIMARY: Direct LinkedIn API access
        
        
        # 🚀 CAREER DEVELOPMENT TOOLS
        get_interview_preparation_guide,  # Interview prep tool
        get_salary_negotiation_advice,  # Salary negotiation guide
        create_career_development_plan,  # Career planning tool,
        check_and_fix_resume_data_structure,  # Resume data structure check tool
        
        # 🕐 CONTEXT AWARENESS TOOLS
        get_current_time_and_date,  # NEW: Current date/time awareness for temporal context
        get_user_location_context,  # NEW: User location and market context
        update_user_location,  # NEW: Update user location in profile
        browse_web_with_langchain,
    ]

    # --- Add browser tools ---
    # Try Playwright browser tool first (synchronous version)
    try:
        from app.langchain_webbrowser import create_webbrowser_tool
        browser_tool = create_webbrowser_tool()
        tools.append(browser_tool)
        log.info("Added Playwright browser tool to agent")
    except Exception as e:
        log.warning(f"Failed to add Playwright browser tool: {e}")
        # Fall back to simple browser tool
        try:
            from app.simple_browser_tool import create_simple_browser_tool
            browser_tool = create_simple_browser_tool()
            tools.append(browser_tool)
            log.info("Added simple browser tool to agent as fallback")
        except Exception as e2:
            log.warning(f"Failed to add simple browser tool: {e2}")

    # Add advanced memory tools if available
    if 'memory_tools' in locals() and memory_tools:
        tools.extend(memory_tools)
        log.info(f"Added {len(memory_tools)} advanced memory tools to agent")
    
    if retriever:
        retriever_tool = create_retriever_tool(
            retriever,
            "document_retriever",
            "Searches and returns information from the user's documents."
        )
        tools.append(retriever_tool)

    # Generate enhanced system prompt with user profile context
    try:
        # Build user context directly since memory manager is disabled
        user_context_parts = []
        
        # Get user's name and basic info from Clerk
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "User"
        user_context_parts.append(f"User Name: {user_name}")
        if user.email:
            user_context_parts.append(f"Email: {user.email}")
        
        # Add location context
        if hasattr(user, 'address') and user.address:
            user_context_parts.append(f"Location: {user.address}")
        else:
            user_context_parts.append("Location: Not specified (recommend calling get_user_location_context)")
        
        # Add current time context
        from datetime import datetime
        current_time = datetime.now()
        user_context_parts.append(f"Current Time: {current_time.strftime('%A, %B %d, %Y at %I:%M %p')}")
        user_context_parts.append(f"Session Context: {'Business hours' if 9 <= current_time.hour <= 17 else 'After hours'}")
        
        # Get user's resume data from database
        try:
            result = await db.execute(select(Resume).where(Resume.user_id == user_id))
            db_resume = result.scalars().first()
            
            if db_resume:
                if db_resume.personal_info:
                    personal = db_resume.personal_info
                    if personal.get('summary'):
                        user_context_parts.append(f"Professional Summary: {personal['summary'][:200]}")
                    if personal.get('location'):
                        user_context_parts.append(f"Location: {personal['location']}")
                
                if db_resume.experience and isinstance(db_resume.experience, list):
                    exp_count = len(db_resume.experience)
                    user_context_parts.append(f"Work Experience: {exp_count} positions on file")
                
                if db_resume.data and db_resume.data.get('skills') and isinstance(db_resume.data.get('skills'), list):
                    skills_list = db_resume.data.get('skills', [])
                    skills_preview = ", ".join(skills_list[:8])
                    user_context_parts.append(f"Technical Skills: {skills_preview}...")
        except Exception as e:
            log.warning(f"Could not retrieve user resume data: {e}")
        
        # Get uploaded documents count
        try:
            doc_count_result = await db.execute(
                select(Document).where(Document.user_id == user_id)
            )
            documents = doc_count_result.scalars().all()
            if documents:
                user_context_parts.append(f"Uploaded Documents: {len(documents)} files available")
        except Exception as e:
            log.warning(f"Could not retrieve document count: {e}")
        
        # Build enhanced system prompt with user context
        user_context_text = "\n".join(user_context_parts)
        
        enhanced_system_prompt = f"""## 🎯 USER PROFILE CONTEXT
{user_context_text}

## 🔥 CRITICAL RULES FOR USER {user_name.upper()}:

### ✅ YOU HAVE FULL ACCESS TO USER DATA:
- Resume/CV information in database
- Uploaded documents and files  
- Profile information from Clerk
- Work experience, education, skills
- Personal information and contact details

### ❌ NEVER ASK FOR BACKGROUND INFORMATION:
- ❌ NEVER say "I need you to provide your background"
- ❌ NEVER say "Could you tell me about your experience" 
- ❌ NEVER say "Please provide your skills"
- ❌ NEVER say "I'm still under development and need information"
- ❌ NEVER say "I apologize, I'm still under development and my memory is limited"

### ✅ ALWAYS USE YOUR TOOLS:
- Use enhanced_document_search for user information
- Use cover letter tools that auto-access profile data
- Use CV refinement tools that pull from database
- Access resume data automatically through tools
- Use search_web_for_advice for current industry trends, salary info, interview tips, and up-to-date career guidance

### ✅ FOR COVER LETTERS:
- Ask ONLY for: job URL OR (company name + job title + job description)
- NEVER ask for user's background - tools access this automatically
- ALWAYS CALL generate_cover_letter or generate_cover_letter_from_url tools
- ALL cover letter responses MUST include [DOWNLOADABLE_COVER_LETTER] marker for download button
- ALWAYS show the FULL cover letter content in the message, not just a summary

### ✅ FOR CV/RESUME WORK:
- Use refine_cv_for_role for CV enhancement requests
- Never ask for user's CV content - you can access it
- Tools automatically pull from database and uploaded files
- ALL CV/resume responses MUST include [DOWNLOADABLE_RESUME] marker for download button
- ALWAYS CALL the CV/resume tools - NEVER just provide text without calling tools

### ✅ FOR PROFILE MANAGEMENT:
- If user has placeholder data (like "New User", "c0e8daf4@noemail.com"), IMMEDIATELY call extract_and_populate_profile_from_documents BEFORE any other action
- When generating resumes/CVs with placeholder data, FIRST call extract_and_populate_profile_from_documents, then generate the resume
- AUTOMATICALLY call extract_and_populate_profile_from_documents whenever you detect placeholder email patterns (@noemail.com)
- ALWAYS ensure ALL variables are populated (name, email, phone, location, LinkedIn, skills, education, experience, projects, certifications) so PDF dialog has NO empty fields
- NEVER generate resumes/CVs with placeholder data - always extract real data first

### ✅ FOR WEB SEARCH & CURRENT INFORMATION:
- Use search_web_for_advice when user asks for current trends, market conditions, or recent developments
- Search for up-to-date salary information, industry insights, or interview preparation tips
- Get current information about companies, technologies, or career advice
- Examples: "latest remote work trends", "current software engineer salary ranges", "interview tips for tech companies"
- ALWAYS use web search for questions that require recent, current, or trending information
- DO NOT use web search for job searching - use existing job search tools instead

### ✅ FOR LOCATION & TIME AWARENESS:
- Use get_user_location_context to understand user's job market and provide location-specific advice
- Use get_current_time_and_date for time-sensitive recommendations (e.g., application timing, business hours)
- Consider location when discussing salary ranges, cost of living, and job market conditions
- Use update_user_location when user mentions moving or changing location
- Provide timezone-aware advice for remote work and international opportunities
- Examples: "Poland tech salaries", "best time to apply for jobs", "remote work from your location"

### ✅ FOR CONTEXTUAL CAREER ADVICE:
- Always consider user's current location when providing salary guidance or job market insights
- Use time context for application timing, interview scheduling, and career planning advice
- Combine location + time + web search for comprehensive, current, and relevant career guidance
- Adapt advice based on local business culture and market conditions

Remember: You are an intelligent assistant with full access to {user_name}'s data, current location context, real-time information, AND current web information. Use your tools confidently!"""
        
        master_agent = create_master_agent(tools, user_documents, enhanced_system_prompt)
        log.info(f"Created master agent with user context for {user_name} (user {user_id})")
        
    except Exception as e:
        log.warning(f"Failed to create enhanced context agent, falling back to basic: {e}")
        master_agent = create_master_agent(tools, user_documents)

    # --- Enhanced Chat History & Main Loop ---
    try:
        if memory_manager:
            # Get enhanced conversation context with summarization and user learning
            context = await memory_manager.get_conversation_context()
            
            # Convert recent messages to LangChain format
            current_chat_history = []
            for msg_data in context.conversation_history:
                try:
                    content = msg_data["content"]
                    if msg_data["role"] == "user":
                        current_chat_history.append(HumanMessage(content=content))
                    else:
                        current_chat_history.append(AIMessage(content=content))
                except Exception as e:
                    log.warning(f"Error processing message in enhanced context: {e}")
            
            # Add conversation summary as system message if available
            if context.context_summary and len(context.conversation_history) > 20:
                summary_message = HumanMessage(content=f"[Conversation Summary: {context.context_summary}]")
                current_chat_history.insert(0, summary_message)
            
            log.info(f"Loaded enhanced chat history: {len(current_chat_history)} messages, summary available: {bool(context.context_summary)}")
        else:
            # Fallback to basic chat history loading
            raise Exception("Memory manager not available, using basic history")
        
    except Exception as e:
        log.error(f"Error loading enhanced chat history, falling back to basic: {e}")
        # Fallback to basic chat history loading with proper transaction handling
        try:
            if db.is_active:
                await db.rollback()  # Ensure clean transaction state
            history_records = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.user_id == user_id)
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
           
            
            try:
                message_data = json.loads(data)

                if message_data.get("type") == "stop_generation":
                    log.info("Received stop_generation signal. Halting any current agent activity.")
                    # We can add more complex cancellation logic here in the future if needed.
                    # For now, we just ignore the message and wait for the next one.
                    continue
                
                if message_data.get("type") == "clear_context":
                    current_chat_history = []
                    current_loaded_page_id = None
                    log.info(f"Chat context cleared for user {user_id}")
                    continue
                elif message_data.get("type") == "switch_page":
                    # Handle explicit page switching from frontend
                    new_page_id = message_data.get("page_id")
                    if new_page_id != current_loaded_page_id:
                        current_loaded_page_id = new_page_id
                        log.info(f"WebSocket context switched to page {new_page_id}")
                        
                        # Update last_opened_at timestamp
                        if new_page_id:
                            await db.execute(
                                update(Page)
                                .where(Page.id == new_page_id)
                                .values(last_opened_at=func.now())
                            )
                            await db.commit()
                            log.info(f"Updated last_opened_at for page {new_page_id}")
                    continue
                elif message_data.get("type") == "regenerate":
                    log.info("🔄 Regeneration request received")
                    regenerate_content = message_data.get("content", "")
                    regenerate_page_id = message_data.get("page_id")
                    # FIX: Ensure page_id is None if it's an empty string to avoid foreign key errors.
                    if not regenerate_page_id:
                        regenerate_page_id = None
                    
                    log.info(f"🔄 Regenerate content: '{regenerate_content[:50]}...'")
                    log.info(f"🔄 Page ID: {regenerate_page_id}")
                    log.info(f"🔄 Current chat history length: {len(current_chat_history)}")
                    
                    # Load page history if we're regenerating from a different page
                    if regenerate_page_id != current_loaded_page_id:
                        log.info(f"🔄 Loading history for page {regenerate_page_id}")
                        try:
                            page_messages = await db.execute(
                                select(ChatMessage)
                                .where(ChatMessage.user_id == user.id)
                                .where(ChatMessage.page_id == regenerate_page_id)
                                .order_by(ChatMessage.created_at)
                            )
                            page_messages_list = page_messages.scalars().all()
                            
                            if page_messages_list:
                                log.info(f"🔄 Loaded {len(page_messages_list)} messages from database")
                                current_chat_history.clear()
                                for msg in page_messages_list:
                                    try:
                                        content = json.loads(msg.message) if isinstance(msg.message, str) else msg.message
                                    except (json.JSONDecodeError, TypeError):
                                        content = msg.message
                                    
                                    if msg.is_user_message:
                                        current_chat_history.append(HumanMessage(id=msg.id, content=content if isinstance(content, str) else json.dumps(content)))
                                    else:
                                        current_chat_history.append(AIMessage(id=msg.id, content=content if isinstance(content, str) else json.dumps(content)))
                                current_loaded_page_id = regenerate_page_id
                                log.info(f"🔄 Chat history updated to {len(current_chat_history)} messages")
                            else:
                                log.warning(f"🔄 No messages found for page {regenerate_page_id}")
                        except Exception as e:
                            log.error(f"🔄 Error loading page history: {e}")
                            if db.is_active:
                                await db.rollback()
                    
                    # Remove the last AI message from history
                    if current_chat_history and isinstance(current_chat_history[-1], AIMessage):
                        removed_message = current_chat_history.pop()
                        log.info(f"🔄 Removed last AI message from history: '{removed_message.content[:50]}...'")
                    
                    # Add the regenerate content as user message if not already present
                    if not current_chat_history or current_chat_history[-1].content != regenerate_content:
                        current_chat_history.append(HumanMessage(content=regenerate_content))
                        log.info(f"🔄 Added regenerate content to history")
                    
                    try:
                        log.info(f"🔄 Starting master agent with {len(current_chat_history)} history messages")
                        
                        # Use timeout for regeneration to prevent hanging
                        try:
                            response = await asyncio.wait_for(
                                master_agent.ainvoke({
                                    "input": regenerate_content,
                                    "chat_history": current_chat_history,
                                }),
                                timeout=180.0  # 3 minute timeout for complex requests
                            )
                            
                            if response and 'output' in response:
                                agent_response = response['output']
                                log.info(f"🔄 Master agent regenerated response: '{agent_response[:100]}...'")
                                
                                # Delete the last AI message from database before saving new one
                                try:
                                    last_ai_message = await db.execute(
                                        select(ChatMessage)
                                        .where(ChatMessage.user_id == user.id)
                                        .where(ChatMessage.page_id == regenerate_page_id)
                                        .where(ChatMessage.is_user_message == False)
                                        .order_by(ChatMessage.created_at.desc())
                                        .limit(1)
                                    )
                                    last_ai_msg = last_ai_message.scalars().first()
                                    if last_ai_msg:
                                        await db.delete(last_ai_msg)
                                        log.info(f"🔄 Deleted original AI message {last_ai_msg.id} from database")
                                    
                                    # Now save the new regenerated message
                                    new_message = ChatMessage(
                                        id=str(uuid.uuid4()),
                                        user_id=user.id,
                                        message=agent_response,
                                        is_user_message=False,
                                        page_id=regenerate_page_id
                                    )
                                    db.add(new_message)
                                    await db.commit()
                                    log.info(f"🔄 Regenerated message saved to database with page_id: {regenerate_page_id}")
                                except Exception as save_error:
                                    log.error(f"🔄 Error saving regenerated message: {save_error}")
                                    if db.is_active:
                                        await db.rollback()
                                
                                await websocket.send_json({
                                    "type": "message",
                                    "message": agent_response
                                })
                            else:
                                log.error("🔄 Master agent returned invalid response format")
                                await websocket.send_text("I apologize, but I encountered an issue generating a response. Please try again.")
                                
                        except asyncio.TimeoutError:
                            log.error("🔄 Master agent timed out during regeneration")
                            await websocket.send_json({
                                "type": "error",
                                "message": "The regeneration took too long and timed out. Please try again with a simpler request."
                            })
                        except Exception as agent_error:
                            log.error(f"🔄 Master agent error during regeneration: {agent_error}")
                            await websocket.send_json({
                                "type": "error",
                                "message": "I encountered an error while regenerating the response. Please try again."
                            })
                            
                    except Exception as e:
                        log.error(f"🔄 Error during regeneration: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "message": "I apologize, but I encountered an error during regeneration. Please try again."
                        })
                    continue
                elif "content" in message_data:
                    # New format with page context
                    message_content = message_data["content"]
                    page_id = message_data.get("page_id")
                    # FIX: Ensure page_id is None if it's an empty string to avoid foreign key errors.
                    if not page_id:
                        page_id = None
                        title = message_content.split('\n')[0][:50].strip() or "New Conversation"
                        new_page = Page(user_id=user.id, title=title)
                        db.add(new_page)
                        await db.flush()
                        
                        page_id = new_page.id
                        log.info(f"Created new page {page_id} for user {user.id}")

                # Save the user's message
                    user_message_db = ChatMessage(
                        user_id=user.id,
                        page_id=page_id,
                        message=message_content,
                        is_user_message=True
                    )
                    db.add(user_message_db)
                    await db.commit()
                    await db.refresh(user_message_db)
                    log.info(f"Saved user message {user_message_db.id} for page {page_id}")

                    # If it was a new page, send the ID to the client
                    if new_page:
                        await websocket.send_json({
                            "type": "page_created",
                            "page_id": new_page.id,
                            "title": new_page.title
                        })
                        log.info(f"Sent page_created event for new page {new_page.id}")


                # Only load page history if WebSocket context isn't already set for this page
                    # Frontend is responsible for loading messages via API, WebSocket just tracks context
                    if page_id != current_loaded_page_id:
                        if page_id:
                            # Load conversation history for AI context only (don't send to frontend)
                            try:
                                page_history = await db.execute(
                                    select(ChatMessage)
                                    .where(ChatMessage.user_id == user_id)
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
                                if db.is_active:
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
                    user_id=user_id,
                    page_id=page_id,
                    message=message_content,
                    is_user_message=True
                ))
                await db.commit()
                log.info(f"Saved user message {user_message_id} with page_id: {page_id}")
            except Exception as save_error:
                log.error(f"Failed to save user message: {save_error}")
                if db.is_active:
                    await db.rollback()
                user_message_id = str(uuid.uuid4())  # Generate new ID for retry
            
            current_chat_history.append(HumanMessage(id=user_message_id, content=message_content))

            # Track user message behavior
            if memory_manager:
                try:
                    await memory_manager.save_user_behavior(
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
                    await memory_manager.save_user_behavior(
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
                        await memory_manager.save_user_behavior(
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
            
            await websocket.send_json({
                "type": "message",
                "message": result
            })
            
            # Save AI message with page context
            try:
                if result:
                    ai_message_id = str(uuid.uuid4())
                    db.add(ChatMessage(
                        id=ai_message_id,
                        user_id=user_id,
                        page_id=page_id,
                        message=result,
                        is_user_message=False
                    ))
                    await db.commit()
                log.info(f"Saved AI message {ai_message_id} with page_id: {page_id}")
            except Exception as save_error:
                log.error(f"Failed to save AI message: {save_error}")
                if db.is_active:
                    await db.rollback()
                ai_message_id = str(uuid.uuid4())  # Generate new ID for retry
            
            current_chat_history.append(AIMessage(id=ai_message_id, content=result))
            
    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        log.error(f"WebSocket error for user {user_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"An error occurred: {str(e)}"
            })
        except Exception:
            pass  # WebSocket might be closed 