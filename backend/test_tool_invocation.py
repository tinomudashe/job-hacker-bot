#!/usr/bin/env python3
"""
Test script to identify where sync invocation is happening with StructuredTool
"""

import asyncio
import logging
from typing import Dict, Any
from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test 1: Create a StructuredTool with async function
async def async_test_function(input_text: str) -> str:
    """Test async function"""
    logger.info(f"Async function called with: {input_text}")
    return f"Processed: {input_text}"

def sync_test_function(input_text: str) -> str:
    """Test sync function"""
    logger.info(f"Sync function called with: {input_text}")
    return f"Processed: {input_text}"

async def test_structured_tool_creation():
    """Test different ways of creating StructuredTool"""
    
    print("\n" + "="*60)
    print("TEST 1: StructuredTool with async function as 'func'")
    print("="*60)
    try:
        # Wrong way - passing async function as func
        tool1 = StructuredTool.from_function(
            func=async_test_function,  # WRONG for async
            name="test_tool_wrong",
            description="Test tool with wrong parameter"
        )
        
        # Try to invoke it
        result = await tool1.ainvoke({"input_text": "test1"})
        print(f"✓ Success with func parameter: {result}")
    except Exception as e:
        print(f"✗ Error with func parameter: {e}")
    
    print("\n" + "="*60)
    print("TEST 2: StructuredTool with async function as 'coroutine'")
    print("="*60)
    try:
        # Right way - passing async function as coroutine
        tool2 = StructuredTool.from_function(
            coroutine=async_test_function,  # CORRECT for async
            name="test_tool_right",
            description="Test tool with correct parameter"
        )
        
        # Try to invoke it
        result = await tool2.ainvoke({"input_text": "test2"})
        print(f"✓ Success with coroutine parameter: {result}")
    except Exception as e:
        print(f"✗ Error with coroutine parameter: {e}")
    
    print("\n" + "="*60)
    print("TEST 3: StructuredTool with sync function")
    print("="*60)
    try:
        # Sync function as func
        tool3 = StructuredTool.from_function(
            func=sync_test_function,
            name="test_tool_sync",
            description="Test tool with sync function"
        )
        
        # Try to invoke it async
        result = await tool3.ainvoke({"input_text": "test3"})
        print(f"✓ Success with sync function: {result}")
    except Exception as e:
        print(f"✗ Error with sync function: {e}")

async def test_career_tools():
    """Test the actual CareerTools to see where the issue is"""
    print("\n" + "="*60)
    print("TEST 4: Testing actual CareerToolsLangGraph")
    print("="*60)
    
    try:
        # Import and test the actual tools
        from app.db import async_session_maker
        from app.models_db import User
        from app.orchestrator_tools import CareerToolsLangGraph
        
        # Create a mock user and session
        async with async_session_maker() as db:
            from sqlalchemy import select
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("✗ No user found in database")
                return
            
            # Create the tool instance
            career_tools = CareerToolsLangGraph(user, db)
            
            # Get the tools
            tools = career_tools.get_tools()
            
            print(f"Found {len(tools)} tools")
            
            # Check each tool
            for tool in tools:
                print(f"\nChecking tool: {tool.name}")
                print(f"  - Has func: {hasattr(tool, 'func') and tool.func is not None}")
                print(f"  - Has coroutine: {hasattr(tool, 'coroutine') and tool.coroutine is not None}")
                print(f"  - Has ainvoke: {hasattr(tool, 'ainvoke')}")
                
                # Check the actual function/coroutine
                if hasattr(tool, 'func') and tool.func:
                    import inspect
                    print(f"  - func is coroutine: {inspect.iscoroutinefunction(tool.func)}")
                if hasattr(tool, 'coroutine') and tool.coroutine:
                    import inspect
                    print(f"  - coroutine is coroutine: {inspect.iscoroutinefunction(tool.coroutine)}")
            
            # Try to invoke the review_resume_ats tool
            ats_tool = next((t for t in tools if t.name == "review_resume_ats"), None)
            if ats_tool:
                print(f"\nTrying to invoke review_resume_ats tool...")
                try:
                    # This should work if configured correctly
                    result = await ats_tool.ainvoke({"resume_text": "Test resume content"})
                    print(f"✓ Success: {result[:100]}...")
                except Exception as e:
                    print(f"✗ Error: {e}")
                    import traceback
                    traceback.print_exc()
    
    except Exception as e:
        print(f"✗ Failed to test CareerTools: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("Testing StructuredTool invocation patterns...")
    
    # Test basic StructuredTool creation
    await test_structured_tool_creation()
    
    # Test actual CareerTools
    await test_career_tools()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())