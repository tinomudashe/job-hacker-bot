#!/usr/bin/env python3
import os
import subprocess
import sys

# Set the correct Google Cloud environment variables
os.environ['GOOGLE_CLOUD_PROJECT'] = 'blogai-457111'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './app/job-bot-credentials.json'

print("Environment variables set:")
print(f"GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

# Test job search first
print("\n=== Testing Job Search ===")
try:
    from app.job_search import JobSearchRequest, search_jobs
    import asyncio
    
    async def test_search():
        search_request = JobSearchRequest(query='software engineer', location='Poland')
        results = await search_jobs(search_request, user_id='test_user', debug=False)
        print(f"✅ Job search test successful! Found {len(results)} jobs")
        return True
    
    success = asyncio.run(test_search())
    if success:
        print("\n=== Starting Server ===")
        # Start the server with the environment variables
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 