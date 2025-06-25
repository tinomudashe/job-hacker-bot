import asyncio
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import logging
import re
import json

from browser_use import Agent, Controller, Browser
from browser_use.agent.views import ActionResult
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, HttpUrl, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class JobURL:
    """Represents a job URL found on a job board."""
    url: str
    title: str
    company: str
    location: str
    snippet: str
    posted_date: Optional[str] = None

@dataclass 
class JobExtraction:
    """Complete job information extracted from a specific job URL."""
    url: str
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None
    apply_url: Optional[str] = None
    raw_text: str = ""

class JobURLsResult(BaseModel):
    """Pydantic model for job URLs extraction result."""
    jobs: List[Dict[str, str]]
    total_found: int
    search_query: str
    location: str

class JobDetailsResult(BaseModel):
    """Pydantic model for detailed job extraction result."""
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None
    apply_url: Optional[str] = None

class BrowserJobExtractor:
    """Advanced job extraction using browser automation."""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash', temperature=0.1)
        
    async def search_job_urls(
        self, 
        search_query: str, 
        location: str = "Remote", 
        job_board: str = "linkedin",
        max_jobs: int = 10
    ) -> List[JobURL]:
        """Search for job URLs on various job boards using browser automation."""
        
        controller = Controller(output_model=JobURLsResult)
        
        @controller.action('Extract job URLs from the current page')
        def extract_job_urls() -> ActionResult:
            """Extract job URLs, titles, companies, and locations from the current page."""
            # This will be handled by the LLM to identify and extract job listings
            return ActionResult(
                extracted_content="Job URLs extracted successfully",
                include_in_memory=True
            )
        
        browser = Browser(
            wss_url="ws://127.0.0.1:3000/",
            incognito=True,
        )
        
        # Create search URL based on job board
        search_url = self._build_search_url(job_board, search_query, location)
        
        task_prompt = f"""
        You are an expert at extracting job listings from job boards. Your task is to:
        
        1. Navigate to {search_url}
        2. Wait for the page to fully load and handle any pop-ups, cookie banners, or sign-in prompts
        3. Identify all job listings on the page (usually displayed as cards or list items)
        4. For each job listing, extract:
           - Job title
           - Company name
           - Location
           - Job URL (clickable link to the full job posting)
           - Brief snippet/description if available
           - Posted date if visible
        
        5. Collect up to {max_jobs} job listings
        6. If there are pagination controls (Next, Page 2, etc.), navigate to additional pages if needed
        7. Return the extracted job information in the specified format
        
        Search Parameters:
        - Query: "{search_query}"
        - Location: "{location}"
        - Job Board: {job_board}
        - Max Jobs: {max_jobs}
        
        Focus on extracting accurate URLs that lead directly to individual job postings.
        Ensure all URLs are complete and valid (include domain if relative URLs are found).
        """
        
        try:
            agent = Agent(
                task=task_prompt,
                llm=self.llm,
                controller=controller,
                browser=browser,
                enable_memory=True,
                planner_llm=self.llm,
                use_vision_for_planner=True,
            )
            
            logger.info(f"Starting job URL extraction for '{search_query}' on {job_board}")
            result = await agent.run()
            
            # Parse the result and convert to JobURL objects
            if hasattr(result, 'jobs') and result.jobs:
                job_urls = []
                for job_data in result.jobs[:max_jobs]:
                    job_url = JobURL(
                        url=job_data.get('url', ''),
                        title=job_data.get('title', ''),
                        company=job_data.get('company', ''),
                        location=job_data.get('location', ''),
                        snippet=job_data.get('snippet', ''),
                        posted_date=job_data.get('posted_date')
                    )
                    job_urls.append(job_url)
                return job_urls
            else:
                logger.warning("No jobs found in browser automation result")
                return []
                
        except Exception as e:
            logger.error(f"Error in job URL extraction: {e}")
            return []
    
    async def extract_job_details(self, job_url: str) -> Optional[JobExtraction]:
        """Extract complete job details from a specific job URL using browser automation."""
        
        controller = Controller(output_model=JobDetailsResult)
        
        @controller.action('Extract complete job information from current page')
        def extract_job_info() -> ActionResult:
            """Extract all job details from the current job posting page."""
            return ActionResult(
                extracted_content="Job details extracted successfully",
                include_in_memory=True
            )
        
        browser = Browser(
            wss_url="ws://127.0.0.1:3000/",
            incognito=True,
        )
        
        task_prompt = f"""
        You are an expert at extracting detailed job information from job posting pages.
        
        Your task is to:
        
        1. Navigate to {job_url}
        2. Wait for the page to fully load and handle any pop-ups or cookie banners
        3. Extract comprehensive job information:
           - Job title
           - Company name
           - Job location (city, state, country, or "Remote")
           - Complete job description (responsibilities, duties, what you'll do)
           - Requirements and qualifications (skills, experience, education needed)
           - Salary/compensation information (if available)
           - Job type (full-time, part-time, contract, internship, etc.)
           - Posted date (if available)
           - Apply URL or application instructions (if different from current URL)
        
        4. Ensure you capture the COMPLETE job description and requirements
        5. Clean up any formatting issues and provide well-structured text
        6. If multiple sections exist (Description, Requirements, Benefits, etc.), capture all relevant content
        
        Focus on extracting comprehensive and accurate information that would be needed for generating a cover letter.
        """
        
        try:
            agent = Agent(
                task=task_prompt,
                llm=self.llm,
                controller=controller,
                browser=browser,
                enable_memory=True,
                planner_llm=self.llm,
                use_vision_for_planner=True,
            )
            
            logger.info(f"Extracting job details from: {job_url}")
            result = await agent.run()
            
            if hasattr(result, 'title') and result.title:
                job_extraction = JobExtraction(
                    url=job_url,
                    title=result.title,
                    company=result.company,
                    location=result.location,
                    description=result.description,
                    requirements=result.requirements,
                    salary=result.salary,
                    job_type=result.job_type,
                    posted_date=result.posted_date,
                    apply_url=result.apply_url or job_url
                )
                return job_extraction
            else:
                logger.warning(f"Failed to extract job details from {job_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting job details from {job_url}: {e}")
            return None
    
    async def search_and_extract_jobs(
        self,
        search_query: str,
        location: str = "Remote",
        job_board: str = "linkedin",
        max_jobs: int = 5,
        extract_details: bool = True
    ) -> List[JobExtraction]:
        """Complete job search and extraction pipeline."""
        
        logger.info(f"Starting complete job search for '{search_query}' on {job_board}")
        
        # Step 1: Get job URLs
        job_urls = await self.search_job_urls(search_query, location, job_board, max_jobs)
        
        if not job_urls:
            logger.warning("No job URLs found")
            return []
        
        logger.info(f"Found {len(job_urls)} job URLs")
        
        # Step 2: Extract details for each job (if requested)
        if not extract_details:
            # Convert JobURL to basic JobExtraction
            return [
                JobExtraction(
                    url=job.url,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    description=job.snippet,
                    requirements="",
                    posted_date=job.posted_date
                )
                for job in job_urls
            ]
        
        job_extractions = []
        for job_url in job_urls:
            logger.info(f"Extracting details for: {job_url.title} at {job_url.company}")
            job_details = await self.extract_job_details(job_url.url)
            if job_details:
                job_extractions.append(job_details)
            
            # Add small delay to be respectful to job boards
            await asyncio.sleep(2)
        
        logger.info(f"Successfully extracted details for {len(job_extractions)} jobs")
        return job_extractions
    
    def _build_search_url(self, job_board: str, search_query: str, location: str) -> str:
        """Build search URL for different job boards."""
        
        # URL encode the parameters
        import urllib.parse
        query_encoded = urllib.parse.quote_plus(search_query)
        location_encoded = urllib.parse.quote_plus(location)
        
        job_board = job_board.lower()
        
        if job_board == "linkedin":
            return f"https://www.linkedin.com/jobs/search/?keywords={query_encoded}&location={location_encoded}"
        elif job_board == "indeed":
            return f"https://www.indeed.com/jobs?q={query_encoded}&l={location_encoded}"
        elif job_board == "glassdoor":
            return f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query_encoded}&locT=C&locId={location_encoded}"
        elif job_board == "monster":
            return f"https://www.monster.com/jobs/search/?q={query_encoded}&where={location_encoded}"
        elif job_board == "ziprecruiter":
            return f"https://www.ziprecruiter.com/jobs/search?search={query_encoded}&location={location_encoded}"
        else:
            # Default to LinkedIn
            return f"https://www.linkedin.com/jobs/search/?keywords={query_encoded}&location={location_encoded}"

# Convenience functions for direct usage
async def search_jobs_with_browser(
    search_query: str,
    location: str = "Remote",
    job_board: str = "linkedin",
    max_jobs: int = 5
) -> List[JobExtraction]:
    """Search and extract jobs using browser automation."""
    extractor = BrowserJobExtractor()
    return await extractor.search_and_extract_jobs(
        search_query=search_query,
        location=location,
        job_board=job_board,
        max_jobs=max_jobs,
        extract_details=True
    )

async def extract_job_from_url(job_url: str) -> Optional[JobExtraction]:
    """Extract job details from a specific URL using browser automation."""
    extractor = BrowserJobExtractor()
    return await extractor.extract_job_details(job_url) 