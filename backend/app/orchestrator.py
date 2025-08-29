"""
ENHANCED ORCHESTRATOR - LangGraph Integration
Maintains WebSocket handling but replaces AgentExecutor with LangGraph StateGraph
Preserves exact frontend JSON format while adding reliability and session management
"""

import os
import logging
import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from pydantic import BaseModel

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_anthropic import ChatAnthropic
from app.utils.retry_helper import retry_with_backoff
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage

# Existing imports
from app.db import get_db, async_session_maker
from app.models_db import User, ChatMessage, Resume, Document, Page
from app.resume import ResumeData, PersonalInfo, fix_resume_data_structure
from app.orchestrator_tools import create_all_tools
from langchain_core.runnables import RunnablePassthrough
from typing import Any
from app.state_aware_tools import StateAwareToolNode, state_manager


# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

router = APIRouter()

# ============================================================================
# 1. CONFIGURATION & CONSTANTS
# ============================================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ============================================================================
# 2. ENHANCED STATE SCHEMA (NEW)
# ============================================================================

class WebSocketState(TypedDict):
    """Enhanced state schema for LangGraph - preserves all existing functionality"""
    
    # Core conversation (existing functionality)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Your existing WebSocket context
    user_id: str
    page_id: Optional[str]
    current_page_id: Optional[str]
    
    # LangGraph enhancements for reliability
    tool_results: Dict[str, Any]
    executed_tools: List[str]
    pending_tools: List[str]
    error_state: Optional[Dict[str, str]]
    confidence_score: float
    processing_stage: str
    
    # Frontend response preparation (maintains exact format)
    frontend_response: Optional[Dict[str, Any]]
    
    # Database session context for shared sessions
    db_session_id: str
    session_metadata: Dict[str, Any]

# ============================================================================
# 3. HELPER FUNCTIONS FOR PROGRESS UPDATES
# ============================================================================

def get_node_start_message(node_name: str) -> str:
    """Generate user-friendly messages when a node starts executing"""
    
    node_start_messages = {
        "conversation": "Analyzing your request with Claude AI...",
        "tool_execution": "Preparing to execute tools...",
        "data_persistence": "Getting ready to save data...",
        "response_formatting": "Preparing your response..."
    }
    
    return node_start_messages.get(node_name, f"Starting {node_name.replace('_', ' ')}...")

def get_node_progress_message(node_name: str, node_output: Dict[str, Any]) -> str:
    """Generate user-friendly progress messages based on node execution"""
    
    # Extract context from node output
    processing_stage = node_output.get("processing_stage", "")
    pending_tools = node_output.get("pending_tools", [])
    executed_tools = node_output.get("executed_tools", [])
    
    # Node-specific messages
    if node_name == "conversation":
        if pending_tools:
            tools_str = ", ".join(pending_tools[:2])  # Show first 2 tools
            if len(pending_tools) > 2:
                tools_str += f" and {len(pending_tools) - 2} more"
            return f"Planning to use: {tools_str}"
        return "Understanding your request and analyzing context"
    
    elif node_name == "tool_execution":
        if executed_tools:
            tool_name = executed_tools[-1] if executed_tools else "tools"
            # Map tool names to user-friendly descriptions
            tool_messages = {
                "refine_cv_for_role": "Tailoring your CV for the specific role",
                "generate_cover_letter": "Creating a personalized cover letter",
                "search_jobs": "Searching for job opportunities",
                "update_resume": "Updating your resume information",
                "analyze_job_fit": "Analyzing job compatibility with your profile",
                "browser_navigate": "Fetching job posting details",
                "send_email": "Preparing email draft",
                "get_job_details": "Retrieving detailed job information"
            }
            return tool_messages.get(tool_name, f"Executing {tool_name}")
        return "Running requested operations"
    
    elif node_name == "data_persistence":
        return "Saving your data securely to the database"
    
    elif node_name == "response_formatting":
        return "Formatting and preparing final response"
    
    # Default message if node not recognized
    return f"Processing {node_name.replace('_', ' ')}"

# ============================================================================
# 4. LANGGRAPH NODES (NEW)
# ============================================================================

async def conversation_node(state: WebSocketState) -> WebSocketState:
    """
    Handles LLM conversation logic - replaces master_agent functionality
    Uses your existing master_agent logic but in node format
    """
    from app.master_agent import build_user_context_for_agent, create_enhanced_system_prompt
    from app.orchestrator_tools import create_all_tools
    
    try:
        log.info(f"Processing conversation for user {state['user_id']}")
        
        # Get user and context (using existing logic)
        user = await get_user_by_id(state["user_id"])
        db_session = await get_shared_session_from_state(state)
        
        # Build user context (existing function from master_agent)
        user_context = build_user_context_for_agent(
            user=user,
            resume_data=await get_resume_data_for_user(user.id, db_session),
            documents_count=await get_documents_count_for_user(user.id, db_session)
        )
        
        # Create tools (your existing function)
        tools = await create_all_tools(user, db_session)
        
        # LLM setup (existing logic from master_agent)
        llm = ChatAnthropic(
            model="claude-3-7-sonnet-20250219", 
            temperature=0.7,
            max_tokens=4096,
            timeout=60
        )
        
        # Bind tools to model
        model_with_tools = llm.bind_tools(tools)
        
        # Generate response using your existing system prompt logic
        system_prompt = create_enhanced_system_prompt(user.name, user_context)
        
        # Create messages with system context
        conversation_messages = [
            {"role": "system", "content": system_prompt}
        ] + [msg for msg in state["messages"]]
        
        # Generate response with retry logic for overload errors
        try:
            response = await retry_with_backoff(
                model_with_tools.ainvoke,
                conversation_messages,
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=2.0
            )
        except Exception as e:
            log.error(f"Failed to generate response after retries: {e}")
            # Return a friendly error message to the user
            return {
                "error_state": {
                    "type": "overload_error" if "high traffic" in str(e) else "conversation_error",
                    "message": str(e) if "high traffic" in str(e) else "Failed to process conversation",
                    "details": str(e)
                },
                "processing_stage": "conversation_failed",
                "confidence_score": 0.0
            }
        
        # Calculate confidence score
        confidence = calculate_confidence_score(response)
        
        # Extract tool calls if any
        tool_calls = extract_tool_calls_from_response(response)
        
        return {
            "messages": [response],
            "confidence_score": confidence,
            "pending_tools": list(tool_calls.keys()) if tool_calls else [],
            "tool_results": tool_calls if tool_calls else {},
            "processing_stage": "conversation_complete",
            "error_state": None
        }
        
    except Exception as e:
        log.error(f"Error in conversation_node: {e}", exc_info=True)
        return {
            "error_state": {
                "type": "conversation_error",
                "message": "Failed to process conversation",
                "details": str(e)
            },
            "processing_stage": "conversation_failed",
            "confidence_score": 0.0
        }

