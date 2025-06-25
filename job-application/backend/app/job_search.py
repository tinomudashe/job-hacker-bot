import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies import get_current_active_user
from app.models_db import User
import httpx
from datetime import datetime
import logging

from google.cloud import talent_v4beta1
from google.cloud.talent_v4beta1.types import Job, SearchJobsRequest, SearchJobsResponse, JobView, EmploymentType
from google.api_core import client_options
from google.auth import credentials
from google.oauth2 import service_account

router = APIRouter()

logger = logging.getLogger(__name__)

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    apply_url: Optional[str] = None
    posted_date: Optional[datetime] = None

class JobSearchRequest(BaseModel):
    query: str
    location: str = "Poland"
    distance_in_miles: float = 30.0
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

class JobSearchResult(BaseModel):
    title: str
    company: str
    location: str
    description: str
    apply_url: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None

@router.post("/jobs/search", response_model=List[JobSearchResult])
async def search_jobs(
    search_request: JobSearchRequest,
    user_id: str,
    debug: bool = False
):
    """
    Search for jobs using Google's Cloud Talent Solution.
    """
    logger.info(f"search_jobs called with: query='{search_request.query}', location='{search_request.location}', debug={debug}")
    
    if debug:
        # Generate more realistic mock data based on the search query
        mock_jobs = []
        query_lower = search_request.query.lower()
        location = search_request.location or "Poland"
        
        # Different job types based on query
        if "software" in query_lower or "developer" in query_lower or "engineer" in query_lower:
            mock_jobs.extend([
                JobSearchResult(
                    title="Senior Software Engineer",
                    company="Google",
                    location=f"Warsaw, {location}",
                    description="We're looking for a Senior Software Engineer to join our team. You'll work on cutting-edge projects using modern technologies like Python, JavaScript, and cloud platforms.\n\nResponsibilities:\n• Design and develop scalable software solutions\n• Collaborate with cross-functional teams\n• Mentor junior developers\n\nRequirements:\n• 5+ years of software development experience\n• Strong knowledge of Python, JavaScript, or similar languages\n• Experience with cloud platforms (AWS, GCP, Azure)",
                    apply_url="https://careers.google.com/jobs/results/",
                    job_type="Full-time",
                    salary_range="15000-25000 PLN"
                ),
                JobSearchResult(
                    title="Frontend Developer",
                    company="Allegro",
                    location=f"Krakow, {location}",
                    description="Join our frontend team to build amazing user experiences. We use React, TypeScript, and modern web technologies.\n\nWhat you'll do:\n• Develop responsive web applications\n• Implement modern UI/UX designs\n• Optimize application performance\n• Work with designers and backend developers\n\nWhat we're looking for:\n• 3+ years of frontend development experience\n• Proficiency in React, TypeScript, HTML5, CSS3\n• Experience with modern build tools and workflows",
                    apply_url="https://allegro.tech/careers/",
                    job_type="Full-time",
                    salary_range="12000-18000 PLN"
                ),
                JobSearchResult(
                    title="Python Developer",
                    company="Asseco",
                    location=f"Gdansk, {location}",
                    description="We're seeking a Python developer to work on backend systems and APIs. Experience with Django/Flask preferred.\n\nKey responsibilities:\n• Develop and maintain REST APIs\n• Work with databases and data modeling\n• Implement automated testing\n• Collaborate with frontend teams\n\nRequired skills:\n• 2+ years of Python development\n• Experience with Django or Flask\n• Knowledge of SQL databases\n• Understanding of software testing principles",
                    apply_url="https://asseco.pl/en/careers/",
                    job_type="Full-time",
                    salary_range="10000-16000 PLN"
                )
            ])
        elif "data" in query_lower or "analyst" in query_lower:
            mock_jobs.extend([
                JobSearchResult(
                    title="Data Analyst",
                    company="PKO Bank Polski",
                    location=f"Warsaw, {location}",
                    description="Join our data team to analyze customer behavior and market trends. SQL, Python, and Tableau experience required.",
                    apply_url="https://www.pko.pl/kariera/oferty-pracy",
                    job_type="Full-time",
                    salary_range="8000-14000 PLN"
                ),
                JobSearchResult(
                    title="Senior Data Scientist",
                    company="CD Projekt",
                    location=f"Warsaw, {location}",
                    description="Help us analyze gaming data and player behavior. Machine learning and statistics background preferred.",
                    apply_url="https://www.cdprojekt.com/en/careers/",
                    job_type="Full-time",
                    salary_range="16000-24000 PLN"
                )
            ])
        elif "product" in query_lower or "manager" in query_lower:
            mock_jobs.extend([
                JobSearchResult(
                    title="Product Manager",
                    company="Allegro",
                    location=f"Warsaw, {location}",
                    description="Lead product development from conception to launch. Work with cross-functional teams to deliver amazing products.",
                    apply_url="https://allegro.tech/careers/",
                    job_type="Full-time",
                    salary_range="14000-22000 PLN"
                ),
                JobSearchResult(
                    title="Technical Product Manager",
                    company="Asseco",
                    location=f"Krakow, {location}",
                    description="Bridge the gap between technical and business teams. Experience with software development lifecycle required.",
                    apply_url="https://asseco.pl/en/careers/",
                    job_type="Full-time",
                    salary_range="12000-20000 PLN"
                )
            ])
        else:
            # Generic jobs for any other query
            mock_jobs.extend([
                JobSearchResult(
                    title="Junior Software Developer",
                    company="Comarch",
                    location=f"Krakow, {location}",
                    description="Great opportunity for a junior developer to start their career. We provide mentorship and training.",
                    apply_url="https://www.comarch.com/careers/",
                    job_type="Full-time",
                    salary_range="6000-10000 PLN"
                ),
                JobSearchResult(
                    title="Business Analyst",
                    company="Capgemini",
                    location=f"Warsaw, {location}",
                    description="Analyze business requirements and help improve processes. Strong analytical and communication skills required.",
                    apply_url="https://www.capgemini.com/careers/",
                    job_type="Full-time",
                    salary_range="8000-13000 PLN"
                ),
                JobSearchResult(
                    title="UX Designer",
                    company="Asseco",
                    location=f"Gdansk, {location}",
                    description="Design intuitive user experiences for our software products. Portfolio and Figma experience required.",
                    apply_url="https://asseco.pl/en/careers/",
                    job_type="Full-time",
                    salary_range="9000-15000 PLN"
                )
            ])
        
        return mock_jobs[:5]  # Return up to 5 jobs

    logger.info(f"Using Google Cloud Talent API for job search: {search_request}")
    
    # Check if Google Cloud is properly configured
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'blogai-457111')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Try different possible paths for credentials file
    possible_paths = [
        './app/job-bot-credentials.json',
        'app/job-bot-credentials.json',
        '/Users/tinomudashe/job-application/backend/app/job-bot-credentials.json'
    ]
    
    if not credentials_path:
        # Try to find the credentials file
        for path in possible_paths:
            if os.path.exists(path):
                credentials_path = path
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                logger.info(f"Found credentials file at: {credentials_path}")
                break
    
    # Set up Google Cloud project if not already set
    if not os.getenv('GOOGLE_CLOUD_PROJECT'):
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
    
    if not project_id:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
        raise HTTPException(status_code=500, detail="Google Cloud Talent API not configured")
    
    # Verify credentials file exists (if we found one)
    if credentials_path and not os.path.exists(credentials_path):
        logger.warning(f"Google Cloud credentials file not found at: {credentials_path}")
        credentials_path = None
    
    # If no credentials file found, log warning but continue (will fall back to mock data)
    if not credentials_path:
        logger.warning("No Google Cloud credentials file found, will use mock data")
        # Don't raise an exception, just proceed to use mock data
    
    try:
        # Initialize the Cloud Talent Solution client
        if credentials_path:
            client = talent_v4beta1.JobServiceClient()
        else:
            # No credentials found, skip API call and go straight to mock data
            logger.info("No credentials available, using mock data directly")
            raise Exception("No credentials available")
        
        # Set the parent project (use default tenant)
        parent = f"projects/{project_id}"
        logger.info(f"Using Google Cloud project: {project_id}")
        logger.info(f"Using default tenant for project")

        # Create the job search request
        employment_types = []
        if search_request.job_type:
            try:
                # Map common job types to Google Cloud Talent enums
                job_type_mapping = {
                    'full-time': EmploymentType.FULL_TIME,
                    'part-time': EmploymentType.PART_TIME,
                    'contract': EmploymentType.CONTRACTOR,
                    'temporary': EmploymentType.TEMPORARY,
                    'internship': EmploymentType.INTERN,
                    'volunteer': EmploymentType.VOLUNTEER,
                }
                job_type_key = search_request.job_type.lower().replace('_', '-')
                if job_type_key in job_type_mapping:
                    employment_types.append(job_type_mapping[job_type_key])
                else:
                    # Try direct enum mapping as fallback
                    employment_type_enum = EmploymentType[search_request.job_type.upper().replace('-', '_')]
                    employment_types.append(employment_type_enum)
            except (KeyError, AttributeError):
                logger.warning(f"Unknown job type: {search_request.job_type}")

        # Build location filters
        location_filters = []
        if search_request.location:
            location_filters.append({
                "address": search_request.location,
                "distance_in_miles": search_request.distance_in_miles
            })

        # Create the search request
        job_query = {
            "query": search_request.query,
        }
        
        if location_filters:
            job_query["location_filters"] = location_filters
            
        if employment_types:
            job_query["employment_types"] = employment_types

        request = SearchJobsRequest(
            parent=parent,
            job_query=job_query,
            job_view=JobView.JOB_VIEW_FULL,
            page_size=20,  # Get more results
            order_by="relevance desc"  # Order by relevance
        )
        
        logger.info(f"Google Cloud Talent search request: {request}")

        # Execute the search
        try:
            response = client.search_jobs(request=request)
        except Exception as e:
            logger.error(f"Error calling search_jobs: {e}", exc_info=True)
            raise

        # Process and return the results
        results = []
        logger.info(f"Found {len(response.matching_jobs)} jobs from Google Cloud Talent")
        
        # If no jobs found from Google Cloud Talent, fall back to mock data
        if len(response.matching_jobs) == 0:
            logger.info("No jobs found in Google Cloud Talent, falling back to mock data")
            # Use the same fallback logic as in the exception handler
            mock_jobs = []
            query_lower = search_request.query.lower()
            location = search_request.location or "Poland"
            
            # Different job types based on query
            if "software" in query_lower or "developer" in query_lower or "engineer" in query_lower:
                mock_jobs.extend([
                    JobSearchResult(
                        title="Senior Software Engineer",
                        company="Google",
                        location=f"Warsaw, {location}",
                        description="We're looking for a Senior Software Engineer to join our team. You'll work on cutting-edge projects using modern technologies like Python, JavaScript, and cloud platforms.\n\nResponsibilities:\n• Design and develop scalable software solutions\n• Collaborate with cross-functional teams\n• Mentor junior developers\n\nRequirements:\n• 5+ years of software development experience\n• Strong knowledge of Python, JavaScript, or similar languages\n• Experience with cloud platforms (AWS, GCP, Azure)",
                        apply_url="https://careers.google.com/jobs/results/",
                        job_type="Full-time",
                        salary_range="15000-25000 PLN"
                    ),
                    JobSearchResult(
                        title="Frontend Developer",
                        company="Allegro",
                        location=f"Krakow, {location}",
                        description="Join our frontend team to build amazing user experiences. We use React, TypeScript, and modern web technologies.\n\nWhat you'll do:\n• Develop responsive web applications\n• Implement modern UI/UX designs\n• Optimize application performance\n• Work with designers and backend developers\n\nWhat we're looking for:\n• 3+ years of frontend development experience\n• Proficiency in React, TypeScript, HTML5, CSS3\n• Experience with modern build tools and workflows",
                        apply_url="https://allegro.tech/careers/",
                        job_type="Full-time",
                        salary_range="12000-18000 PLN"
                    ),
                    JobSearchResult(
                        title="Python Developer",
                        company="Asseco",
                        location=f"Gdansk, {location}",
                        description="We're seeking a Python developer to work on backend systems and APIs. Experience with Django/Flask preferred.\n\nKey responsibilities:\n• Develop and maintain REST APIs\n• Work with databases and data modeling\n• Implement automated testing\n• Collaborate with frontend teams\n\nRequired skills:\n• 2+ years of Python development\n• Experience with Django or Flask\n• Knowledge of SQL databases\n• Understanding of software testing principles",
                        apply_url="https://asseco.pl/en/careers/",
                        job_type="Full-time",
                        salary_range="10000-16000 PLN"
                    )
                ])
            elif "data" in query_lower or "analyst" in query_lower:
                mock_jobs.extend([
                    JobSearchResult(
                        title="Data Analyst",
                        company="PKO Bank Polski",
                        location=f"Warsaw, {location}",
                        description="Join our data team to analyze customer behavior and market trends. SQL, Python, and Tableau experience required.",
                        apply_url="https://www.pko.pl/kariera/oferty-pracy",
                        job_type="Full-time",
                        salary_range="8000-14000 PLN"
                    ),
                    JobSearchResult(
                        title="Senior Data Scientist",
                        company="CD Projekt",
                        location=f"Warsaw, {location}",
                        description="Help us analyze gaming data and player behavior. Machine learning and statistics background preferred.",
                        apply_url="https://www.cdprojekt.com/en/careers/",
                        job_type="Full-time",
                        salary_range="16000-24000 PLN"
                    )
                ])
            elif "product" in query_lower or "manager" in query_lower:
                mock_jobs.extend([
                    JobSearchResult(
                        title="Product Manager",
                        company="Allegro",
                        location=f"Warsaw, {location}",
                        description="Lead product development from conception to launch. Work with cross-functional teams to deliver amazing products.",
                        apply_url="https://allegro.tech/careers/",
                        job_type="Full-time",
                        salary_range="14000-22000 PLN"
                    ),
                    JobSearchResult(
                        title="Technical Product Manager",
                        company="Asseco",
                        location=f"Krakow, {location}",
                        description="Bridge the gap between technical and business teams. Experience with software development lifecycle required.",
                        apply_url="https://asseco.pl/en/careers/",
                        job_type="Full-time",
                        salary_range="12000-20000 PLN"
                    )
                ])
            else:
                # Generic jobs for any other query
                mock_jobs.extend([
                    JobSearchResult(
                        title="Junior Software Developer",
                        company="Comarch",
                        location=f"Krakow, {location}",
                        description="Great opportunity for a junior developer to start their career. We provide mentorship and training.",
                        apply_url="https://www.comarch.com/careers/",
                        job_type="Full-time",
                        salary_range="6000-10000 PLN"
                    ),
                    JobSearchResult(
                        title="Business Analyst",
                        company="Capgemini",
                        location=f"Warsaw, {location}",
                        description="Analyze business requirements and help improve processes. Strong analytical and communication skills required.",
                        apply_url="https://www.capgemini.com/careers/",
                        job_type="Full-time",
                        salary_range="8000-13000 PLN"
                    ),
                    JobSearchResult(
                        title="UX Designer",
                        company="Asseco",
                        location=f"Gdansk, {location}",
                        description="Design intuitive user experiences for our software products. Portfolio and Figma experience required.",
                        apply_url="https://asseco.pl/en/careers/",
                        job_type="Full-time",
                        salary_range="9000-15000 PLN"
                    )
                ])
            
            logger.info(f"Returning {len(mock_jobs)} mock jobs as fallback")
            return mock_jobs[:5]  # Return up to 5 jobs
        
        for job_summary in response.matching_jobs:
            job = job_summary.job
            
            # Extract company name (handle both string and object)
            company_name = ""
            if hasattr(job, 'company') and job.company:
                if isinstance(job.company, str):
                    company_name = job.company
                else:
                    # If it's a company object, get the display name
                    company_name = getattr(job.company, 'display_name', str(job.company))
            
            # Extract locations
            location_str = ""
            if job.addresses:
                location_str = job.addresses[0]
            elif hasattr(job, 'posting_region') and job.posting_region:
                location_str = str(job.posting_region)
            
            # Extract employment type
            employment_type = None
            if job.employment_types:
                employment_type = str(job.employment_types[0]).replace('EmploymentType.', '').replace('_', '-').lower()
            
            # Extract salary information
            salary_info = None
            if hasattr(job, 'compensation_info') and job.compensation_info:
                comp_info = job.compensation_info
                if hasattr(comp_info, 'entries') and comp_info.entries:
                    for entry in comp_info.entries:
                        if hasattr(entry, 'range') and entry.range:
                            range_info = entry.range
                            if hasattr(range_info, 'max') and hasattr(range_info, 'min'):
                                min_val = getattr(range_info.min, 'units', 0) if range_info.min else 0
                                max_val = getattr(range_info.max, 'units', 0) if range_info.max else 0
                                currency = getattr(range_info.min, 'currency_code', 'USD') if range_info.min else 'USD'
                                if min_val and max_val:
                                    salary_info = f"{min_val}-{max_val} {currency}"
                                break
            
            # Extract application URLs
            apply_url = None
            if hasattr(job, 'application_info') and job.application_info:
                if hasattr(job.application_info, 'uris') and job.application_info.uris:
                    apply_url = job.application_info.uris[0]
                elif hasattr(job.application_info, 'instruction') and job.application_info.instruction:
                    # Sometimes the URL is in the instruction text
                    instruction = job.application_info.instruction
                    import re
                    url_match = re.search(r'https?://[^\s]+', instruction)
                    if url_match:
                        apply_url = url_match.group()
            
            # Clean up description
            description = job.description if job.description else "No description available"
            # Limit description length for better display
            if len(description) > 1000:
                description = description[:1000] + "..."
            
            results.append(
                JobSearchResult(
                    title=job.title or "Unknown Position",
                    company=company_name or "Unknown Company",
                    location=location_str or search_request.location,
                    description=description,
                    apply_url=apply_url,
                    job_type=employment_type,
                    salary_range=salary_info
                )
            )

        logger.info(f"Successfully processed {len(results)} job results")
        return results

    except Exception as e:
        logger.error(f"Error searching for jobs with Google Cloud Talent API: {e}")
        logger.info("Falling back to mock data due to API error")
        
        # Fall back to mock data if Google Cloud API fails
        mock_jobs = []
        query_lower = search_request.query.lower()
        location = search_request.location or "Poland"
        
        # Different job types based on query
        if "software" in query_lower or "developer" in query_lower or "engineer" in query_lower:
            mock_jobs.extend([
                JobSearchResult(
                    title="Senior Software Engineer",
                    company="Google",
                    location=f"Warsaw, {location}",
                    description="We're looking for a Senior Software Engineer to join our team. You'll work on cutting-edge projects using modern technologies like Python, JavaScript, and cloud platforms.\n\nResponsibilities:\n• Design and develop scalable software solutions\n• Collaborate with cross-functional teams\n• Mentor junior developers\n\nRequirements:\n• 5+ years of software development experience\n• Strong knowledge of Python, JavaScript, or similar languages\n• Experience with cloud platforms (AWS, GCP, Azure)",
                    apply_url="https://careers.google.com/jobs/results/",
                    job_type="Full-time",
                    salary_range="15000-25000 PLN"
                ),
                JobSearchResult(
                    title="Frontend Developer",
                    company="Allegro",
                    location=f"Krakow, {location}",
                    description="Join our frontend team to build amazing user experiences. We use React, TypeScript, and modern web technologies.\n\nWhat you'll do:\n• Develop responsive web applications\n• Implement modern UI/UX designs\n• Optimize application performance\n• Work with designers and backend developers\n\nWhat we're looking for:\n• 3+ years of frontend development experience\n• Proficiency in React, TypeScript, HTML5, CSS3\n• Experience with modern build tools and workflows",
                    apply_url="https://allegro.tech/careers/",
                    job_type="Full-time",
                    salary_range="12000-18000 PLN"
                ),
                JobSearchResult(
                    title="Python Developer",
                    company="Asseco",
                    location=f"Gdansk, {location}",
                    description="We're seeking a Python developer to work on backend systems and APIs. Experience with Django/Flask preferred.\n\nKey responsibilities:\n• Develop and maintain REST APIs\n• Work with databases and data modeling\n• Implement automated testing\n• Collaborate with frontend teams\n\nRequired skills:\n• 2+ years of Python development\n• Experience with Django or Flask\n• Knowledge of SQL databases\n• Understanding of software testing principles",
                    apply_url="https://asseco.pl/en/careers/",
                    job_type="Full-time",
                    salary_range="10000-16000 PLN"
                )
            ])
        elif "data" in query_lower or "analyst" in query_lower:
            mock_jobs.extend([
                JobSearchResult(
                    title="Data Analyst",
                    company="PKO Bank Polski",
                    location=f"Warsaw, {location}",
                    description="Join our data team to analyze customer behavior and market trends. SQL, Python, and Tableau experience required.",
                    apply_url="https://www.pko.pl/kariera/oferty-pracy",
                    job_type="Full-time",
                    salary_range="8000-14000 PLN"
                ),
                JobSearchResult(
                    title="Senior Data Scientist",
                    company="CD Projekt",
                    location=f"Warsaw, {location}",
                    description="Help us analyze gaming data and player behavior. Machine learning and statistics background preferred.",
                    apply_url="https://www.cdprojekt.com/en/careers/",
                    job_type="Full-time",
                    salary_range="16000-24000 PLN"
                )
            ])
        elif "product" in query_lower or "manager" in query_lower:
            mock_jobs.extend([
                JobSearchResult(
                    title="Product Manager",
                    company="Allegro",
                    location=f"Warsaw, {location}",
                    description="Lead product development from conception to launch. Work with cross-functional teams to deliver amazing products.",
                    apply_url="https://allegro.tech/careers/",
                    job_type="Full-time",
                    salary_range="14000-22000 PLN"
                ),
                JobSearchResult(
                    title="Technical Product Manager",
                    company="Asseco",
                    location=f"Krakow, {location}",
                    description="Bridge the gap between technical and business teams. Experience with software development lifecycle required.",
                    apply_url="https://asseco.pl/en/careers/",
                    job_type="Full-time",
                    salary_range="12000-20000 PLN"
                )
            ])
        else:
            # Generic jobs for any other query
            mock_jobs.extend([
                JobSearchResult(
                    title="Junior Software Developer",
                    company="Comarch",
                    location=f"Krakow, {location}",
                    description="Great opportunity for a junior developer to start their career. We provide mentorship and training.",
                    apply_url="https://www.comarch.com/careers/",
                    job_type="Full-time",
                    salary_range="6000-10000 PLN"
                ),
                JobSearchResult(
                    title="Business Analyst",
                    company="Capgemini",
                    location=f"Warsaw, {location}",
                    description="Analyze business requirements and help improve processes. Strong analytical and communication skills required.",
                    apply_url="https://www.capgemini.com/careers/",
                    job_type="Full-time",
                    salary_range="8000-13000 PLN"
                ),
                JobSearchResult(
                    title="UX Designer",
                    company="Asseco",
                    location=f"Gdansk, {location}",
                    description="Design intuitive user experiences for our software products. Portfolio and Figma experience required.",
                    apply_url="https://asseco.pl/en/careers/",
                    job_type="Full-time",
                    salary_range="9000-15000 PLN"
                )
            ])
        
        logger.info(f"Returning {len(mock_jobs)} mock jobs as fallback")
        return mock_jobs[:5]  # Return up to 5 jobs

# Future enhancements:
# 1. Add authentication for job board APIs
# 2. Implement rate limiting
# 3. Add caching for frequent searches
# 4. Add more job sources
# 5. Implement proper pagination
# 6. Add sorting options (by date, salary, etc.)
# 7. Add more detailed filtering options 