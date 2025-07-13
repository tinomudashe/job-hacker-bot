#!/usr/bin/env python3
"""Test job extraction from URLs using the Playwright browser tool."""

import asyncio
from app.langchain_webbrowser import create_webbrowser_tool

async def test_job_extraction():
    """Test extracting job details from a URL."""
    print("🧪 Testing job extraction with Playwright browser tool...\n")
    
    # Test URL (Veeam job posting)
    job_url = "https://job-boards.eu.greenhouse.io/veeamsoftware/jobs/4593587101?gh_src=f754f242teu"
    
    # Create browser tool
    browser_tool = create_webbrowser_tool()
    
    # Extract content using the tool
    print(f"📄 Extracting content from: {job_url}")
    
    # Run sync tool in async context
    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(None, browser_tool.invoke, {"url": job_url})
    
    print(f"\n✅ Extracted {len(content)} characters")
    print("\n📋 Content preview:")
    print("-" * 50)
    print(content[:1000])
    print("-" * 50)
    
    # Check if we got job-related content
    if "Frontend Developer" in content or "Veeam" in content:
        print("\n✅ Successfully extracted job posting content!")
        
        # Parse key information
        lines = content.split('\n')
        for line in lines[:20]:  # Check first 20 lines
            if line.strip():
                print(f"  • {line.strip()}")
    else:
        print("\n⚠️  Content extracted but might not be the job posting")
    
    return True

async def main():
    """Run the test."""
    try:
        await test_job_extraction()
        print("\n✅ Job extraction test completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 