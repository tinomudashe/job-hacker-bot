import logging
import os
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_db import User
# FIX: Import the correct function and request model from app.job_search
from app.job_search import search_jobs, JobSearchRequest, JobSearchResult

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class JobSearchInput(BaseModel):
    query: str = Field(description="Job search terms, e.g., 'software engineer'.")
    location: Optional[str] = Field(default="Poland", description="Location to search in, e.g., 'Warsaw, Poland'.")
    distance_in_miles: Optional[float] = Field(default=30.0, description="Search radius in miles.")
    job_type: Optional[str] = Field(default=None, description="Type of employment, e.g., 'full-time'.")
    experience_level: Optional[str] = Field(default=None, description="Required experience level, e.g., 'entry-level'.")

# Step 2: Define the core logic as a plain async function.
async def _search_jobs_tool(
    db: AsyncSession,
    user: User,
    query: str,
    location: Optional[str],
    distance_in_miles: Optional[float],
    job_type: Optional[str],
    experience_level: Optional[str]
) -> str:
    """The underlying implementation for searching for real-time job postings."""
    try:
        log.info(f"Searching jobs with query: '{query}', location: '{location}' for user {user.id}")
        
        search_request = JobSearchRequest(
            query=query,
            location=location,
            distance_in_miles=distance_in_miles,
            job_type=job_type,
            experience_level=experience_level
        )

        # Use debug mode if GOOGLE_CLOUD_PROJECT is not set, otherwise use the real API.
        use_real_api = bool(os.getenv('GOOGLE_CLOUD_PROJECT'))
        results: List[JobSearchResult] = await search_jobs(
            search_request=search_request,
            user_id=str(user.id),
            debug=not use_real_api
        )

        if not results:
            return f"🔍 No jobs found for '{query}' in {location}. Try a broader search or different keywords."

        response_parts = [f"Found {len(results)} jobs for '{query}' in {location}:\n"]
        for i, job in enumerate(results[:5], 1): # Show top 5
            parts = [f"**{i}. {job.title}** at **{job.company}**"]
            if job.location: parts.append(f"   📍 Location: {job.location}")
            if job.salary_range: parts.append(f"   💰 Salary: {job.salary_range}")
            if job.description: parts.append(f"   📋 Description: {job.description[:200]}...")
            if job.apply_url: parts.append(f"   🔗 Apply: {job.apply_url}")
            response_parts.append("\n".join(parts))

        return "\n\n---\n\n".join(response_parts)

    except Exception as e:
        log.error(f"Error in _search_jobs_tool for user {user.id}: {e}", exc_info=True)
        return "Sorry, I encountered an error while searching for jobs. Please try again."

# Step 3: Manually construct the Tool object with the explicit schema.
search_jobs_tool = Tool(
    name="search_jobs_tool",
    description="Searches for job postings using the Google Cloud Talent Solution API with a mock data fallback.",
    func=lambda **kwargs: _search_jobs_tool(**kwargs),
    args_schema=JobSearchInput
)
