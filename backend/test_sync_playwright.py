#!/usr/bin/env python3
"""Test the synchronous Playwright browser tool implementation."""

import asyncio
from app.langchain_webbrowser import create_webbrowser_tool, _sync_browser_navigate

def test_sync_browser():
    """Test the synchronous browser navigation."""
    print("🧪 Testing synchronous browser navigation...")
    
    # Test with httpbin
    result = _sync_browser_navigate("https://httpbin.org/html")
    print(f"✅ Result length: {len(result)} characters")
    print(f"📄 Result preview: {result[:200]}...")
    
    # Test with a job posting URL (might fail due to protection)
    print("\n🧪 Testing with job posting URL...")
    job_url = "https://job-boards.eu.greenhouse.io/veeamsoftware/jobs/4593587101"
    result2 = _sync_browser_navigate(job_url)
    print(f"📄 Job result preview: {result2[:300]}...")
    
    return True

def test_browser_tool():
    """Test the browser tool creation."""
    print("\n🧪 Testing browser tool creation...")
    
    tool = create_webbrowser_tool()
    print(f"✅ Tool created: {tool.name}")
    print(f"📝 Description: {tool.description}")
    
    # Test tool invocation
    print("\n🧪 Testing tool invocation...")
    result = tool.invoke({"url": "https://httpbin.org/html"})
    print(f"✅ Tool result length: {len(result)} characters")
    
    return True

async def test_in_async_context():
    """Test that it works within an async context."""
    print("\n🧪 Testing in async context (simulating FastAPI)...")
    
    # This simulates what happens in FastAPI
    tool = create_webbrowser_tool()
    
    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, tool.invoke, {"url": "https://httpbin.org/html"})
    
    print(f"✅ Async context result length: {len(result)} characters")
    return True

def main():
    """Run all tests."""
    print("🚀 Starting Synchronous Playwright Browser Tool Tests\n")
    
    try:
        # Test 1: Direct sync browser
        if test_sync_browser():
            print("✅ Sync browser test passed")
        
        # Test 2: Browser tool
        if test_browser_tool():
            print("✅ Browser tool test passed")
        
        # Test 3: Async context
        try:
            asyncio.run(test_in_async_context())
            print("✅ Async context test passed")
        except RuntimeError as e:
            if "already running" in str(e):
                print("⚠️  Async context test skipped (event loop already running)")
            else:
                raise
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 