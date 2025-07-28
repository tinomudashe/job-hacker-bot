import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_db import User
from app.job_search import search_jobs_with_serper, JobSearchResult

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class JobSearchInput(BaseModel):
    query: str = Field(description="Job search terms, e.g., 'software engineer'.")
    location: Optional[str] = Field(default="United States", description="Location to search in, e.g., 'Warsaw, Poland'.")
    job_type: Optional[str] = Field(default=None, description="Type of employment, e.g., 'full-time'.")
    experience_level: Optional[str] = Field(default=None, description="Required experience level, e.g., 'entry-level'.")

# Step 2: Define the core logic as a plain async function.
async def _search_jobs_tool(
    query: str,
    location: Optional[str],
    job_type: Optional[str],
    experience_level: Optional[str],
    user: User, # Injected dependency
    db: AsyncSession # Injected dependency
) -> str:
    """The underlying implementation for searching for real-time job postings."""
    try:
        log.info(f"Searching jobs with query: '{query}', location: '{location}' for user {user.id}")
        
        # We will use the serper integration for a reliable, simple search.
        # The more complex browser-based tools can be called explicitly if needed.
        results: List[JobSearchResult] = await search_jobs_with_serper(
            query=query,
            location=location,
            user_id=str(user.id)
        )

        if not results:
            return f"🔍 No jobs found for '{query}' in {location}. Try a broader search or different keywords."

        response_parts = [f"Found {len(results)} jobs for '{query}' in {location}:\n"]
        for i, job in enumerate(results[:5], 1): # Show top 5
            parts = [f"**{i}. {job.title}** at **{job.company}**"]
            if job.location: parts.append(f"   📍 Location: {job.location}")
            if job.salary: parts.append(f"   💰 Salary: {job.salary}")
            if job.description: parts.append(f"   📋 Description: {job.description[:200]}...")
            if job.url: parts.append(f"   🔗 Apply: {job.url}")
            response_parts.append("\n".join(parts))

        return "\n\n---\n\n".join(response_parts)

    except Exception as e:
        log.error(f"Error in _search_jobs_tool for user {user.id}: {e}", exc_info=True)
        return "Sorry, I encountered an error while searching for jobs. Please try again."

# Step 3: Manually construct the Tool object with the explicit schema.
search_jobs_tool = Tool(
    name="search_jobs_tool",
    description="Searches for real-time job postings using a general web search provider.",
    func=lambda **kwargs: _search_jobs_tool(**kwargs),
    args_schema=JobSearchInput
)
