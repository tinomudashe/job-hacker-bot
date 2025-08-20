"""
State types for LangGraph - Shared between orchestrator and tools
This prevents circular imports
"""

from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class WebSocketState(TypedDict):
    """Enhanced state schema for LangGraph"""
    
    # Core conversation
    messages: Annotated[List[BaseMessage], add_messages]
    
    # WebSocket context
    user_id: str
    page_id: Optional[str]
    current_page_id: Optional[str]
    
    # LangGraph enhancements
    tool_results: Dict[str, Any]
    executed_tools: List[str]
    pending_tools: List[str]
    error_state: Optional[Dict[str, str]]
    confidence_score: float
    processing_stage: str
    
    # Frontend response preparation
    frontend_response: Optional[Dict[str, Any]]
    
    # Database session context
    db_session_id: str
    session_metadata: Dict[str, Any]