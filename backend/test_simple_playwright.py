#!/usr/bin/env python3
"""
Simple test for Playwright without LangChain to check if Playwright itself works.
"""

import asyncio
from playwright.async_api import async_playwright

async def test_basic_playwright():
    """Test basic Playwright functionality."""
    print("🧪 Testing basic Playwright...")
    
    try:
        async with async_playwright() as p:
            print("✅ Playwright context created")
            
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            print("✅ Browser launched")
            
            # Create page
            page = await browser.new_page()
            print("✅ Page created")
            
            # Navigate to a simple page
            print("🔍 Navigating to httpbin.org...")
            await page.goto("https://httpbin.org/html")
            
            # Get page content
            content = await page.content()
            print(f"📄 Page content length: {len(content)} characters")
            print(f"📄 Content preview: {content[:200]}...")
            
            # Check if we got HTML content
            if "<html" in content.lower() and ("moby" in content.lower() or "herman" in content.lower()):
                print("✅ Successfully retrieved HTML content")
                success = True
            else:
                print("❌ Content doesn't look like expected HTML")
                success = False
            
            # Close browser
            await browser.close()
            print("✅ Browser closed")
            
            return success
            
    except Exception as e:
        print(f"❌ Playwright test failed: {e}")
        return False

def test_sync_wrapper():
    """Test running Playwright in a new event loop."""
    print("\n🧪 Testing Playwright in new event loop...")
    
    try:
        # Create a new event loop
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        try:
            result = new_loop.run_until_complete(test_basic_playwright())
            return result
        finally:
            new_loop.close()
            
    except Exception as e:
        print(f"❌ Sync wrapper test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Simple Playwright Tests\n")
    
    # Test 1: Basic async Playwright
    print("Test 1: Direct async test")
    async_success = await test_basic_playwright()
    
    # Test 2: Sync wrapper with new event loop
    print("\nTest 2: New event loop test")
    sync_success = test_sync_wrapper()
    
    # Summary
    print("\n📊 Test Results:")
    print(f"   Direct Async:  {'✅ PASS' if async_success else '❌ FAIL'}")
    print(f"   New Loop:      {'✅ PASS' if sync_success else '❌ FAIL'}")
    
    if async_success and sync_success:
        print("\n🎉 Playwright is working correctly!")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 