async def tool_execution_node(state: WebSocketState) -> WebSocketState:
    """
    Executes tools with state awareness
    """
    try:
        log.info(f"Executing tools: {state.get('pending_tools', [])}")
        
        # Set state in manager for tools to access
        state_manager.set_state(state)
        
        # Get user and shared session
        user = await get_user_by_id(state["user_id"])
        db_session = await get_shared_session_from_state(state)
        
        # Create tools (they can now access state via state_manager)
        tools = await create_all_tools(user, db_session)
        
        # Create StateAwareToolNode with state provider
        tool_node = StateAwareToolNode(
            tools, 
            state_provider=lambda: state
        )
        
        # Set the current state
        tool_node.set_state(state)
        
        # Execute tools
        tool_execution_input = {
            "messages": state["messages"]
        }
        
        tool_results = await tool_node.ainvoke(tool_execution_input)
        
        # Extract executed tool names
        executed_tools = []
        for msg in tool_results.get("messages", []):
            if isinstance(msg, ToolMessage):
                executed_tools.append(msg.name)
                log.info(f"Tool {msg.name} result preview: {msg.content[:200]}...")
        
        return {
            "messages": tool_results.get("messages", []),
            "executed_tools": state.get("executed_tools", []) + executed_tools,
            "tool_results": tool_results,
            "pending_tools": [],
            "processing_stage": "tools_executed",
            "error_state": None
        }
        
    except Exception as e:
        log.error(f"Error in tool_execution_node: {e}", exc_info=True)
        return {
            "error_state": {
                "type": "tool_execution_error",
                "message": "Failed to execute tools",
                "details": str(e)
            },
            "processing_stage": "tool_execution_failed"
        }
    finally:
        # Clear state after execution
        state_manager.clear_state()

async def data_persistence_node(state: WebSocketState) -> WebSocketState:
    """
    Handles all database operations with shared session
    Uses your existing DatabaseService logic
    """
    try:
        log.info(f"Persisting data for user {state['user_id']}")
        
        # Get shared database session
        db_session = await get_shared_session_from_state(state)
        
        # Skip saving conversation messages here - they're saved after formatting
        # await save_conversation_messages(state, db_session)
        
        # Save tool results (resume updates, cover letters, etc.)
        if state.get("tool_results"):
            await save_tool_results_to_database(state, db_session)
        
        # Update page information if needed (existing logic)
        if state.get("page_id"):
            await update_page_metadata(state, db_session)
        
        # Commit all changes in single transaction
        await db_session.commit()
        
        log.info(f"Data persistence successful for user {state['user_id']}")
        
        return {
            "processing_stage": "data_persisted",
            "error_state": None
        }
        
    except Exception as e:
        log.error(f"Error in data_persistence_node: {e}", exc_info=True)
        
        # Rollback on error
        db_session = await get_shared_session_from_state(state)
        await db_session.rollback()
        
        return {
            "error_state": {
                "type": "database_error",
                "message": "Failed to save data", 
                "details": str(e)
            },
            "processing_stage": "data_persistence_failed"
        }

async def response_formatting_node(state: WebSocketState) -> WebSocketState:
    """
    Formats response for frontend - PRESERVES YOUR EXACT JSON FORMAT
    """
    try:
        log.info(f"Formatting response for user {state['user_id']}")
        
        # Get ALL messages, including tool results
        all_messages = state.get("messages", [])
        
        # Find the last message with actual content (could be AI or Tool message)
        final_message = None
        for msg in reversed(all_messages):
            if hasattr(msg, 'content') and msg.content:
                # Check if this is a tool message or AI message with content
                if isinstance(msg, (AIMessage, ToolMessage)) or (hasattr(msg, 'name') and msg.name):
                    final_message = msg
                    break
        
        if not final_message:
            formatted_content = "I'm sorry, I couldn't process your request. Please try again."
        else:
            # Log what we're formatting
            log.info(f"Formatting message type: {type(final_message).__name__}")
            
            # Handle Anthropic's content format (can be a list for tool calls)
            message_content = final_message.content
            if isinstance(message_content, list):
                # For tool calls, extract the text or convert to string
                if message_content and isinstance(message_content[0], dict):
                    if 'text' in message_content[0]:
                        message_content = message_content[0]['text']
                    else:
                        # For pure tool calls without text, use a default message
                        message_content = "Processing your request..."
                else:
                    message_content = str(message_content)
            
            log.info(f"Content preview: {message_content[:200] if message_content else 'No content'}...")
            
            # Process the content
            formatted_content = process_download_triggers(message_content)
            formatted_content = process_special_markers(formatted_content)
        
        # Create response in YOUR EXACT EXISTING FORMAT
        frontend_response = {
            "type": "message",
            "message": formatted_content,
        }
        
        # Add optional fields
        if state.get("page_id"):
            frontend_response["page_id"] = state["page_id"]
        
        log.info(f"Response formatted successfully with {len(formatted_content)} chars")
        
        return {
            "frontend_response": frontend_response,
            "processing_stage": "response_formatted"
        }
        
    except Exception as e:
        log.error(f"Error in response_formatting_node: {e}", exc_info=True)
        return {
            "frontend_response": {
                "type": "error",
                "message": "Sorry, I encountered an error while formatting the response. Please try again."
            },
            "processing_stage": "response_formatting_failed"
        }

def route_next_action(state: WebSocketState) -> str:
    """
    Determines next node based on conversation state
    Implements routing logic for the LangGraph flow
    """
    # Check for errors first
    if state.get("error_state"):
        return "response_formatting"
    
    # Check current processing stage
    current_stage = state.get("processing_stage", "")
    
    # If we just completed conversation and have pending tools
    if current_stage == "conversation_complete" and state.get("pending_tools"):
        return "tool_execution"
    
    # If we just executed tools, persist data
    elif current_stage == "tools_executed":
        return "data_persistence"
    
    # If conversation complete but no tools, go straight to persistence
    elif current_stage == "conversation_complete":
        return "data_persistence"
    
    # After data persistence, format response
    elif current_stage == "data_persisted":
        return "response_formatting"
    
    # Default to response formatting
    else:
        return "response_formatting"

# ============================================================================
# 4. LANGGRAPH SETUP (NEW)
# ============================================================================

async def create_websocket_langgraph_app(user: User, db: AsyncSession):
    """
    Creates LangGraph StateGraph replacing AgentExecutor
    Implements the three-node architecture you requested
    """
    try:
        log.info(f"Creating LangGraph app for user {user.id}")
        
        # Create StateGraph with enhanced state
        workflow = StateGraph(WebSocketState)
        
        # Add your three core nodes + response formatting
        workflow.add_node("conversation", conversation_node)
        workflow.add_node("tool_execution", tool_execution_node)
        workflow.add_node("data_persistence", data_persistence_node) 
        workflow.add_node("response_formatting", response_formatting_node)
        
        # Define the flow according to your requirements
        workflow.add_edge(START, "conversation")
        
        # Add conditional routing based on conversation output
        workflow.add_conditional_edges(
            "conversation",
            route_next_action,
            {
                "tool_execution": "tool_execution",
                "data_persistence": "data_persistence",
                "response_formatting": "response_formatting"
            }
        )
        
        # Tools -> Data Persistence -> Response
        workflow.add_edge("tool_execution", "data_persistence")
        workflow.add_edge("data_persistence", "response_formatting")
        workflow.add_edge("response_formatting", END)
        
        # Set up checkpointer for session persistence
        checkpointer = None
        try:
            if os.getenv("DATABASE_URL"):
                from psycopg_pool import AsyncConnectionPool
                
                connection_kwargs = {
                    "autocommit": True,
                    "prepare_threshold": 0,
                }
                
                pool = AsyncConnectionPool(
                    conninfo=os.getenv("DATABASE_URL"),
                    max_size=10,
                    kwargs=connection_kwargs
                )
                
                checkpointer = AsyncPostgresSaver(pool)
                await checkpointer.setup()
                log.info("PostgreSQL checkpointer configured")
        except Exception as e:
            log.warning(f"Could not set up PostgreSQL checkpointer: {e}")
        
        # Rest of your existing function stays the same
        compiled_app = workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=[],
            interrupt_after=[]
        )
        return compiled_app
        
    except Exception as e:
        log.error(f"Error creating LangGraph app: {e}", exc_info=True)
        raise

