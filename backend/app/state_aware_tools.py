"""
State-Aware Tool System for LangGraph
Wraps tools to automatically inject state while maintaining LangChain compatibility
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.tools import StructuredTool
from app.state_types import WebSocketState

log = logging.getLogger(__name__)

class StateAwareToolNode:
    """
    Custom ToolNode that maintains state context for tools
    Transparently passes state to tools that need it
    """
    
    def __init__(self, tools: List[StructuredTool], state_provider=None):
        """
        Initialize with tools and optional state provider
        
        Args:
            tools: List of StructuredTool instances
            state_provider: Callable that returns current state
        """
        self.tools = {tool.name: tool for tool in tools}
        self.state_provider = state_provider
        self._current_state = None
        log.info(f"StateAwareToolNode initialized with {len(self.tools)} tools")
    
    def set_state(self, state: WebSocketState):
        """Set the current state for tool execution"""
        self._current_state = state
        log.debug(f"State updated for user {state.get('user_id')}")
    
    async def ainvoke(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tools with state injection
        Compatible with LangGraph's expected interface
        """
        messages = input_dict.get("messages", [])
        
        # Get state from provider if available
        if self.state_provider and not self._current_state:
            self._current_state = self.state_provider()
        
        # Find the last AI message with tool calls
        last_message = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                last_message = msg
                break
        
        if not last_message:
            log.debug("No tool calls found in messages")
            return {"messages": []}
        
        result_messages = []
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", f"{tool_name}_call")
            
            log.info(f"Executing tool: {tool_name} with args: {list(tool_args.keys())}")
            
            if tool_name not in self.tools:
                error_msg = f"Tool {tool_name} not found"
                log.error(error_msg)
                result_messages.append(
                    ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                )
                continue
            
            tool = self.tools[tool_name]
            
            try:
                # IMPORTANT: Check if the tool is async and await it properly
                import asyncio
                import inspect
                
                # Get the actual function from the tool
                if hasattr(tool, 'func'):
                    func = tool.func
                elif hasattr(tool, 'coroutine'):
                    func = tool.coroutine
                else:
                    func = tool
                
                # Execute the tool
                if asyncio.iscoroutinefunction(func):
                    # It's an async function, use ainvoke
                    result = await tool.ainvoke(tool_args)
                else:
                    # It's a sync function, check if tool has ainvoke
                    if hasattr(tool, 'ainvoke'):
                        result = await tool.ainvoke(tool_args)
                    else:
                        # Fallback to sync invoke
                        result = tool.invoke(tool_args)
                
                # CRITICAL: If result is still a coroutine, await it
                if asyncio.iscoroutine(result):
                    log.warning(f"Tool {tool_name} returned unawaited coroutine, awaiting now...")
                    result = await result
                
                # Convert result to string
                result_str = str(result) if result is not None else "Tool executed successfully"
                
                log.info(f"Tool {tool_name} executed successfully, result length: {len(result_str)}")
                
                result_messages.append(
                    ToolMessage(
                        content=result_str,
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                )
                
            except Exception as e:
                error_msg = f"Error executing {tool_name}: {str(e)}"
                log.error(error_msg, exc_info=True)
                result_messages.append(
                    ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                )
        
        return {"messages": result_messages}

def create_state_aware_tool(tool_func, name: str, description: str, state_getter):
    """
    Create a state-aware tool that automatically gets state from context
    
    Args:
        tool_func: The actual tool function (can expect state as first parameter)
        name: Tool name
        description: Tool description  
        state_getter: Function that returns current state
    """
    
    # Check if the function expects state as first parameter
    import inspect
    sig = inspect.signature(tool_func)
    params = list(sig.parameters.keys())
    expects_state = len(params) > 0 and params[0] == 'state'
    
    if expects_state:
        # Create wrapper that injects state
        async def wrapped_tool(**kwargs):
            """Wrapper that injects state automatically"""
            current_state = state_getter()
            if current_state:
                return await tool_func(current_state, **kwargs)
            else:
                # Fallback - create minimal state if needed
                minimal_state = {
                    "user_id": kwargs.get("_user_id", "unknown"),
                    "messages": [],
                    "tool_results": {},
                    "executed_tools": [],
                    "pending_tools": [],
                    "confidence_score": 1.0,
                    "processing_stage": "tool_execution"
                }
                return await tool_func(minimal_state, **kwargs)
        
        # Mark the wrapper so we know it handles state
        wrapped_tool.__wrapped__ = tool_func
        
        # Create tool from wrapper
        return StructuredTool.from_function(
            func=wrapped_tool,
            name=name,
            description=description
        )
    else:
        # Regular tool, no state injection needed
        return StructuredTool.from_function(
            func=tool_func,
            name=name,
            description=description
        )


class StateManager:
    """Singleton to manage state across tool executions"""
    
    _instance = None
    _state: Optional[WebSocketState] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_state(self, state: WebSocketState):
        """Set the current state"""
        self._state = state
        log.debug(f"StateManager updated for user {state.get('user_id')}")
    
    def get_state(self) -> Optional[WebSocketState]:
        """Get the current state"""
        return self._state
    
    def clear_state(self):
        """Clear the current state"""
        self._state = None


# Global state manager instance
state_manager = StateManager()