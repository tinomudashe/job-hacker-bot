import logging
log = logging.getLogger(__name__)


async def _try_basic_extraction(url: str) -> tuple:
        """Try basic HTTP scraping as fallback."""
        try:
            from app.url_scraper import scrape_job_url
            
            job_details = await scrape_job_url(url)
            # Check if we got a valid JobDetails object
            if job_details and hasattr(job_details, 'title') and hasattr(job_details, 'company'):
                return True, {
                    "job_title": job_details.title,
                    "company_name": job_details.company,
                    "job_description": f"{job_details.description}\n\nRequirements: {job_details.requirements}"
                }
            else:
                log.warning(f"Basic extraction returned invalid object type: {type(job_details)}")
                return False, None
        except Exception as e:
            log.warning(f"Basic extraction failed: {e}")
        return False, None
