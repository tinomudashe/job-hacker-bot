from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.job_search import JobSearchRequest, JobSearchResult, search_jobs
from app.dependencies import get_current_active_user
from app.models_db import User

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/search", response_model=List[JobSearchResult])
async def search_job_listings(
    request: JobSearchRequest,
    current_user: User = Depends(get_current_active_user)
) -> List[JobSearchResult]:
    """
    Search for jobs in Poland with various filters.
    
    Parameters:
    - query: Search terms (e.g., "software engineer", "python developer")
    - location: City in Poland (defaults to "Poland" for country-wide search)
    - distance_in_miles: Search radius (default: 30 miles)
    - job_type: Type of job (e.g., "Full-time", "Part-time", "Contract")
    - experience_level: Required experience level
    
    Returns:
    - List of job listings matching the search criteria
    """
    try:
        jobs = await search_jobs(request, current_user.id)
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for jobs: {str(e)}"
        ) 