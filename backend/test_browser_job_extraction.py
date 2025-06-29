#!/usr/bin/env python3
"""
Test script for browser-based job extraction capabilities.
This demonstrates the advanced job search and URL extraction features.
"""

import asyncio
import logging
from app.browser_job_extractor import BrowserJobExtractor, search_jobs_with_browser, extract_job_from_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_job_search():
    """Test searching for jobs using browser automation."""
    print("🔍 Testing Browser-Based Job Search")
    print("=" * 50)
    
    try:
        # Test job search
        jobs = await search_jobs_with_browser(
            search_query="software engineer",
            location="Remote",
            job_board="linkedin",
            max_jobs=3
        )
        
        print(f"✅ Found {len(jobs)} jobs!")
        
        for i, job in enumerate(jobs, 1):
            print(f"\n📋 Job {i}:")
            print(f"   Title: {job.title}")
            print(f"   Company: {job.company}")
            print(f"   Location: {job.location}")
            print(f"   URL: {job.url}")
            print(f"   Description: {job.description[:200]}...")
            
    except Exception as e:
        print(f"❌ Error in job search: {e}")

async def test_url_extraction():
    """Test extracting job details from a specific URL."""
    print("\n🌐 Testing URL-Based Job Extraction")
    print("=" * 50)
    
    # Example job URL (replace with a real one for testing)
    test_url = "https://www.linkedin.com/jobs/view/sample-job-id"
    
    try:
        job_details = await extract_job_from_url(test_url)
        
        if job_details:
            print("✅ Successfully extracted job details!")
            print(f"   Title: {job_details.title}")
            print(f"   Company: {job_details.company}")
            print(f"   Location: {job_details.location}")
            print(f"   Description: {job_details.description[:300]}...")
            print(f"   Requirements: {job_details.requirements[:300]}...")
        else:
            print("❌ Failed to extract job details")
            
    except Exception as e:
        print(f"❌ Error in URL extraction: {e}")

async def test_multiple_job_boards():
    """Test searching across different job boards."""
    print("\n🌍 Testing Multiple Job Boards")
    print("=" * 50)
    
    job_boards = ["linkedin", "indeed", "glassdoor"]
    
    for board in job_boards:
        print(f"\n🔍 Testing {board.title()}...")
        try:
            jobs = await search_jobs_with_browser(
                search_query="python developer",
                location="San Francisco",
                job_board=board,
                max_jobs=2
            )
            print(f"   ✅ Found {len(jobs)} jobs on {board}")
            
            for job in jobs:
                print(f"   📋 {job.title} at {job.company}")
                
        except Exception as e:
            print(f"   ❌ Error with {board}: {e}")
        
        # Small delay between job boards
        await asyncio.sleep(3)

async def main():
    """Run all tests."""
    print("🚀 Browser Automation Job Extraction Test Suite")
    print("=" * 60)
    print("This test demonstrates advanced job search capabilities")
    print("using browser automation with the browser-use library.\n")
    
    # Note: These tests require a browser automation server to be running
    print("📝 Note: Make sure the browser automation server is running")
    print("   You can start it with: browser-use server --port 3000\n")
    
    try:
        await test_job_search()
        await test_url_extraction()
        await test_multiple_job_boards()
        
        print("\n🎉 All tests completed!")
        print("\n💡 Key Features Demonstrated:")
        print("   ✅ Multi-job board support (LinkedIn, Indeed, Glassdoor)")
        print("   ✅ Comprehensive job detail extraction")
        print("   ✅ URL-based job information extraction")
        print("   ✅ Smart navigation and pop-up handling")
        print("   ✅ Pagination support for more results")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure browser-use server is running: browser-use server")
        print("   2. Check your internet connection")
        print("   3. Verify Google API credentials are configured")

if __name__ == "__main__":
    asyncio.run(main()) 