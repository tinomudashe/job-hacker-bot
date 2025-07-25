"""
Test for dependency injection issues in orchestrator_main.py
"""
import pytest
from unittest.mock import Mock, AsyncMock
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# Import the functions to test
import sys
import os
import inspect
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.orchestrator.orchestrator_main import (
    create_dependency_injected_tool, 
    create_tools_with_dependencies,
    check_tool_needs_injection
)

class TestInput(BaseModel):
    query: str = Field(description="Test query")

def test_function_tool():
    """Regular function tool"""
    async def test_tool(db, user, query: str):
        return f"Result for {query}"
    return test_tool

def test_structured_tool():
    """StructuredTool instance (this causes the AttributeError)"""
    async def _impl(query: str):
        return f"Result for {query}"
    
    return StructuredTool.from_function(
        func=_impl,
        name="test_structured_tool",
        description="A test structured tool",
        args_schema=TestInput
    )

def test_structured_tool_with_injection():
    """StructuredTool that needs dependency injection"""
    async def _impl(db, user, query: str):
        return f"Result for {query} with user {user.id}"
    
    # For dependency injection, we need to use the raw function, not StructuredTool
    # because StructuredTool strips the db/user params from args_schema
    return _impl

@pytest.mark.asyncio
async def test_structured_tool_name_access():
    """Test that StructuredTool objects don't have __name__ attribute"""
    tool = test_structured_tool()
    
    # This should work - StructuredTool has .name
    assert hasattr(tool, 'name')
    assert tool.name == "test_structured_tool"
    
    # This should fail - StructuredTool doesn't have .__name__
    assert not hasattr(tool, '__name__')

@pytest.mark.asyncio 
async def test_create_dependency_injected_tool_with_structured_tool():
    """Test that our fix handles StructuredTool objects correctly"""
    mock_db = Mock()
    mock_user = Mock()
    mock_user.id = "test_user_123"
    
    # Test with StructuredTool that doesn't need injection
    tool = test_structured_tool()
    result = create_dependency_injected_tool(tool, mock_db, mock_user)
    
    # Should return a Tool object (original function always wraps in Tool)
    assert result.name == tool.name
    assert result.description == tool.description
    
    # Test with function that needs injection  
    tool_with_deps = test_structured_tool_with_injection()
    
    # The main test: this should NOT raise AttributeError anymore
    try:
        injected_tool = create_dependency_injected_tool(tool_with_deps, mock_db, mock_user)
        # Should return a Tool object
        assert hasattr(injected_tool, 'name')
        assert callable(injected_tool)
    except AttributeError as e:
        if "__name__" in str(e):
            pytest.fail(f"AttributeError still occurs: {e}")
        else:
            raise  # Re-raise if it's a different AttributeError

@pytest.mark.asyncio
async def test_create_tools_with_dependencies_mixed_types():
    """Test creating tools with a mix of function and StructuredTool objects"""
    mock_db = Mock()
    mock_user = Mock()
    mock_user.id = "test_user_123"
    
    tools = [
        test_function_tool(),
        test_structured_tool(),
        test_structured_tool_with_injection()
    ]
    
    # This should not raise an AttributeError anymore
    result_tools = create_tools_with_dependencies(tools, mock_db, mock_user)
    
    # Should have all 3 tools
    assert len(result_tools) == 3
    
    # All should be callable
    for tool in result_tools:
        assert callable(tool)

@pytest.mark.asyncio
async def test_check_tool_needs_injection_structured_tool():
    """Test injection detection works with StructuredTool objects"""
    # Tool without injection needs
    tool_no_injection = test_structured_tool() 
    assert not check_tool_needs_injection(tool_no_injection)
    
    # Tool with injection needs
    tool_with_injection = test_structured_tool_with_injection()
    assert check_tool_needs_injection(tool_with_injection)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])