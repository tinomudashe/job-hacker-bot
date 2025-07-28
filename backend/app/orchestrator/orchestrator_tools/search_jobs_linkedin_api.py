from langchain_core.tools import tool
import logging
from app.linkedin_jobs_service import get_linkedin_jobs_service
from pydantic import BaseModel, Field
from typing import Optional

log = logging.getLogger(__name__)

# This Pydantic model defines the exact input schema for the tool.
class LinkedInSearchInput(BaseModel):
    keyword: str = Field(description="Job search terms (e.g., 'software engineer', 'python developer')")
    location: str = Field(default="Remote", description="Location to search in (e.g., 'Poland', 'Remote', 'Warsaw')")
    job_type: Optional[str] = Field(default="", description="Type of position ('full time', 'part time', 'contract', 'internship')")
    experience_level: Optional[str] = Field(default="", description="Level ('internship', 'entry level', 'associate', 'senior')")
    limit: Optional[int] = Field(default=10, description="Number of jobs to return (max 25)")

# The @tool decorator now uses the Pydantic model as its `args_schema`.
# The function now accepts a single argument: an instance of the Pydantic model.
# This is the correct way to define a multi-argument tool.
@tool(args_schema=LinkedInSearchInput)
async def search_jobs_linkedin_api(tool_input: LinkedInSearchInput) -> str:
    """⭐ JOB SEARCH API - Direct access to job listings!
    
    Uses professional job search API for reliable, fast job searches.
    NO BROWSER AUTOMATION - Direct API access for instant results.
    """
    try:
        # We now access the arguments from the tool_input object.
        keyword = tool_input.keyword
        location = tool_input.location
        job_type = tool_input.job_type
        experience_level = tool_input.experience_level
        limit = tool_input.limit

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