# ============================================================================
# 5. WEBSOCKET HANDLER (MODIFIED)
# ============================================================================

@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """
    Enhanced WebSocket handler using LangGraph instead of AgentExecutor
    Preserves all existing functionality while adding reliability
    Updated to 2025 best practices: Accept first, then authenticate
    """
    log.info(f"WebSocket connection attempt from {websocket.client}")
    
    # Accept the WebSocket connection first (2025 pattern)
    await websocket.accept()
    log.info("WebSocket connection accepted")
    
    # Now manually authenticate after accepting
    try:
        # Get token from query parameters
        token = websocket.query_params.get("token")
        
        if not token:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication required - no token provided"
            })
            await websocket.close(code=1008)  # Policy violation
            return
        
        # Import authentication functions
        from app.dependencies import get_current_active_user_ws
        from fastapi import Query
        
        # Manually validate the token (simulating what Depends would do)
        try:
            # Check if it's an extension token
            if token.startswith("jhb_"):
                from app.extension_tokens import hash_token, ExtensionToken
                
                token_hash = hash_token(token)
                result = await db.execute(
                    select(ExtensionToken).where(
                        ExtensionToken.token_hash == token_hash,
                        ExtensionToken.is_active == True
                    )
                )
                ext_token = result.scalar_one_or_none()
                
                if not ext_token:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid extension token"
                    })
                    await websocket.close(code=1008)
                    return
                
                # Check expiration
                if ext_token.expires_at and ext_token.expires_at < datetime.utcnow():
                    await websocket.send_json({
                        "type": "error",
                        "message": "Extension token has expired"
                    })
                    await websocket.close(code=1008)
                    return
                
                # Update last used
                ext_token.last_used = datetime.utcnow()
                await db.commit()
                
                # Get the user
                from app.models_db import User
                result = await db.execute(select(User).where(User.external_id == ext_token.user_id))
                user = result.scalar_one_or_none()
                
                if not user:
                    await websocket.send_json({
                        "type": "error",
                        "message": "User not found for extension token"
                    })
                    await websocket.close(code=1008)
                    return
            elif token.startswith("clerk_"):
                # Handle Clerk session ID from extension
                from app.clerk import verify_session_token, ClerkUser
                
                # Extract session ID from token
                session_id = token.replace("clerk_", "")
                
                # Verify the session with Clerk
                clerk_user: ClerkUser = await verify_session_token(session_id)
                if not clerk_user:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid or expired session"
                    })
                    await websocket.close(code=1008)
                    return
            else:
                # First check if it's a session bridge token (created by our extension API)
                try:
                    import jwt as pyjwt
                    import os
                    
                    # Try to decode as session bridge token
                    decoded = pyjwt.decode(
                        token,
                        os.getenv("CLERK_SECRET_KEY", "fallback-secret"),
                        algorithms=["HS256"]
                    )
                    
                    # Check if it's a session bridge token
                    if decoded.get("type") == "session_bridge":
                        from app.clerk import ClerkUser
                        clerk_user = ClerkUser(
                            sub=decoded["userId"],
                            email=decoded.get("email"),
                            first_name=decoded.get("firstName"),
                            last_name=decoded.get("lastName"),
                            picture=decoded.get("imageUrl")
                        )
                        log.info(f"Authenticated with session bridge token for user {clerk_user.sub}")
                    else:
                        # Not a session bridge token, try regular Clerk token
                        raise ValueError("Not a session bridge token")
                        
                except (pyjwt.InvalidTokenError, ValueError, KeyError) as e:
                    # Not a valid session bridge token, try regular Clerk token
                    from app.clerk import verify_token, ClerkUser
                    
                    clerk_user: ClerkUser = await verify_token(token)
                    if not clerk_user:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid authentication token"
                        })
                        await websocket.close(code=1008)
                        return
                
                # Get or create user
                from app.models_db import User
                result = await db.execute(select(User).where(User.external_id == clerk_user.sub))
                user = result.scalar_one_or_none()
                
                if user is None:
                    log.info(f"WS Auth: User with external_id {clerk_user.sub} not found. Creating new user.")
                    user = User(
                        external_id=clerk_user.sub,
                        email=clerk_user.email,
                        name=f"{clerk_user.first_name or ''} {clerk_user.last_name or ''}".strip() or "New User",
                        first_name=clerk_user.first_name,
                        last_name=clerk_user.last_name,
                        picture=clerk_user.picture,
                        active=True
                    )
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)
            
            # Check if user is active
            if not user.active:
                await websocket.send_json({
                    "type": "error",
                    "message": "User account is inactive"
                })
                await websocket.close(code=1008)
                return
            
            log.info(f"WS Auth: Successfully authenticated user: {user.id}")
            
        except Exception as auth_error:
            log.error(f"WebSocket authentication error: {auth_error}")
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close(code=1008)
            return
    except Exception as e:
        log.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011)  # Server error
        return
    
    try:
        # Initialize LangGraph app (replaces AgentExecutor creation)
        langgraph_app = await create_websocket_langgraph_app(user, db)
        
        # Session configuration for LangGraph persistence
        session_config = {
            "configurable": {
                "thread_id": f"user_{user.id}_{datetime.now().isoformat()}",
                "user_id": user.id,
                "db_session_id": str(uuid.uuid4())
            }
        }
        
        # Session state tracking (preserve existing logic)
        current_page_id = None
        is_processing = False
        
        log.info(f"WebSocket session initialized for user: {user.id}")
        
        # Main message loop (preserve existing structure)
        while True:
            try:
                log.info(f"Waiting for message from user: {user.id}")
                data = await websocket.receive_text()
                log.info(f"Received data from user {user.id}: {data[:200] if data else 'Empty'}")
                # Parse message (existing logic)
                if data.startswith('{'):
                    message_data = json.loads(data)
                    message_type = message_data.get("type", "message")
                else:
                    # Legacy text message support
                    message_data = {"type": "message", "content": data}
                    message_type = "message"
                
                # Route to appropriate handler
                if message_type == "message":
                    await handle_message_langgraph(
                        message_data, langgraph_app, session_config, 
                        websocket, user, db, is_processing
                    )
                    
                elif message_type == "switch_page":
                    current_page_id = await handle_page_switch_langgraph(
                        message_data, user, db, websocket, current_page_id
                    )
                    
                elif message_type == "regenerate":
                    await handle_regenerate_langgraph(
                        message_data, langgraph_app, session_config, websocket, user, db
                    )
                    
                elif message_type == "stop_generation":
                    is_processing = False
                    log.info("Generation stopped by user request")
                    
                elif message_type == "clear_context":
                    # Clear context by creating new session config
                    session_config["configurable"]["thread_id"] = f"user_{user.id}_{datetime.now().isoformat()}"
                    log.info("Chat context cleared")
                    
                elif message_type == "extract_screenshot":
                    await handle_screenshot_extraction(
                        message_data, websocket, user, db
                    )
                    
                else:
                    log.warning(f"Unknown message type: {message_type}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                
            except json.JSONDecodeError as e:
                log.error(f"Invalid JSON received: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format"
                })
            
            except Exception as e:
                log.error(f"Error processing message: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error", 
                    "message": "Error processing message"
                })
    
    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected for user {user.id}")
    
    except Exception as e:
        log.error(f"WebSocket error for user {user.id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}"
            })
        except:
            pass  # WebSocket might be closed

