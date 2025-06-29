#!/usr/bin/env python3

"""
Browser Compatibility Checker for Playwright
Ensures Playwright browser automation is working correctly.
"""

import asyncio
import logging
import sys
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

async def check_playwright_installation():
    """Check if Playwright is properly installed and browsers are available."""
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Check available browsers
            browsers = {
                'chromium': p.chromium,
                'firefox': p.firefox,
                'webkit': p.webkit
            }
            
            results = {}
            for name, browser_type in browsers.items():
                try:
                    browser = await browser_type.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto('https://httpbin.org/get')
                    content = await page.content()
                    await browser.close()
                    
                    results[name] = {
                        'available': True,
                        'working': True,
                        'version': browser_type.name
                    }
                    logger.info(f"✅ {name.title()} browser working correctly")
                    
                except Exception as e:
                    results[name] = {
                        'available': True,
                        'working': False,
                        'error': str(e)
                    }
                    logger.warning(f"❌ {name.title()} browser failed: {e}")
            
            return results
            
    except ImportError as e:
        logger.error(f"Playwright not installed: {e}")
        return {'error': 'Playwright not installed'}
    except Exception as e:
        logger.error(f"Playwright check failed: {e}")
        return {'error': str(e)}

async def check_system_requirements():
    """Check system requirements for browser automation."""
    import os
    import shutil
    
    checks = {}
    
    # Check for required system tools
    required_tools = ['curl', 'wget']
    for tool in required_tools:
        checks[f'{tool}_available'] = shutil.which(tool) is not None
    
    # Check environment variables
    env_vars = [
        'PLAYWRIGHT_BROWSERS_PATH',
        'GOOGLE_CLOUD_PROJECT',
        'DATABASE_URL'
    ]
    
    for var in env_vars:
        checks[f'env_{var.lower()}'] = os.getenv(var) is not None
    
    # Check memory and disk space (basic checks)
    try:
        import psutil
        checks['memory_gb'] = round(psutil.virtual_memory().total / (1024**3), 2)
        checks['disk_free_gb'] = round(psutil.disk_usage('/').free / (1024**3), 2)
    except ImportError:
        checks['memory_info'] = 'psutil not available'
    
    return checks

async def run_comprehensive_check():
    """Run all compatibility checks and return a comprehensive report."""
    print("🔍 Starting Browser Automation Compatibility Check")
    print("=" * 60)
    
    results = {
        'timestamp': asyncio.get_event_loop().time(),
        'system': await check_system_requirements(),
        'playwright': await check_playwright_installation()
    }
    
    # Determine overall compatibility
    playwright_ok = isinstance(results['playwright'], dict) and any(
        browser.get('working', False) for browser in results['playwright'].values()
        if isinstance(browser, dict)
    )
    
    results['overall_compatible'] = playwright_ok
    
    # Print summary
    print("\n📊 COMPATIBILITY SUMMARY")
    print("-" * 30)
    
    if results['overall_compatible']:
        print("✅ Overall Status: COMPATIBLE")
        print("🎉 Browser automation is ready to use!")
    else:
        print("❌ Overall Status: INCOMPATIBLE")
        print("⚠️  Browser automation may not work correctly")
    
    # Print detailed results
    print(f"\n🖥️  System Requirements:")
    for key, value in results['system'].items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value}")
    
    print(f"\n🎭 Playwright Status:")
    if isinstance(results['playwright'], dict) and 'error' not in results['playwright']:
        for browser, info in results['playwright'].items():
            if isinstance(info, dict):
                status = "✅" if info.get('working') else "❌"
                print(f"   {status} {browser}: {info.get('available', 'Unknown')}")
    else:
        print(f"   ❌ Error: {results['playwright'].get('error', 'Unknown error')}")
    
    return results

async def quick_browser_test():
    """Run a quick test to verify browser automation works end-to-end."""
    print("\n🧪 Running Quick Browser Test")
    print("-" * 30)
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Test navigation
            await page.goto('https://httpbin.org/json')
            
            # Test content extraction
            content = await page.text_content('body')
            
            # Test JavaScript execution
            title = await page.evaluate('() => document.title')
            
            await browser.close()
            
            print("✅ Navigation: Success")
            print("✅ Content extraction: Success")
            print("✅ JavaScript execution: Success")
            print(f"📄 Page title: {title}")
            
            return True
            
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        # Run comprehensive compatibility check
        results = await run_comprehensive_check()
        
        # Run quick browser test if compatible
        if results['overall_compatible']:
            test_passed = await quick_browser_test()
            results['quick_test_passed'] = test_passed
        
        # Save results to file
        with open('browser_compatibility_report.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📋 Full report saved to: browser_compatibility_report.json")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_compatible'] else 1)
    
    asyncio.run(main()) 