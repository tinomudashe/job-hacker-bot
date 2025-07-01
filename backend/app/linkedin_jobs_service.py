"""
LinkedIn Jobs API Service
Provides job search capabilities using the linkedin-jobs-api Node.js package.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

log = logging.getLogger(__name__)

class LinkedInJobResult(BaseModel):
    position: str
    company: str
    company_logo: Optional[str] = None
    location: str
    date: Optional[str] = None
    ago_time: Optional[str] = None
    salary: Optional[str] = None
    job_url: str

class LinkedInJobsService:
    """Service to interact with LinkedIn Jobs API via Node.js subprocess."""
    
    def __init__(self):
        # Get the backend directory at initialization
        self.backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.node_script_template = '''
const linkedIn = require('linkedin-jobs-api');

async function searchJobs() {
    try {
        const queryOptions = {QUERY_OPTIONS};
        
        console.log('🔍 Searching LinkedIn with options:', JSON.stringify(queryOptions, null, 2));
        
        const response = await linkedIn.query(queryOptions);
        
        console.log('✅ LinkedIn API response received');
        console.log('📊 Found', response.length, 'jobs');
        
        // Output the results as JSON
        console.log('LINKEDIN_RESULTS_START');
        console.log(JSON.stringify(response, null, 2));
        console.log('LINKEDIN_RESULTS_END');
        
    } catch (error) {
        console.error('❌ LinkedIn API Error:', error.message);
        console.log('LINKEDIN_ERROR_START');
        console.log(JSON.stringify({ error: error.message }, null, 2));
        console.log('LINKEDIN_ERROR_END');
    }
}

searchJobs();
'''

    async def search_jobs(
        self,
        keyword: str,
        location: str = "Remote",
        date_since_posted: str = "past week",
        job_type: str = "",
        remote_filter: str = "",
        salary: str = "",
        experience_level: str = "",
        limit: int = 10,
        page: int = 0
    ) -> List[LinkedInJobResult]:
        """
        Search for jobs on LinkedIn using the linkedin-jobs-api package.
        
        Args:
            keyword: Job search terms (e.g., 'software engineer')
            location: Location to search in (e.g., 'Poland', 'Remote')
            date_since_posted: Max range of jobs ('past month', 'past week', '24hr')
            job_type: Type of position ('full time', 'part time', 'contract', 'temporary', 'volunteer', 'internship')
            remote_filter: Filter telecommuting ('on site', 'remote', 'hybrid')
            salary: Minimum Salary ('40000', '60000', '80000', '100000', '120000')
            experience_level: Experience level ('internship', 'entry level', 'associate', 'senior', 'director', 'executive')
            limit: Number of jobs to return (max 25 for free API)
            page: Page number for pagination
        
        Returns:
            List of LinkedInJobResult objects
        """
        try:
            # Prepare query options
            query_options = {
                "keyword": keyword,
                "location": location,
                "dateSincePosted": date_since_posted,
                "limit": str(min(limit, 25)),  # API limit
                "page": str(page)
            }
            
            # Add optional filters only if provided
            if job_type:
                query_options["jobType"] = job_type
            if remote_filter:
                query_options["remoteFilter"] = remote_filter
            if salary:
                query_options["salary"] = salary
            if experience_level:
                query_options["experienceLevel"] = experience_level
            
            log.info(f"🔍 Searching LinkedIn for '{keyword}' in '{location}'")
            log.info(f"📋 Query options: {query_options}")
            
            # Create the Node.js script
            script_content = self.node_script_template.replace(
                '{QUERY_OPTIONS}', 
                json.dumps(query_options, indent=8)
            )
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            try:
                # Execute the Node.js script
                log.info(f"🚀 Executing LinkedIn API call...")
                log.info(f"📁 Backend directory: {self.backend_dir}")
                log.info(f"📄 Script path: {script_path}")
                
                node_modules_path = os.path.join(self.backend_dir, 'node_modules')
                log.info(f"📦 Node modules exists: {os.path.exists(node_modules_path)}")
                
                # Set up environment with NODE_PATH pointing to our node_modules
                env = os.environ.copy()
                env['NODE_PATH'] = node_modules_path
                
                process = await asyncio.create_subprocess_exec(
                    'node', script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    cwd=self.backend_dir
                )
                
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
                
                # Decode output
                stdout_str = stdout.decode('utf-8')
                stderr_str = stderr.decode('utf-8')
                
                log.info(f"📤 Node.js stdout: {stdout_str}")
                if stderr_str:
                    log.warning(f"⚠️ Node.js stderr: {stderr_str}")
                
                # Parse results
                jobs = self._parse_node_output(stdout_str)
                
                log.info(f"✅ Successfully retrieved {len(jobs)} jobs from LinkedIn")
                return jobs
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(script_path)
                except OSError:
                    pass
                    
        except asyncio.TimeoutError:
            log.error("⏰ LinkedIn API call timed out after 60 seconds")
            return []
        except Exception as e:
            log.error(f"❌ Error calling LinkedIn API: {e}")
            return []
    
    def _parse_node_output(self, output: str) -> List[LinkedInJobResult]:
        """Parse the Node.js script output to extract job results."""
        try:
            # Look for results between markers
            if 'LINKEDIN_RESULTS_START' in output and 'LINKEDIN_RESULTS_END' in output:
                start_marker = 'LINKEDIN_RESULTS_START'
                end_marker = 'LINKEDIN_RESULTS_END'
                
                start_idx = output.find(start_marker) + len(start_marker)
                end_idx = output.find(end_marker)
                
                if start_idx > len(start_marker) and end_idx > start_idx:
                    json_str = output[start_idx:end_idx].strip()
                    
                    try:
                        jobs_data = json.loads(json_str)
                        
                        if isinstance(jobs_data, list):
                            jobs = []
                            for job_data in jobs_data:
                                if isinstance(job_data, dict):
                                    try:
                                        job = LinkedInJobResult(
                                            position=job_data.get('position', 'Unknown Position'),
                                            company=job_data.get('company', 'Unknown Company'),
                                            company_logo=job_data.get('companyLogo'),
                                            location=job_data.get('location', 'Unknown Location'),
                                            date=job_data.get('date'),
                                            ago_time=job_data.get('agoTime'),
                                            salary=job_data.get('salary') if job_data.get('salary') else None,
                                            job_url=job_data.get('jobUrl', '')
                                        )
                                        jobs.append(job)
                                    except Exception as e:
                                        log.warning(f"⚠️ Failed to parse job data: {e}")
                                        continue
                            
                            return jobs
                        
                    except json.JSONDecodeError as e:
                        log.error(f"❌ Failed to parse JSON response: {e}")
                        log.error(f"📄 Raw JSON string: {json_str}")
            
            # Check for errors
            if 'LINKEDIN_ERROR_START' in output and 'LINKEDIN_ERROR_END' in output:
                start_marker = 'LINKEDIN_ERROR_START'
                end_marker = 'LINKEDIN_ERROR_END'
                
                start_idx = output.find(start_marker) + len(start_marker)
                end_idx = output.find(end_marker)
                
                if start_idx > len(start_marker) and end_idx > start_idx:
                    error_str = output[start_idx:end_idx].strip()
                    try:
                        error_data = json.loads(error_str)
                        log.error(f"❌ LinkedIn API returned error: {error_data.get('error', 'Unknown error')}")
                    except json.JSONDecodeError:
                        log.error(f"❌ LinkedIn API error (unparseable): {error_str}")
            
            log.warning("⚠️ No valid job results found in Node.js output")
            return []
            
        except Exception as e:
            log.error(f"❌ Error parsing Node.js output: {e}")
            return []

# Global instance
_linkedin_service = None

def get_linkedin_jobs_service() -> LinkedInJobsService:
    """Get the global LinkedIn Jobs service instance."""
    global _linkedin_service
    if _linkedin_service is None:
        _linkedin_service = LinkedInJobsService()
    return _linkedin_service 