# ============================================================================
# 6. MESSAGE HANDLERS (MODIFIED)
# ============================================================================

async def load_chat_history(user_id: str, page_id: str, db: AsyncSession, limit: int = 50) -> List:
    """Load chat history for a specific page"""
    from sqlalchemy import and_, select
    from langchain_core.messages import HumanMessage, AIMessage
    
    result = await db.execute(
        select(ChatMessage)
        .where(
            and_(
                ChatMessage.user_id == user_id,
                ChatMessage.page_id == page_id,
                ChatMessage.deleted_at.is_(None)
            )
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    
    messages = result.scalars().all()
    
    # Convert to LangChain message format, filtering out empty messages
    chat_history = []
    for msg in messages:
        # Skip messages with empty or null content
        if not msg.message or msg.message.strip() == "":
            log.warning(f"Skipping empty message {msg.id} for user {user_id}")
            continue
            
        # Clean the message content
        content = msg.message.strip()
        
        # Handle special message formats (e.g., file attachments)
        if content.startswith("File Attached:"):
            # Extract the actual message content after the file attachment notice
            parts = content.split("\n\nMessage:", 1)
            if len(parts) > 1 and parts[1].strip():
                content = parts[1].strip()
            else:
                # If there's no message content with the file, skip this message
                log.info(f"Skipping file attachment message without text content: {msg.id}")
                continue
        
        if msg.is_user_message:
            chat_history.append(HumanMessage(content=content))
        else:
            chat_history.append(AIMessage(content=content))
    
    return chat_history

async def handle_message_langgraph(
    message_data: Dict, 
    langgraph_app, 
    session_config: Dict,
    websocket: WebSocket,
    user: User,
    db: AsyncSession,
    is_processing: bool
) -> None:
    """
    Handle regular messages through LangGraph
    Preserves your existing message handling logic
    """
    content = message_data.get("content", "").strip()
    page_id = message_data.get("page_id")
    
    if not content:
        await websocket.send_json({
            "type": "error", 
            "message": "Empty message received"
        })
        return
    
    # Prevent concurrent processing (existing logic)
    if is_processing:
        log.warning("Already processing a message, ignoring new one")
        return
    
    is_processing = True
    
    try:
        # Check if this is an extension temporary page
        is_extension_page = page_id and page_id.startswith("extension_temp_")
        
        # Handle new page creation (existing logic) - skip for extension pages
        if not page_id:
            title = content[:50].strip() or "New Conversation"
            page_id = await create_new_page(user.id, title, db)
            
            await websocket.send_json({
                "type": "page_created",
                "message": "",
                "page_id": page_id,
                "title": title
            })
        
        # Save the user's message immediately to prevent loss (skip for extension pages)
        if not is_extension_page:
            user_message = ChatMessage(
                id=str(uuid.uuid4()),
                user_id=user.id,
                page_id=page_id,
                message=content,
                is_user_message=True
            )
            db.add(user_message)
            await db.commit()
            log.info(f"Saved user message immediately for page {page_id}")
        else:
            log.info(f"Skipping message save for extension page {page_id}")
        
        # Load chat history for context (skip for extension pages)
        if not is_extension_page:
            chat_history = await load_chat_history(user.id, page_id, db, limit=20)
        else:
            chat_history = []  # No history for extension pages
        
        # Add current message to history (it should now be in the loaded history)
        # But add it anyway in case the load didn't include it yet
        if not chat_history or chat_history[-1].content != content:
            chat_history.append(HumanMessage(content=content))
        
        # Prepare LangGraph input state with full chat history
        langgraph_input = {
            "messages": chat_history,
            "user_id": user.id,
            "page_id": page_id,
            "current_page_id": page_id,
            "db_session_id": session_config["configurable"]["user_id"],
            "tool_results": {},
            "executed_tools": [],
            "pending_tools": [],
            "confidence_score": 1.0,
            "processing_stage": "initialized",
            "session_metadata": {
                "timestamp": datetime.now().isoformat(),
                "user_agent": "websocket"
            }
        }
        
        # Execute through LangGraph (replaces agent.ainvoke)
        try:
            # Send initial progress update
            await websocket.send_json({
                "type": "progress_update",
                "node": "initialization",
                "message": "Initializing AI assistant and loading your context...",
                "stage": "starting"
            })
            
            # Process through nodes - send manual progress updates
            await websocket.send_json({
                "type": "progress_update", 
                "node": "conversation",
                "message": "Understanding your request and analyzing context...",
                "stage": "conversation_started"
            })
            
            async for chunk in langgraph_app.astream(langgraph_input, config=session_config):
                # Process each node's output
                for node_name, node_output in chunk.items():
                    log.info(f"Node {node_name} completed")
                    
                    # Send progress update AFTER node completes
                    progress_message = get_node_progress_message(node_name, node_output)
                    if progress_message:
                        await websocket.send_json({
                            "type": "progress_update",
                            "node": node_name,
                            "message": progress_message,
                            "stage": node_output.get("processing_stage", node_name)
                        })
                    
                    # Send initial message for next node if applicable
                    if node_name == "conversation" and node_output.get("pending_tools"):
                        await websocket.send_json({
                            "type": "progress_update",
                            "node": "tool_execution",
                            "message": "Preparing to execute selected tools...",
                            "stage": "tool_execution_started"
                        })
                    elif node_name == "tool_execution":
                        await websocket.send_json({
                            "type": "progress_update",
                            "node": "data_persistence",
                            "message": "Saving your data securely...",
                            "stage": "data_persistence_started"
                        })
                    elif node_name == "data_persistence":
                        await websocket.send_json({
                            "type": "progress_update",
                            "node": "response_formatting",
                            "message": "Formatting your response...",
                            "stage": "response_formatting_started"
                        })
                    
                    # Send final response when response_formatting completes
                    if node_name == "response_formatting" and node_output.get("frontend_response"):
                        frontend_response = node_output["frontend_response"]
                        await websocket.send_json(frontend_response)
                        log.info(f"Response sent to user {user.id}")
                        
                        # Send complete message for extension pages to signal end of generation
                        if is_extension_page:
                            await websocket.send_json({
                                "type": "complete",
                                "message": "Generation complete"
                            })
                            log.info(f"Sent complete signal for extension page {page_id}")
                        
                        # Save the final assistant response to the database (skip for extension pages)
                        if frontend_response.get("type") == "message" and frontend_response.get("message") and not is_extension_page:
                            try:
                                # Check if this exact message already exists to avoid duplicates
                                existing = await db.execute(
                                    select(ChatMessage)
                                    .where(
                                        and_(
                                            ChatMessage.user_id == user.id,
                                            ChatMessage.page_id == page_id,
                                            ChatMessage.message == frontend_response["message"],
                                            ChatMessage.is_user_message == False,
                                            ChatMessage.deleted_at.is_(None)
                                        )
                                    )
                                    .limit(1)
                                )
                                
                                if not existing.scalar_one_or_none():
                                    assistant_message = ChatMessage(
                                        id=str(uuid.uuid4()),
                                        user_id=user.id,
                                        page_id=page_id,
                                        message=frontend_response["message"],
                                        is_user_message=False
                                    )
                                    db.add(assistant_message)
                                    await db.commit()
                                    log.info(f"Saved assistant message for page {page_id}")
                                else:
                                    log.info(f"Assistant message already exists, skipping duplicate save")
                            except Exception as save_error:
                                log.error(f"Failed to save assistant message: {save_error}")
                                if db.is_active:
                                    await db.rollback()
                        
        except Exception as e:
            log.error(f"LangGraph execution error: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": "I encountered an issue processing your request. Please try again."
            })
            
    except Exception as e:
        log.error(f"Error in handle_message_langgraph: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": "Failed to process message"
        })
    
    finally:
        is_processing = False

