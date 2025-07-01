"""
Browser Use Cloud API Integration
Provides browser automation capabilities using the Browser Use Cloud service.
"""

import asyncio
import logging
import json
import aiohttp
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

log = logging.getLogger(__name__)

class BrowserTaskResponse(BaseModel):
    task_id: str
    live_url: Optional[str] = None
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class JobExtractionResult(BaseModel):
    title: str
    company: str
    location: str
    description: str
    requirements: str
    url: str
    salary: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None

class BrowserUseCloudService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.browser-use.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def run_task(self, task: str, model: str = "gemini-2.0-flash") -> BrowserTaskResponse:
        """
        Run a browser automation task using the Browser Use Cloud API.
        
        Args:
            task: Natural language description of the task to perform
            model: LLM model to use (gemini-2.0-flash is cost-effective at $0.01/step)
        
        Returns:
            BrowserTaskResponse with task details and results
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "task": task,
                    "model": model
                }
                
                log.info(f"Starting browser task: {task[:100]}...")
                
                async with session.post(
                    f"{self.base_url}/run-task",
                    headers=self.headers,
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        log.error(f"Browser Use API error: {response.status} - {error_text}")
                        return BrowserTaskResponse(
                            task_id="",
                            status="error",
                            error=f"API error: {response.status} - {error_text}"
                        )
                    
                    result = await response.json()
                    
                    # Handle different response formats
                    task_id = result.get("task_id") or result.get("id") or ""
                    live_url = result.get("live_url") or result.get("preview_url")
                    status = result.get("status", "running")
                    
                    log.info(f"Task started successfully: {task_id}")
                    if live_url:
                        log.info(f"Live preview available: {live_url}")
                    
                    return BrowserTaskResponse(
                        task_id=task_id,
                        live_url=live_url,
                        status=status,
                        result=result
                    )
                    
        except Exception as e:
            log.error(f"Error running browser task: {e}")
            return BrowserTaskResponse(
                task_id="",
                status="error",
                error=str(e)
            )

    async def get_task_status(self, task_id: str) -> BrowserTaskResponse:
        """Get the current status of a running task."""
        try:
            async with aiohttp.ClientSession() as session:
                # Try different possible endpoints for task status
                possible_endpoints = [
                    f"{self.base_url}/get-task/{task_id}",
                    f"{self.base_url}/get-task-status/{task_id}", 
                    f"{self.base_url}/task/{task_id}",
                    f"{self.base_url}/tasks/{task_id}"
                ]
                
                for endpoint in possible_endpoints:
                    try:
                        async with session.get(endpoint, headers=self.headers) as response:
                            if response.status == 200:
                                result = await response.json()
                                return BrowserTaskResponse(
                                    task_id=task_id,
                                    status=result.get("status", "unknown"),
                                    result=result
                                )
                            elif response.status == 404:
                                continue  # Try next endpoint
                            else:
                                error_text = await response.text()
                                log.warning(f"Endpoint {endpoint} returned {response.status}: {error_text}")
                                continue
                    except Exception as e:
                        log.warning(f"Failed to check endpoint {endpoint}: {e}")
                        continue
                
                # If all endpoints failed, return error
                return BrowserTaskResponse(
                    task_id=task_id,
                    status="error",
                    error="Could not find valid status endpoint"
                )
                    
        except Exception as e:
            log.error(f"Error checking task status: {e}")
            return BrowserTaskResponse(
                task_id=task_id,
                status="error",
                error=str(e)
            )

    async def wait_for_completion(self, task_id: str, timeout: int = 300) -> BrowserTaskResponse:
        """
        Wait for a task to complete with detailed progress tracking.
        
        Args:
            task_id: The task ID to monitor
            timeout: Maximum time to wait in seconds (default 5 minutes)
        """
        start_time = datetime.now()
        last_status = None
        progress_stages = {
            "created": "🔨 Initializing browser automation...",
            "pending": "⏳ Queuing browser task...",
            "running": "🌐 Browser is actively working...",
            "processing": "⚙️ Processing search results...",
            "extracting": "📄 Extracting job information...",
            "completing": "✅ Finalizing results...",
            "completed": "🎉 Job search completed successfully!",
            "failed": "❌ Task failed",
            "error": "⚠️ Error occurred"
        }
        
        elapsed_minutes = 0
        
        while (datetime.now() - start_time).seconds < timeout:
            status_response = await self.get_task_status(task_id)
            current_status = status_response.status.lower()
            
            # Show progress updates only when status changes or every minute
            current_elapsed = (datetime.now() - start_time).seconds
            current_minutes = current_elapsed // 60
            
            if current_status != last_status or current_minutes > elapsed_minutes:
                progress_message = progress_stages.get(current_status, f"🔄 Status: {current_status}")
                time_info = f"[{current_minutes}m {current_elapsed % 60}s elapsed]"
                
                if current_status == "running":
                    # Add more specific running status based on elapsed time
                    if current_elapsed < 30:
                        progress_message = "🌐 Opening browser and navigating to job board..."
                    elif current_elapsed < 60:
                        progress_message = "🔍 Entering search terms and location..."
                    elif current_elapsed < 120:
                        progress_message = "📋 Loading and analyzing job listings..."
                    elif current_elapsed < 180:
                        progress_message = "📊 Extracting detailed job information..."
                    else:
                        progress_message = "⚡ Finalizing comprehensive job search..."
                
                log.info(f"Browser automation progress: {progress_message} {time_info}")
                last_status = current_status
                elapsed_minutes = current_minutes
            
            # Check if task is complete
            if current_status in ["completed", "finished", "success", "done"]:
                log.info(f"✅ Browser automation completed successfully after {current_elapsed}s")
                # Make sure we update the status to "completed" for consistent handling
                if current_status == "finished":
                    status_response.status = "completed"
                return status_response
            elif current_status in ["failed", "error", "cancelled", "timeout"]:
                log.error(f"❌ Browser automation failed: {status_response.error or 'Unknown error'}")
                return status_response
            
            await asyncio.sleep(3)  # Check every 3 seconds
        
        # Timeout reached
        final_elapsed = (datetime.now() - start_time).seconds
        log.warning(f"⏰ Browser automation timed out after {final_elapsed}s (limit: {timeout}s)")
        return BrowserTaskResponse(
            task_id=task_id,
            status="timeout",
            error=f"Browser automation timed out after {timeout} seconds. Task may still be running in background."
        )

    async def search_jobs_on_platform(
        self, 
        query: str, 
        location: str = "Poland", 
        platform: str = "linkedin",
        max_jobs: int = 5
    ) -> List[JobExtractionResult]:
        """
        Search for jobs on a specific platform using browser automation.
        
        Args:
            query: Job search terms (e.g., 'software engineer')
            location: Location to search in
            platform: Job platform ('linkedin', 'indeed', 'glassdoor')
            max_jobs: Maximum number of jobs to extract
        """
        try:
            # Create comprehensive task instruction
            task_instruction = self._create_job_search_task(query, location, platform, max_jobs)
            
            # Start the browser automation task
            task_response = await self.run_task(task_instruction, model="gemini-2.0-flash")
            
            if task_response.status == "error":
                log.error(f"Failed to start job search task: {task_response.error}")
                return []
            
            log.info(f"Job search task started: {task_response.task_id}")
            if task_response.live_url:
                log.info(f"Live preview: {task_response.live_url}")
            
            # Wait for completion with 5-minute timeout for comprehensive search
            completed_task = await self.wait_for_completion(task_response.task_id, timeout=300)
            
            if completed_task.status not in ["completed", "finished", "success"]:
                log.error(f"Job search task failed or timed out: {completed_task.status} - {completed_task.error}")
                return []
            
            # Extract job results from the completed task
            extracted_jobs = await self._extract_job_results(completed_task)
            
            if len(extracted_jobs) > 0:
                log.info(f"✅ Successfully found {len(extracted_jobs)} jobs via Browser Use Cloud")
            else:
                log.warning("Browser automation completed but no jobs were extracted from the results")
                log.warning(f"Raw result data: {completed_task.result}")
            
            return extracted_jobs
            
        except Exception as e:
            log.error(f"Error in job search: {e}")
            return []

    def _create_job_search_task(self, query: str, location: str, platform: str, max_jobs: int) -> str:
        """Create a detailed task instruction for job searching without login requirements."""
        
        # Use public job boards that don't require login and work internationally
        platform_urls = {
            "indeed": "https://www.indeed.com",
            "glassdoor": "https://www.glassdoor.com/Job", 
            "justjoin": "https://justjoin.it",
            "nofluffjobs": "https://nofluffjobs.com",
            "linkedin": "https://www.indeed.com"  # Redirect LinkedIn to Indeed to avoid login
        }
        
        base_url = platform_urls.get(platform.lower(), "https://www.indeed.com")
        
        # Simplified task that avoids login and focuses on URL collection
        task = f"""
        IMPORTANT: Do NOT attempt to sign in or log in to any website. If you see a login prompt, close it or skip it.

        Go to {base_url} and find "{query}" jobs in "{location}".

        Steps:
        1. Navigate to {base_url}
        2. Look for a search box and enter: "{query}"
        3. Look for a location field and enter: "{location}" 
        4. Click the search button
        5. Wait for job results to load (avoid any login prompts)
        6. Extract the first {max_jobs} job listings from the search results

        For each job listing, collect:
        - Job title
        - Company name  
        - Location
        - Brief description (first 200 characters visible)
        - Direct link/URL to the full job posting
        - Salary if visible
        - Job type if visible

        CRITICAL: If the site asks you to sign in, log in, or create an account:
        - Click "Skip" or "Not now" or "Continue without signing in"
        - Look for "View jobs without signing in" options
        - Close any popup or modal that asks for login
        - DO NOT enter any credentials

        Return the job data as a simple list. Focus on getting job titles, companies, and URLs.
        """
        
        return task.strip()

    async def _extract_job_results(self, completed_task: BrowserTaskResponse) -> List[JobExtractionResult]:
        """Extract job results from completed browser task."""
        try:
            if not completed_task.result:
                log.warning("No result data in completed task")
                return []
            
            result_data = completed_task.result
            log.info(f"Processing result data type: {type(result_data)}")
            
            # Look for job data in various possible response formats
            jobs_data = []
            
            if isinstance(result_data, dict):
                log.info(f"Result data keys: {list(result_data.keys())}")
                
                # Check common response fields
                if "jobs" in result_data:
                    jobs_data = result_data["jobs"]
                elif "job_listings" in result_data:
                    jobs_data = result_data["job_listings"] 
                elif "data" in result_data:
                    jobs_data = result_data["data"]
                elif "results" in result_data:
                    jobs_data = result_data["results"]
                elif "output" in result_data:
                    # Browser Use Cloud might return results in "output" field
                    output_data = result_data["output"]
                    if isinstance(output_data, str):
                        # Try to parse JSON string
                        try:
                            import json
                            parsed_output = json.loads(output_data)
                            if isinstance(parsed_output, list):
                                jobs_data = parsed_output
                            elif isinstance(parsed_output, dict) and "job_listings" in parsed_output:
                                jobs_data = parsed_output["job_listings"]
                        except json.JSONDecodeError:
                            log.warning("Failed to parse output JSON")
                    elif isinstance(output_data, list):
                        jobs_data = output_data
                    elif isinstance(output_data, dict):
                        if "job_listings" in output_data:
                            jobs_data = output_data["job_listings"]
                        elif "jobs" in output_data:
                            jobs_data = output_data["jobs"]
                else:
                    # Check if the result itself contains job fields
                    if "job_title" in result_data or "title" in result_data:
                        jobs_data = [result_data]
                    else:
                        # Look for any list values that might contain jobs
                        for key, value in result_data.items():
                            if isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], dict) and ("title" in value[0] or "job_title" in value[0]):
                                    jobs_data = value
                                    break
                        
            elif isinstance(result_data, list):
                jobs_data = result_data
            elif isinstance(result_data, str):
                # Try to parse as JSON
                try:
                    import json
                    parsed_data = json.loads(result_data)
                    if isinstance(parsed_data, list):
                        jobs_data = parsed_data
                    elif isinstance(parsed_data, dict):
                        if "job_listings" in parsed_data:
                            jobs_data = parsed_data["job_listings"]
                        elif "jobs" in parsed_data:
                            jobs_data = parsed_data["jobs"]
                except json.JSONDecodeError:
                    log.warning("Failed to parse result as JSON")
            
            log.info(f"Found {len(jobs_data)} job entries to process")
            
            # Convert to JobExtractionResult objects
            extracted_jobs = []
            for i, job_data in enumerate(jobs_data):
                if isinstance(job_data, dict):
                    try:
                        # Handle different field name variations
                        title = (job_data.get("job_title") or 
                                job_data.get("title") or 
                                job_data.get("position") or 
                                "Unknown Title")
                        
                        company = (job_data.get("company_name") or 
                                  job_data.get("company") or 
                                  job_data.get("employer") or 
                                  "Unknown Company")
                        
                        location = (job_data.get("location") or 
                                   job_data.get("city") or 
                                   job_data.get("place") or 
                                   "Unknown Location")
                        
                        description = (job_data.get("brief_description") or 
                                     job_data.get("description") or 
                                     job_data.get("summary") or 
                                     "")
                        
                        url = (job_data.get("direct_link") or 
                              job_data.get("url") or 
                              job_data.get("link") or 
                              job_data.get("apply_url") or 
                              "")
                        
                        salary = job_data.get("salary")
                        job_type = job_data.get("job_type")
                        
                        job = JobExtractionResult(
                            title=title,
                            company=company,
                            location=location,
                            description=description,
                            requirements=job_data.get("requirements", ""),
                            url=url,
                            salary=salary,
                            job_type=job_type,
                            posted_date=job_data.get("posted_date")
                        )
                        extracted_jobs.append(job)
                        log.info(f"Successfully extracted job {i+1}: {title} at {company}")
                        
                    except Exception as e:
                        log.warning(f"Failed to parse job data {i+1}: {e}")
                        log.warning(f"Job data: {job_data}")
                        continue
                else:
                    log.warning(f"Job data {i+1} is not a dict: {type(job_data)}")
            
            log.info(f"Successfully extracted {len(extracted_jobs)} jobs from {len(jobs_data)} entries")
            return extracted_jobs
            
        except Exception as e:
            log.error(f"Error extracting job results: {e}")
            log.error(f"Result data: {completed_task.result}")
            return []

    async def extract_job_from_url(self, job_url: str) -> Optional[JobExtractionResult]:
        """
        Extract detailed job information from a specific job URL.
        
        Args:
            job_url: Direct URL to a job posting
            
        Returns:
            JobExtractionResult with extracted job details
        """
        try:
            task_instruction = f"""
            Go to {job_url} and extract all available job information.
            
            Extract:
            - Job title
            - Company name
            - Location
            - Full job description
            - Requirements and qualifications
            - Salary information (if available)
            - Job type (full-time, part-time, contract, etc.)
            - Posted date
            - Benefits (if mentioned)
            
            Return the information as a JSON object with these fields:
            {{
                "title": "Job Title",
                "company": "Company Name",
                "location": "Location", 
                "description": "Full job description...",
                "requirements": "Requirements and qualifications...",
                "url": "{job_url}",
                "salary": "Salary information",
                "job_type": "Employment type",
                "posted_date": "When posted"
            }}
            """
            
            # Start the task
            task_response = await self.run_task(task_instruction, model="gemini-2.0-flash")
            
            if task_response.status == "error":
                log.error(f"Failed to start job extraction task: {task_response.error}")
                return None
            
            # Wait for completion  
            completed_task = await self.wait_for_completion(task_response.task_id, timeout=300)
            
            if completed_task.status != "completed":
                log.error(f"Job extraction failed: {completed_task.status}")
                return None
            
            # Extract the job information
            if completed_task.result:
                job_data = completed_task.result
                
                # Handle different response formats
                if isinstance(job_data, dict):
                    return JobExtractionResult(
                        title=job_data.get("title", ""),
                        company=job_data.get("company", ""),
                        location=job_data.get("location", ""),
                        description=job_data.get("description", ""),
                        requirements=job_data.get("requirements", ""),
                        url=job_url,
                        salary=job_data.get("salary"),
                        job_type=job_data.get("job_type"),
                        posted_date=job_data.get("posted_date")
                    )
            
            return None
            
        except Exception as e:
            log.error(f"Error extracting job from URL: {e}")
            return None


# Global instance
_browser_service = None

def get_browser_use_service() -> BrowserUseCloudService:
    """Get the global Browser Use Cloud service instance."""
    global _browser_service
    if _browser_service is None:
        api_key = "bu_vX4S9JvacU0xKbk_6aYsyHUQGioiff3L4Dh8s1qkKkI"
        _browser_service = BrowserUseCloudService(api_key)
    return _browser_service 