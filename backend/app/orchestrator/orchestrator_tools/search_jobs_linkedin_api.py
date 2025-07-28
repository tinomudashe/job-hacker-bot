from langchain_core.tools import tool
import logging
from app.linkedin_jobs_service import get_linkedin_jobs_service
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)

# This schema now just signals that the input is a dictionary.
class LinkedInSearchInput(BaseModel):
    tool_input: Dict[str, Any] = Field(description="A dictionary containing the job search parameters.")

@tool
async def search_jobs_linkedin_api(tool_input: dict) -> str:
    """⭐ JOB SEARCH API - Direct access to job listings!
    
    Uses professional job search API for reliable, fast job searches.
    Accepts a single dictionary with the following keys:
    - keyword (str): Job search terms (e.g., 'software engineer'). Required.
    - location (str): Location to search in. Defaults to 'Remote'.
    - job_type (str): 'full time', 'part time', etc. Optional.
    - experience_level (str): 'internship', 'entry level', etc. Optional.
    - limit (int): Number of jobs to return. Defaults to 10.
    """
    try:
        # Manually and safely extract arguments from the input dictionary.
        # This makes the tool a true single-input tool, resolving the error.
        keyword = tool_input.get("keyword")
        if not keyword:
            return "Error: The 'keyword' argument is required for a job search."
            
        location = tool_input.get("location", "Remote")
        job_type = tool_input.get("job_type", "")
        experience_level = tool_input.get("experience_level", "")
        limit = tool_input.get("limit", 10)

        log.info(f"🔗 Starting job search for '{keyword}' in '{location}'")
        
        linkedin_service = get_linkedin_jobs_service()
        
        jobs = await linkedin_service.search_jobs(
            keyword=keyword,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
            limit=min(limit, 25),
            date_since_posted="past week"
        )
        
        if not jobs:
            return f"🔍 No jobs found for '{keyword}' in {location}.\n\n💡 **Suggestions:**\n• Try different keywords\n• Expand location"
        
        formatted_jobs = []
        for i, job in enumerate(jobs, 1):
            job_text = f"**{i}. {job.position}** at **{job.company}**"
            if job.location: job_text += f"\n   📍 **Location:** {job.location}"
            if job.ago_time: job_text += f"\n   📅 **Posted:** {job.ago_time}"
            if job.salary and job.salary != "Not specified": job_text += f"\n   💰 **Salary:** {job.salary}"
            if job_type: job_text += f"\n   📋 **Type:** {job_type}"
            if experience_level: job_text += f"\n   👨‍💼 **Level:** {experience_level}"
            if job.job_url: job_text += f"\n   🔗 **Apply:** {job.job_url}"
            formatted_jobs.append(job_text)
        
        result_header = f"🎯 **Found {len(jobs)} jobs for '{keyword}' in {location}:**\n\n"
        result_body = "\n\n---\n\n".join(formatted_jobs)
        
        return result_header + result_body
        
    except Exception as e:
        log.error(f"Error in LinkedIn API search: {e}", exc_info=True)
        return "An error occurred during the job search. Please try again."