async def handle_page_switch_langgraph(
    message_data: Dict,
    user: User,
    db: AsyncSession, 
    websocket: WebSocket,
    current_page_id: Optional[str]
) -> Optional[str]:
    """
    Handle page switching with LangGraph context
    Preserves your existing page switching logic
    """
    new_page_id = message_data.get("page_id")
    
    try:
        if new_page_id != current_page_id:
            # Load page history (existing logic from DatabaseService)
            history = await load_page_history(user.id, new_page_id, db)
            
            # Update last opened timestamp (existing logic)
            if new_page_id:
                await db.execute(
                    update(Page)
                    .where(Page.id == new_page_id)
                    .values(last_opened_at=func.now())
                )
                await db.commit()
            
            log.info(f"Switched to page {new_page_id}, loaded {len(history)} messages")
            return new_page_id
            
    except Exception as e:
        log.error(f"Error in page switch: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": "Failed to switch page"
        })
    
    return current_page_id

async def handle_regenerate_langgraph(
    message_data: Dict,
    langgraph_app,
    session_config: Dict,
    websocket: WebSocket,
    user: User,
    db: AsyncSession
) -> None:
    """
    Handle message regeneration through LangGraph
    """
    regenerate_content = message_data.get("content", "")
    page_id = message_data.get("page_id")
    
    if not regenerate_content:
        await websocket.send_json({
            "type": "error",
            "message": "No content provided for regeneration"
        })
        return
    
    try:
        # First, delete the last assistant message to avoid duplicates
        if page_id:
            try:
                # Find and delete the last assistant message for this page
                from sqlalchemy import and_, select, delete
                
                # Get the last assistant message
                last_assistant_msg_query = await db.execute(
                    select(ChatMessage)
                    .where(
                        and_(
                            ChatMessage.user_id == user.id,
                            ChatMessage.page_id == page_id,
                            ChatMessage.is_user_message == False,
                            ChatMessage.deleted_at.is_(None)
                        )
                    )
                    .order_by(ChatMessage.created_at.desc())
                    .limit(1)
                )
                
                last_assistant_msg = last_assistant_msg_query.scalar_one_or_none()
                
                if last_assistant_msg:
                    # Soft delete by setting deleted_at timestamp
                    last_assistant_msg.deleted_at = datetime.now()
                    await db.commit()
                    log.info(f"Soft deleted previous assistant message {last_assistant_msg.id} before regeneration")
                    
            except Exception as delete_error:
                log.error(f"Failed to delete previous assistant message: {delete_error}")
                if db.is_active:
                    await db.rollback()
        
        # Prepare regeneration input
        regeneration_input = {
            "messages": [HumanMessage(content=regenerate_content)],
            "user_id": session_config["configurable"]["user_id"],
            "page_id": page_id,
            "processing_stage": "regeneration",
            "tool_results": {},
            "executed_tools": [],
            "confidence_score": 1.0
        }
        
        # Send initial progress update for regeneration
        await websocket.send_json({
            "type": "progress_update",
            "node": "initialization",
            "message": "Regenerating response with different approach...",
            "stage": "starting"
        })
        
        # Process regeneration through LangGraph with progress updates
        async for chunk in langgraph_app.astream(regeneration_input, config=session_config):
            for node_name, node_output in chunk.items():
                log.info(f"Regeneration - Node {node_name} completed")
                
                # Send progress update for each node
                progress_message = get_node_progress_message(node_name, node_output)
                if progress_message:
                    await websocket.send_json({
                        "type": "progress_update",
                        "node": node_name,
                        "message": f"Regenerating: {progress_message}",
                        "stage": node_output.get("processing_stage", node_name)
                    })
                
                # Send final response when response_formatting completes
                if node_name == "response_formatting" and node_output.get("frontend_response"):
                    frontend_response = node_output["frontend_response"]
                    await websocket.send_json(frontend_response)
                    
                    # Save the regenerated assistant response to the database (skip for extension pages)
                    is_extension_page = page_id and page_id.startswith("extension_temp_")
                    if frontend_response.get("type") == "message" and frontend_response.get("message") and not is_extension_page:
                        try:
                            assistant_message = ChatMessage(
                                id=str(uuid.uuid4()),
                                user_id=user.id,
                                page_id=page_id,
                                message=frontend_response["message"],
                                is_user_message=False
                            )
                            db.add(assistant_message)
                            await db.commit()
                            log.info(f"Saved regenerated assistant message for page {page_id}")
                        except Exception as save_error:
                            log.error(f"Failed to save regenerated assistant message: {save_error}")
                            if db.is_active:
                                await db.rollback()
                    
        log.info("Regeneration completed successfully")
        
    except Exception as e:
        log.error(f"Error during regeneration: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": "Failed to regenerate response"
        })

# ============================================================================
# 7. UTILITY FUNCTIONS (EXISTING + NEW)
# ============================================================================

# Keep all your existing utility functions and add new LangGraph helpers

async def get_user_by_id(user_id: str) -> User:
    """Get user from database by ID"""
    async with async_session_maker() as session:
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            await session.commit()  # Ensure transaction is committed
            return user
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()  # Explicitly close the session

async def get_shared_session_from_state(state: WebSocketState) -> AsyncSession:
    """Get shared database session from LangGraph state"""
    # Implementation for shared session management
    # This will be enhanced when we modify orchestrator_tools.py
    return await async_session_maker().__anext__()

def calculate_confidence_score(response: AIMessage) -> float:
    """Calculate confidence score for LLM response"""
    # Simple confidence calculation based on response characteristics
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return 0.9  # High confidence for tool calls
    elif len(response.content) > 100:
        return 0.8  # Medium-high confidence for detailed responses
    elif len(response.content) > 20:
        return 0.6  # Medium confidence
    else:
        return 0.4  # Lower confidence for short responses

def extract_tool_calls_from_response(response: AIMessage) -> Dict[str, Any]:
    """Extract tool calls from LLM response"""
    tool_calls = {}
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for i, tool_call in enumerate(response.tool_calls):
            tool_calls[f"{tool_call['name']}_{i}"] = tool_call
    return tool_calls

def extract_executed_tool_names(tool_results: Dict) -> List[str]:
    """Extract names of executed tools from ToolNode results"""
    executed = []
    if "messages" in tool_results:
        for msg in tool_results["messages"]:
            if hasattr(msg, 'name') and msg.name:
                executed.append(msg.name)
    return executed

def merge_tool_results(existing: Dict[str, Any], new: Dict) -> Dict[str, Any]:
    """Merge tool execution results"""
    merged = existing.copy()
    if "messages" in new:
        merged["latest_execution"] = new["messages"]
    return merged

def get_final_ai_message(messages: List[BaseMessage]) -> Optional[AIMessage]:
    """Get the last AI message from conversation"""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return msg
    return None

