from langchain_core.tools import tool
import logging
from app.linkedin_jobs_service import get_linkedin_jobs_service

log = logging.getLogger(__name__)

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
        """
        try:
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
