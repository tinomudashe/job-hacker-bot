from typing import Optional
from langchain_core.tools import tool
import logging
import os

log = logging.getLogger(__name__)

from app.models.job_search import JobSearchRequest
from app.models.job_search import search_jobs
from app.browser_use_cloud import get_browser_use_service



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
            
            # Try Browser Use Cloud first as fallback for real data
            try:
                from app.browser_use_cloud import get_browser_use_service
                
                log.info("🔄 Basic search: Trying Browser Use Cloud as primary source...")
                browser_service = get_browser_use_service()
                
                cloud_jobs = await browser_service.search_jobs_on_platform(
                    query=search_query,
                    location=location or "Remote",
                    platform="indeed",
                    max_jobs=5
                )
                
                if cloud_jobs:
                    log.info(f"✅ Basic search: Found {len(cloud_jobs)} real jobs via Browser Use Cloud")
                    results = [
                        type('JobResult', (), {
                            'title': job.title,
                            'company': job.company,
                            'location': job.location,
                            'description': job.description,
                            'requirements': job.requirements,
                            'apply_url': job.url,
                            'job_type': job.job_type,
                            'salary_range': job.salary,
                            'dict': lambda: {
                                'title': job.title,
                                'company': job.company,
                                'location': job.location,
                                'description': job.description,
                                'requirements': job.requirements,
                                'apply_url': job.url,
                                'employment_type': job.job_type,
                                'salary_range': job.salary
                            }
                        })() for job in cloud_jobs
                    ]
                else:
                    log.warning("Browser Use Cloud returned no results, trying Google Cloud API...")
                    # Use real Google Cloud Talent API if project is configured, otherwise use debug mode
                    use_real_api = bool(os.getenv('GOOGLE_CLOUD_PROJECT'))
                    results = await search_jobs(search_request, user_id, debug=not use_real_api)
                    
            except Exception as e:
                log.warning(f"Browser Use Cloud failed in basic search: {e}, trying Google Cloud API...")
            # Use real Google Cloud Talent API if project is configured, otherwise use debug mode
            use_real_api = bool(os.getenv('GOOGLE_CLOUD_PROJECT'))
            results = await search_jobs(search_request, user_id, debug=not use_real_api)
            
            if not results:
                return f"🔍 No jobs found for '{search_query}' in {location or 'Poland'}.\n\n💡 **Tip**: Try asking me to 'search for {search_query} jobs using browser automation' for more comprehensive results from LinkedIn, Indeed, and other major job boards!"
            
            job_list = [job.dict() for job in results]
            
            # Format the response nicely for the user
            formatted_jobs = []
            for i, job in enumerate(job_list, 1):
                job_text = f"**{i}. {job.get('title', 'Job Title')}** at **{job.get('company', 'Company')}**"
                
                if job.get('location'):
                    job_text += f"\n   📍 **Location:** {job['location']}"
                
                if job.get('employment_type'):
                    job_text += f"\n   💼 **Type:** {job['employment_type']}"
                
                if job.get('salary_range'):
                    job_text += f"\n   💰 **Salary:** {job['salary_range']}"
                
                if job.get('description'):
                    # Clean up and truncate description
                    desc = job['description'].replace('\n', ' ').strip()
                    if len(desc) > 300:
                        desc = desc[:300] + "..."
                    job_text += f"\n   📋 **Description:** {desc}"
                
                if job.get('requirements'):
                    req = job['requirements'].replace('\n', ' ').strip()
                    if len(req) > 200:
                        req = req[:200] + "..."
                    job_text += f"\n   ✅ **Requirements:** {req}"
                
                if job.get('apply_url'):
                    job_text += f"\n   🔗 **Apply:** [{job['apply_url']}]({job['apply_url']})"
                    # Remove automatic cover letter link
                
                formatted_jobs.append(job_text)
            
            # Check if we used Browser Use Cloud data
            using_cloud_data = any('Browser Use Cloud' in str(job.get('source', '')) for job in job_list) or len([job for job in job_list if job.get('apply_url', '').startswith('http')]) > 0
            
            if using_cloud_data:
                result_header = f"🔍 **Found {len(job_list)} real jobs for '{search_query}' in {location or 'Poland'}** (via Browser Use Cloud):\n\n"
                result_footer = f"\n\n✨ **These are real job postings!** Click the URLs to apply directly. Want even more detailed results? Ask me to 'search with comprehensive browser automation'!"
            else:
                result_header = f"🔍 **Found {len(job_list)} jobs for '{search_query}' in {location or 'Poland'}** (sample results):\n\n"
                result_footer = f"\n\n💡 **Want real job postings?** Ask me to 'search for {search_query} jobs using browser automation' for live results from LinkedIn, Indeed, and other major job boards!"
            
            result_body = "\n\n---\n\n".join(formatted_jobs)
            
            return result_header + result_body + result_footer

        except Exception as e:
            log.error(f"Error in search_jobs_tool: {e}", exc_info=True)
            return f"Sorry, I encountered an error while searching for jobs: {str(e)}. Please try again with different search terms."