def process_download_triggers(content: str) -> str:
    """
    Process download triggers - PRESERVES YOUR EXISTING LOGIC
    This maintains compatibility with your frontend download handling
    """
    # The triggers should be preserved in the content for the frontend to process
    # Don't remove or modify them - the frontend MessageContent component handles them
    # Just ensure they're properly formatted
    
    # Log if triggers are present for debugging
    if "[DOWNLOADABLE_" in content:
        log.info(f"Download trigger found in content: {content[:200]}")
    
    return content

def process_special_markers(content: str) -> str:
    """Process other special markers in responses"""
    # Handle interview flashcards, document analysis triggers, etc.
    return content

def get_user_friendly_error_message(error_info: Dict[str, str]) -> str:
    """Convert technical errors to user-friendly messages"""
    error_type = error_info.get("type", "unknown")
    
    if error_type == "conversation_error":
        return "I'm having trouble understanding your request. Please try rephrasing it."
    elif error_type == "tool_execution_error":
        return "I encountered an issue while processing your request. Please try again."
    elif error_type == "database_error":
        return "I'm having trouble saving your information right now. Please try again."
    else:
        return "Something went wrong. Please try again or contact support if the issue persists."

# Preserve your existing utility functions
async def create_new_page(user_id: str, title: str, db: AsyncSession) -> str:
    """Create a new conversation page (existing logic)"""
    new_page = Page(user_id=user_id, title=title)
    db.add(new_page)
    await db.flush()
    page_id = new_page.id
    await db.commit()
    return page_id

async def load_page_history(user_id: str, page_id: Optional[str], db: AsyncSession) -> List[Dict]:
    """Load chat history for a page (existing logic)"""
    query = (
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .where(ChatMessage.page_id == page_id)
        .where(ChatMessage.deleted_at.is_(None))  # Filter out soft-deleted messages
        .order_by(ChatMessage.created_at)
    )
    
    result = await db.execute(query)
    messages = []
    
    for record in result.scalars().all():
        try:
            content = json.loads(record.message) if isinstance(record.message, str) else record.message
        except (json.JSONDecodeError, TypeError):
            content = record.message
        
        messages.append({
            "id": record.id,
            "content": content if isinstance(content, str) else json.dumps(content),
            "is_user": record.is_user_message,
            "created_at": record.created_at
        })
    
    return messages

async def save_tool_results_to_database(state: WebSocketState, db_session: AsyncSession) -> None:
    """Save tool execution results to appropriate database tables"""
    # Implementation for saving tool results
    pass

async def update_page_metadata(state: WebSocketState, db_session: AsyncSession) -> None:
    """Update page metadata and timestamps"""
    # Implementation for page updates
    pass

