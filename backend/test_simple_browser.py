#!/usr/bin/env python3
"""
Test script for the simple browser tool that uses subprocess.
"""

import logging
from app.simple_browser_tool import create_simple_browser_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_browser_tool():
    """Test the simple browser tool."""
    print("🧪 Testing simple browser tool...")
    
    try:
        # Create the tool
        tool = create_simple_browser_tool()
        print(f"✅ Tool created: {tool.name}")
        print(f"📝 Description: {tool.description}")
        
        # Test with a simple webpage
        print("🔍 Testing navigation to httpbin.org...")
        result = tool.func("https://httpbin.org/html")
        print(f"📄 Result:\n{result}")
        
        # Check if the result looks successful
        if "successfully scraped" in result.lower() and "moby" in result.lower():
            print("✅ Tool executed successfully and got expected content")
            return True
        elif "error" in result.lower() or "failed" in result.lower():
            print("❌ Tool returned an error")
            return False
        else:
            print("⚠️  Tool executed but result is unclear")
            return False
            
    except Exception as e:
        print(f"❌ Simple browser tool test failed: {e}")
        return False

def main():
    """Run the test."""
    print("🚀 Starting Simple Browser Tool Test\n")
    
    success = test_simple_browser_tool()
    
    print(f"\n📊 Test Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 Simple browser tool is working correctly!")
    else:
        print("\n⚠️  Test failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 