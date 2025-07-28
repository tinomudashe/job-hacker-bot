import logging
from typing import Optional, Type
from app.linkedin_jobs_service import get_linkedin_jobs_service
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

log = logging.getLogger(__name__)

# The Pydantic schema will now correctly expect 'query'.
class LinkedInSearchInput(BaseModel):
    query: str = Field(description="Job search query (e.g., 'software engineer', 'python developer')")
    location: str = Field(default="Remote", description="Location to search in (e.g., 'Poland', 'Remote', 'Warsaw')")
    job_type: Optional[str] = Field(default="", description="Type of position ('full time', 'part time', 'contract', 'internship')")
    experience_level: Optional[str] = Field(default="", description="Level ('internship', 'entry level', 'associate', 'senior')")
    limit: Optional[int] = Field(default=10, description="Number of jobs to return (max 25)")

# The function will now correctly accept 'query'.
async def _search_jobs(
        query: str,
        location: str = "Remote",
        job_type: str = "",
        experience_level: str = "",
        limit: int = 10
    ) -> str:
    """The underlying implementation of the job search tool."""
    try:
        log.info(f"🔗 Starting job search for '{query}' in '{location}'")
        
        linkedin_service = get_linkedin_jobs_service()
        
        # The received 'query' is now correctly passed as the 'keyword' parameter to the service.
        jobs = await linkedin_service.search_jobs(
            keyword=query,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
            limit=min(limit, 25),
            date_since_posted="past week"
        )
        
        if not jobs:
            return f"🔍 No jobs found for '{query}' in {location}.\n\n💡 **Suggestions:**\n• Try different queries\n• Expand location"
        
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
        
        result_header = f"🎯 **Found {len(jobs)} jobs for '{query}' in {location}:**\n\n"
        result_body = "\n\n---\n\n".join(formatted_jobs)
        
        return result_header + result_body
        
    except Exception as e:
        log.error(f"Error in LinkedIn API search: {e}", exc_info=True)
        return "An error occurred during the job search. Please try again."

# The Tool object is constructed with the function that now correctly handles the 'query' argument.
search_jobs_linkedin_api = Tool(
    name="search_jobs_linkedin_api",
    description="⭐ JOB SEARCH API - Direct access to job listings! Uses professional job search API for reliable, fast job searches.",
    func=_search_jobs,
    args_schema=LinkedInSearchInput
)