async def save_conversation_messages(state: WebSocketState, db_session: AsyncSession) -> None:
    """Save conversation messages to database using existing logic"""
    try:
        user_id = state["user_id"]
        page_id = state.get("page_id")
        
        if not page_id:
            log.warning(f"No page_id provided for user {user_id}, skipping message save")
            return
        
        # Get existing message IDs to avoid duplicates
        existing_messages = await db_session.execute(
            select(ChatMessage.message)
            .where(
                and_(
                    ChatMessage.user_id == user_id,
                    ChatMessage.page_id == page_id,
                    ChatMessage.deleted_at.is_(None)
                )
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(100)
        )
        existing_contents = {msg for (msg,) in existing_messages}
        
        # Get only the last few messages to save (not all history)
        messages_to_save = state["messages"][-4:] if len(state["messages"]) > 4 else state["messages"]
        
        saved_count = 0
        for message in messages_to_save:
            if isinstance(message, (HumanMessage, AIMessage)):
                # Create message record using existing logic
                message_id = str(uuid.uuid4())
                is_user_message = isinstance(message, HumanMessage)
                
                # Handle Anthropic's tool call format (content can be a list)
                message_content = message.content
                if isinstance(message_content, list):
                    # For tool calls, extract the text or convert to JSON string
                    if message_content and isinstance(message_content[0], dict):
                        # If it has a 'text' field, use that, otherwise serialize the whole thing
                        if 'text' in message_content[0]:
                            message_content = message_content[0]['text']
                        else:
                            message_content = json.dumps(message_content)
                    else:
                        message_content = str(message_content)
                
                # Skip empty messages
                if not message_content or str(message_content).strip() == "":
                    log.warning(f"Skipping empty message for user {user_id}")
                    continue
                
                # Clean the message content
                clean_content = str(message_content).strip()
                
                # Check if message already exists (avoid duplicates)
                if clean_content in existing_contents:
                    log.debug(f"Message already exists, skipping: {clean_content[:50]}...")
                    continue
                
                chat_message = ChatMessage(
                    id=message_id,
                    user_id=user_id,
                    page_id=page_id,
                    message=clean_content,
                    is_user_message=is_user_message
                )
                
                db_session.add(chat_message)
                saved_count += 1
        
        log.info(f"Saved {saved_count} new messages for user {user_id} (checked {len(messages_to_save)} messages)")
        
    except Exception as e:
        log.error(f"Error saving conversation messages: {e}")
        raise

async def save_tool_results_to_database(state: WebSocketState, db_session: AsyncSession) -> None:
    """Save tool execution results to appropriate database tables"""
    try:
        user_id = state["user_id"]
        tool_results = state.get("tool_results", {})
        executed_tools = state.get("executed_tools", [])
        
        # Handle resume updates (if any resume tools were executed)
        if any("resume" in tool.lower() or "cv" in tool.lower() for tool in executed_tools):
            await handle_resume_tool_results(user_id, tool_results, db_session)
        
        # Handle cover letter results
        if any("cover_letter" in tool.lower() for tool in executed_tools):
            await handle_cover_letter_tool_results(user_id, tool_results, db_session)
        
        # Handle profile updates
        if any("profile" in tool.lower() for tool in executed_tools):
            await handle_profile_tool_results(user_id, tool_results, db_session)
        
        log.info(f"Saved tool results for user {user_id}: {executed_tools}")
        
    except Exception as e:
        log.error(f"Error saving tool results: {e}")
        raise

async def handle_resume_tool_results(user_id: str, tool_results: Dict, db_session: AsyncSession) -> None:
    """Handle resume-specific tool results"""
    # This will be called when resume tools have been executed
    # The actual resume saving is handled by the tools themselves
    # This is for any additional metadata or logging
    log.info(f"Resume tools executed for user {user_id}")

async def handle_cover_letter_tool_results(user_id: str, tool_results: Dict, db_session: AsyncSession) -> None:
    """Handle cover letter-specific tool results"""
    # Cover letter saving is handled by the tools themselves
    # This is for any additional processing needed
    log.info(f"Cover letter tools executed for user {user_id}")

async def handle_profile_tool_results(user_id: str, tool_results: Dict, db_session: AsyncSession) -> None:
    """Handle profile update tool results"""
    # Profile updates are handled by the tools themselves
    # This is for any additional processing needed
    log.info(f"Profile tools executed for user {user_id}")

async def update_page_metadata(state: WebSocketState, db_session: AsyncSession) -> None:
    """Update page metadata and timestamps"""
    try:
        page_id = state.get("page_id")
        if not page_id:
            return
        
        # Update last activity timestamp
        await db_session.execute(
            update(Page)
            .where(Page.id == page_id)
            .values(last_opened_at=func.now())
        )
        
        log.info(f"Updated metadata for page {page_id}")
        
    except Exception as e:
        log.error(f"Error updating page metadata: {e}")
        raise

async def get_resume_data_for_user(user_id: str, db_session: AsyncSession) -> Optional[ResumeData]:
    """Get resume data for user context building"""
    try:
        result = await db_session.execute(select(Resume).where(Resume.user_id == user_id))
        db_resume = result.scalar_one_or_none()
        
        if db_resume and db_resume.data:
            fixed_data = fix_resume_data_structure(db_resume.data)
            return ResumeData(**fixed_data)
        
        return None
        
    except Exception as e:
        log.error(f"Error getting resume data for user {user_id}: {e}")
        return None

async def get_documents_count_for_user(user_id: str, db_session: AsyncSession) -> int:
    """Get document count for user context building"""
    try:
        result = await db_session.execute(
            select(func.count(Document.id)).where(Document.user_id == user_id)
        )
        count = result.scalar_one()
        return count or 0
        
    except Exception as e:
        log.error(f"Error getting document count for user {user_id}: {e}")
        return 0

# ============================================================================
# 8. SESSION MANAGEMENT HELPERS (NEW)
# ============================================================================

_active_sessions: Dict[str, AsyncSession] = {}

async def get_shared_session_from_state(state: WebSocketState) -> AsyncSession:
    """
    Get shared database session from LangGraph state
    This ensures all nodes use the same database session for transaction consistency
    """
    session_id = state.get("db_session_id")
    
    if not session_id:
        # Create new session if none exists
        session_id = str(uuid.uuid4())
        state["db_session_id"] = session_id
    
    # Check if session already exists
    if session_id in _active_sessions:
        return _active_sessions[session_id]
    
    # Create new session and store it
    session = async_session_maker()
    _active_sessions[session_id] = session
    
    return session

async def cleanup_session(session_id: str) -> None:
    """Clean up database session after use"""
    if session_id in _active_sessions:
        session = _active_sessions[session_id]
        try:
            await session.close()
        except Exception as e:
            log.error(f"Error closing session {session_id}: {e}")
        finally:
            del _active_sessions[session_id]

# ============================================================================
# 9. ERROR HANDLING AND RECOVERY (NEW)
# ============================================================================

async def handle_node_error(
    node_name: str, 
    error: Exception, 
    state: WebSocketState
) -> WebSocketState:
    """Handle errors that occur in LangGraph nodes"""
    log.error(f"Error in {node_name}: {error}", exc_info=True)
    
    # Create appropriate error state based on node
    if node_name == "conversation":
        error_message = "I'm having trouble understanding your request. Please try rephrasing it."
    elif node_name == "tool_execution":
        error_message = "I encountered an issue while processing your request. Please try again."
    elif node_name == "data_persistence":
        error_message = "I processed your request but had trouble saving the results. Please try again."
    else:
        error_message = "Something went wrong. Please try again."
    
    return {
        "error_state": {
            "type": f"{node_name}_error",
            "message": error_message,
            "details": str(error),
            "node": node_name
        },
        "processing_stage": f"{node_name}_failed",
        "confidence_score": 0.0
    }

def validate_langgraph_state(state: WebSocketState) -> bool:
    """Validate LangGraph state before processing"""
    required_fields = ["user_id", "messages"]
    
    for field in required_fields:
        if field not in state:
            log.error(f"Missing required field in state: {field}")
            return False
    
    if not state["messages"]:
        log.error("Empty messages in state")
        return False
    
    return True

# ============================================================================
# 10. MONITORING AND METRICS (NEW)
# ============================================================================

class LangGraphMetrics:
    """Simple metrics collection for LangGraph execution"""
    
    def __init__(self):
        self.node_execution_times = {}
        self.error_counts = {}
        self.success_counts = {}
    
    def record_node_execution(self, node_name: str, duration: float):
        """Record node execution time"""
        if node_name not in self.node_execution_times:
            self.node_execution_times[node_name] = []
        self.node_execution_times[node_name].append(duration)
    
    def record_error(self, node_name: str):
        """Record node error"""
        self.error_counts[node_name] = self.error_counts.get(node_name, 0) + 1
    
    def record_success(self, node_name: str):
        """Record node success"""
        self.success_counts[node_name] = self.success_counts.get(node_name, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            "node_execution_times": self.node_execution_times,
            "error_counts": self.error_counts,
            "success_counts": self.success_counts
        }

# Global metrics instance
langgraph_metrics = LangGraphMetrics()

# ============================================================================
# 11. CONFIGURATION AND SETUP (PRESERVED)
# ============================================================================

def setup_logging():
    """Configure logging for the orchestrator (existing function)"""
    # Reduce noise from SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    
    # Configure main logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Initialize logging when module is imported
setup_logging()

# ============================================================================
# 12. BACKWARDS COMPATIBILITY LAYER (PRESERVED)
# ============================================================================

class DatabaseService:
    """
    Preserved DatabaseService class for backwards compatibility
    Now acts as a wrapper around LangGraph state management
    """
    
    @staticmethod
    async def get_user_resume(user_id: str, db: AsyncSession) -> tuple[Optional[Resume], Optional[ResumeData]]:
        """Get or create user resume (preserved existing logic)"""
        result = await db.execute(select(Resume).where(Resume.user_id == user_id))
        db_resume = result.scalar_one_or_none()
        
        if db_resume and db_resume.data:
            fixed_data = fix_resume_data_structure(db_resume.data)
            return db_resume, ResumeData(**fixed_data)
        
        # Create default resume (existing logic)
        default_personal_info = PersonalInfo(
            name="User",
            email="",
            phone="",
            linkedin="",
            location="",
            summary=""
        )
        
        new_resume_data = ResumeData(
            personalInfo=default_personal_info,
            experience=[],
            education=[],
            skills=[]
        )
        
        new_db_resume = Resume(user_id=user_id, data=new_resume_data.dict())
        db.add(new_db_resume)
        await db.commit()
        await db.refresh(new_db_resume)
        
        return new_db_resume, new_resume_data
    
    @staticmethod
    async def save_message(
        user_id: str, 
        content: str, 
        is_user: bool, 
        page_id: Optional[str],
        db: AsyncSession
    ) -> str:
        """Save a message to database (preserved existing logic)"""
        # Validate content is not empty
        if not content or content.strip() == "":
            log.warning(f"Attempted to save empty message for user {user_id}, skipping")
            return ""
        
        message_id = str(uuid.uuid4())
        message = ChatMessage(
            id=message_id,
            user_id=user_id,
            page_id=page_id,
            message=content.strip(),  # Store trimmed content
            is_user_message=is_user
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message_id
    
    @staticmethod
    async def load_page_history(user_id: str, page_id: Optional[str], db: AsyncSession) -> List[Dict]:
        """Load chat history for a page (preserved existing logic)"""
        return await load_page_history(user_id, page_id, db)
    
    @staticmethod
    async def create_new_page(user_id: str, title: str, db: AsyncSession) -> str:
        """Create a new conversation page (preserved existing logic)"""
        return await create_new_page(user_id, title, db)

# Preserve any other existing classes and functions that might be imported elsewhere

# ============================================================================
# 13. EXPORT AND MODULE INTERFACE (PRESERVED)
# ============================================================================

# Export all the symbols that other modules might be importing
__all__ = [
    # Main router
    'router',
    
    # LangGraph components (new)
    'WebSocketState',
    'create_websocket_langgraph_app',
    'conversation_node',
    'tool_execution_node', 
    'data_persistence_node',
    'response_formatting_node',
    
    # WebSocket handlers
    'orchestrator_websocket',
    'handle_message_langgraph',
    'handle_page_switch_langgraph',
    'handle_regenerate_langgraph',
    
    # Utility functions (preserved + new)
    'DatabaseService',
    'get_shared_session_from_state',
    'setup_logging',
    'langgraph_metrics',
    
    # Helper functions
    'calculate_confidence_score',
    'extract_tool_calls_from_response', 
    'process_download_triggers',
    'get_user_friendly_error_message'
]

# ============================================================================
# 14. MIGRATION HELPERS (NEW)
# ============================================================================

class MigrationHelper:
    """
    Helper class to ease migration from AgentExecutor to LangGraph
    Provides compatibility methods during transition
    """
    
    @staticmethod
    def convert_agent_executor_call_to_langgraph(
        user_input: str,
        chat_history: List,
        user: User
    ) -> Dict[str, Any]:
        """
        Convert old AgentExecutor call format to LangGraph input format
        Useful during migration to maintain compatibility
        """
        return {
            "messages": chat_history + [HumanMessage(content=user_input)],
            "user_id": user.id,
            "page_id": None,
            "tool_results": {},
            "executed_tools": [],
            "confidence_score": 1.0,
            "processing_stage": "initialized"
        }
    
    @staticmethod
    def extract_response_from_langgraph_output(langgraph_output: Dict) -> str:
        """
        Extract response string from LangGraph output for compatibility
        """
        if "frontend_response" in langgraph_output:
            return langgraph_output["frontend_response"].get("message", "")
        
        # Fallback: look for AI message in messages
        messages = langgraph_output.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "No response generated"

# ============================================================================
# 15. TESTING AND DEVELOPMENT HELPERS (NEW)
# ============================================================================

async def test_langgraph_flow(user_id: str, test_message: str) -> Dict[str, Any]:
    """
    Test the LangGraph flow with a simple message
    Useful for development and debugging
    """
    try:
        # Create test user
        async with async_session_maker() as db:
            user = await get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Create LangGraph app
            app = await create_websocket_langgraph_app(user, db)
            
            # Prepare test input
            test_input = {
                "messages": [HumanMessage(content=test_message)],
                "user_id": user_id,
                "page_id": "test_page",
                "tool_results": {},
                "executed_tools": [],
                "confidence_score": 1.0,
                "processing_stage": "test",
                "db_session_id": str(uuid.uuid4()),
                "session_metadata": {"test": True}
            }
            
            # Run through LangGraph
            result = {}
            async for chunk in app.astream(test_input):
                result.update(chunk)
            
            return {
                "success": True,
                "result": result,
                "test_message": test_message
            }
            
    except Exception as e:
        log.error(f"Test flow error: {e}")
        return {
            "success": False,
            "error": str(e),
            "test_message": test_message
        }

def validate_langgraph_installation() -> Dict[str, bool]:
    """
    Validate that all LangGraph dependencies are properly installed
    """
    validation_results = {}
    
    try:
        from langgraph.graph import StateGraph
        validation_results["langgraph_core"] = True
    except ImportError:
        validation_results["langgraph_core"] = False
    
    try:
        from langgraph.prebuilt import ToolNode
        validation_results["langgraph_prebuilt"] = True
    except ImportError:
        validation_results["langgraph_prebuilt"] = False
    
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        validation_results["langgraph_postgres"] = True
    except ImportError:
        validation_results["langgraph_postgres"] = False
    
    return validation_results

# ============================================================================
# 16. STARTUP VALIDATION (NEW)
# ============================================================================

async def startup_validation():
    """
    Perform startup validation to ensure LangGraph setup is correct
    Call this when the application starts
    """
    log.info("Starting LangGraph orchestrator validation...")
    
    # Validate dependencies
    deps = validate_langgraph_installation()
    missing_deps = [k for k, v in deps.items() if not v]
    
    if missing_deps:
        log.error(f"Missing LangGraph dependencies: {missing_deps}")
        raise ImportError(f"Missing required dependencies: {missing_deps}")
    
    # Validate database connection
    try:
        async with async_session_maker() as session:
            await session.execute(select(1))
            await session.commit()
            await session.close()
        log.info("Database connection validated")
    except Exception as e:
        log.error(f"Database connection failed: {e}")
        raise
    
    # Validate LangGraph setup
    try:
        # Create a minimal test graph
        test_workflow = StateGraph(WebSocketState)
        test_workflow.add_node("test", lambda state: {"processing_stage": "test"})
        test_workflow.add_edge(START, "test")
        test_workflow.add_edge("test", END)
        test_graph = test_workflow.compile()
        log.info("LangGraph compilation validated")
    except Exception as e:
        log.error(f"LangGraph setup validation failed: {e}")
        raise
    
    log.info("✅ LangGraph orchestrator startup validation completed successfully")

# ============================================================================
# 17. PERFORMANCE MONITORING (NEW)
# ============================================================================

import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def monitor_node_performance(node_name: str):
    """Context manager to monitor node execution performance"""
    start_time = time.time()
    try:
        yield
        # Record success
        duration = time.time() - start_time
        langgraph_metrics.record_node_execution(node_name, duration)
        langgraph_metrics.record_success(node_name)
        log.info(f"Node {node_name} completed in {duration:.3f}s")
    except Exception as e:
        # Record error
        duration = time.time() - start_time
        langgraph_metrics.record_error(node_name)
        log.error(f"Node {node_name} failed after {duration:.3f}s: {e}")
        raise

async def get_performance_stats() -> Dict[str, Any]:
    """Get current performance statistics"""
    stats = langgraph_metrics.get_stats()
    
    # Calculate averages
    avg_times = {}
    for node, times in stats["node_execution_times"].items():
        if times:
            avg_times[node] = sum(times) / len(times)
    
    return {
        "average_execution_times": avg_times,
        "total_executions": {
            node: len(times) for node, times in stats["node_execution_times"].items()
        },
        "error_rates": {
            node: stats["error_counts"].get(node, 0) / 
                  (stats["success_counts"].get(node, 0) + stats["error_counts"].get(node, 0))
            for node in set(list(stats["success_counts"].keys()) + list(stats["error_counts"].keys()))
        },
        "raw_stats": stats
    }

# ============================================================================
# 18. GRACEFUL SHUTDOWN (NEW)
# ============================================================================

async def graceful_shutdown():
    """
    Gracefully shutdown the orchestrator
    Clean up active sessions and connections
    """
    log.info("Starting graceful shutdown of LangGraph orchestrator...")
    
    # Close all active database sessions
    session_ids = list(_active_sessions.keys())
    for session_id in session_ids:
        await cleanup_session(session_id)
    
    # Log final statistics
    stats = await get_performance_stats()
    log.info(f"Final performance stats: {stats}")
    
    log.info("✅ LangGraph orchestrator shutdown completed")

# ============================================================================
# 19. HEALTH CHECK ENDPOINT (NEW)
# ============================================================================

@router.get("/health/langgraph")
async def langgraph_health_check():
    """
    Health check endpoint for LangGraph orchestrator
    Returns system status and performance metrics
    """
    try:
        # Check database connectivity
        async with async_session_maker() as session:
            await session.execute(select(1))
            await session.commit()
            await session.close()
        
        # Get performance stats
        stats = await get_performance_stats()
        
        # Check dependency status
        deps = validate_langgraph_installation()
        
        return {
            "status": "healthy",
            "langgraph_version": "latest",
            "dependencies": deps,
            "performance": stats,
            "active_sessions": len(_active_sessions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# END OF ENHANCED ORCHESTRATOR
# ============================================================================