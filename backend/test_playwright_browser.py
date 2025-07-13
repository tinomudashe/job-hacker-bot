#!/usr/bin/env python3
"""
Test script for LangChain Playwright browser tool.
"""

import asyncio
import logging
from app.langchain_webbrowser import create_webbrowser_tool, get_playwright_browser_toolkit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_async_toolkit():
    """Test the async toolkit directly."""
    print("🧪 Testing async toolkit...")
    try:
        toolkit = await get_playwright_browser_toolkit()
        tools = toolkit.get_tools()
        
        print(f"✅ Toolkit created successfully")
        print(f"📋 Available tools: {[tool.name for tool in tools]}")
        
        # Try to navigate to a simple page
        navigate_tool = None
        for tool in tools:
            if "navigate" in tool.name.lower():
                navigate_tool = tool
                break
        
        if navigate_tool:
            print(f"🔍 Testing navigation with tool: {navigate_tool.name}")
            result = await navigate_tool.arun({"url": "https://httpbin.org/html"})
            print(f"📄 Navigation result (first 200 chars): {result[:200]}...")
            return True
        else:
            print("❌ No navigate tool found")
            return False
            
    except Exception as e:
        print(f"❌ Async toolkit test failed: {e}")
        return False

def test_sync_tool():
    """Test the synchronous tool wrapper."""
    print("\n🧪 Testing sync tool wrapper...")
    try:
        tool = create_webbrowser_tool()
        print(f"✅ Tool created: {tool.name}")
        print(f"📝 Description: {tool.description}")
        
        # Test with a simple webpage
        print("🔍 Testing navigation to httpbin.org...")
        result = tool.func("https://httpbin.org/html")
        print(f"📄 Result (first 300 chars): {result[:300]}...")
        
        if "error" in result.lower() or "failed" in result.lower():
            print("❌ Tool returned an error")
            return False
        else:
            print("✅ Tool executed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Sync tool test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting LangChain Playwright Browser Tests\n")
    
    # Test 1: Async toolkit
    async_success = await test_async_toolkit()
    
    # Test 2: Sync tool wrapper
    sync_success = test_sync_tool()
    
    # Summary
    print("\n📊 Test Results:")
    print(f"   Async Toolkit: {'✅ PASS' if async_success else '❌ FAIL'}")
    print(f"   Sync Tool:     {'✅ PASS' if sync_success else '❌ FAIL'}")
    
    if async_success and sync_success:
        print("\n🎉 All tests passed! Browser tool is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 