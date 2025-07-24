import os
import logging
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import List, Literal, Optional, Any, Dict, TypedDict

from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import Tool

from app.db import get_db
from app.models_db import User, ChatMessage, Document, Page
from app.dependencies import get_current_active_user_ws
from app.vector_store import get_user_vector_store
from langchain.tools.retriever import create_retriever_tool
from app.enhanced_memory import EnhancedMemoryManager

# --- All Tool Imports ---
from .orchestrator_tools.add_certification import add_certification
from .orchestrator_tools.add_education import add_education
from .orchestrator_tools.add_projects import add_projects
from .orchestrator_tools.add_work_experience import add_work_experience
from .orchestrator_tools.analyze_skills_gap import analyze_skills_gap
from .orchestrator_tools.analyze_specific_document import analyze_specific_document
from .orchestrator_tools.browser_web_with_langchain import browse_web_with_langchain
from .orchestrator_tools.create_career_development_plan import create_career_development_plan
from .orchestrator_tools.create_resume_from_scratch import create_resume_from_scratch
from .orchestrator_tools.enhance_resume_section import enhance_resume_section
from .orchestrator_tools.enhanced_document_search import enhanced_document_search
from .orchestrator_tools.generate_cover_letter import generate_cover_letter
from .orchestrator_tools.generate_resume_pdf import generate_resume_pdf
from .orchestrator_tools.generate_tailored_resume import generate_tailored_resume
from .orchestrator_tools.get_ats_optimization_tips import get_ats_optimization_tips
from .orchestrator_tools.get_current_time_and_date import get_current_time_and_date
from .orchestrator_tools.get_cv_best_practices import get_cv_best_practices
from .orchestrator_tools.get_interview_preparation_guide import get_interview_preparation_guide
from .orchestrator_tools.get_salary_negotiation_advice import get_salary_negotiation_advice
from .orchestrator_tools.list_documents import list_documents
from .orchestrator_tools.manage_skills_comprehensive import manage_skills_comprehensive
from .orchestrator_tools.read_document import read_document
from .orchestrator_tools.refine_cover_letter_from_url import refine_cover_letter_from_url
from .orchestrator_tools.refine_cv_for_role import refine_cv_for_role
from .orchestrator_tools.search_jobs_linkedin_api import search_jobs_linkedin_api
from .orchestrator_tools.set_skills import set_skills
from .orchestrator_tools.show_resume_download_options import show_resume_download_options
from .orchestrator_tools.update_personal_information import update_personal_information

load_dotenv()
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter()

# --- CORRECTED & FINAL: Load prompts with a fallback ---
def load_prompt_from_file(file_name: str) -> Optional[str]:
    """Helper to load a prompt from the orchestrator_prompts directory."""
    prompt_path = Path(__file__).parent / "orchestrator_prompts" / file_name
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        log.warning(f"Prompt file not found: {file_name}")
        return None

# Load the main prompt, and if it fails, load the fallback.
MAIN_SYSTEM_PROMPT = load_prompt_from_file("system_prompt.txt")
if not MAIN_SYSTEM_PROMPT:
    MAIN_SYSTEM_PROMPT = load_prompt_from_file("fallback_system_prompt.txt")
    if not MAIN_SYSTEM_PROMPT:
        # If both fail, use a hardcoded, basic prompt to prevent a crash.
        log.error("CRITICAL: Both main and fallback prompts are missing. Agent will be unreliable.")
        MAIN_SYSTEM_PROMPT = "You are a helpful assistant."


# --- 1. State & Pydantic Models ---

class AgentState(TypedDict):
    """The shared state for the graph."""
    input: str
    chat_history: list[BaseMessage]
    route: Literal[
        "profile_management", "document_interaction", "resume_cv",
        "job_search", "career_guidance", "general_conversation"
    ]
    agent_outcome: Any
    final_response: str
    critique: str
    retry_count: int
    # Dependencies for tool execution
    db_session: AsyncSession
    current_user: User

class RouteQuery(BaseModel):
    """Route a user query to the appropriate specialist agent."""
    datasource: Literal[
        "profile_management", "document_interaction", "resume_cv",
        "job_search", "career_guidance", "general_conversation"
    ] = Field(description="Given the user query, pick the best specialist agent to handle it.")

class Validation(BaseModel):
    """An evaluation of the agent's response."""
    is_sufficient: bool = Field(description="Is the response high-quality, accurate, and ready to be sent to the user?")
    critique: Optional[str] = Field(description="Specific, actionable feedback if the content is not sufficient.")


# --- 2. Specialist Worker Creation ---

class StateInjectingTool:
    """Wrapper to inject state dependencies into tools."""
    
    def __init__(self, original_tool):
        self.original_tool = original_tool
        self.__name__ = getattr(original_tool, '__name__', 'unknown')
        self.__doc__ = getattr(original_tool, '__doc__', '')
        
        # Copy tool attributes for LangChain compatibility 
        if hasattr(original_tool, 'name'):
            self.name = original_tool.name
        if hasattr(original_tool, 'description'):
            self.description = original_tool.description
        if hasattr(original_tool, 'args_schema'):
            self.args_schema = original_tool.args_schema
            
        # Check if tool needs db/user injection by examining args_schema
        self.needs_db_user = False
        if hasattr(original_tool, 'args_schema') and original_tool.args_schema:
            # Use model_fields for Pydantic v2 compatibility
            if hasattr(original_tool.args_schema, 'model_fields'):
                fields = list(original_tool.args_schema.model_fields.keys())
            elif hasattr(original_tool.args_schema, '__fields__'):
                fields = list(original_tool.args_schema.__fields__.keys())
            else:
                fields = []
            
            # Check if db and user are in the first two parameters
            self.needs_db_user = len(fields) >= 2 and fields[0] == 'db' and fields[1] == 'user'
    
    async def __call__(self, *args, state: AgentState = None, **kwargs):
        """Inject db and user from state into tool call if needed."""
        if state and self.needs_db_user:
            # Tools that need db and user as first two positional args
            db_session = state.get('db_session')
            current_user = state.get('current_user')
            return await self.original_tool(db_session, current_user, *args, **kwargs)
        else:
            # Tools that don't need db/user injection or no state provided
            return await self.original_tool(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(self.original_tool, name)

def wrap_tools_with_state_injection(tools: list) -> list:
    """Wrap tools to inject dependencies from state."""
    return [StateInjectingTool(tool) for tool in tools]

def create_agent_node(tools: list, system_prompt: str):
    """Create an agent node that can decide to call tools."""
    
    async def agent_node(state: AgentState):
        """The agent decision-making node with reasoning streams."""
        route = state.get('route', 'unknown')
        log.info(f"--- 🤖 AGENT NODE ({route}) ---")
        
        # Stream reasoning start - matches your app's Brain icon theme
        reasoning_start = {
            "type": "reasoning_start",
            "specialist": route,
            "message": f"🧠 {route.replace('_', ' ').title()} specialist is analyzing your request..."
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}\n{critique}"),
        ])
        
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.2)
        llm_with_tools = llm.bind_tools(tools)
        
        # Stream thinking process
        reasoning_thinking = {
            "type": "reasoning_chunk",
            "content": "Understanding the context and requirements...",
            "step": "analysis"
        }
        
        response = await (prompt | llm_with_tools).ainvoke({
            "input": state["input"],
            "chat_history": state["chat_history"],
            "critique": state.get("critique", "")
        })
        
        # Check if the model wants to call tools
        if response.tool_calls:
            # Stream tool planning
            tool_names = [call["name"] for call in response.tool_calls]
            tool_planning = {
                "type": "reasoning_chunk", 
                "content": f"Planning to use tools: {', '.join(tool_names)}",
                "step": "tool_planning",
                "tools": tool_names
            }
            
            return {
                "agent_outcome": {
                    "output": response,
                    "tool_calls": response.tool_calls
                },
                "reasoning_events": [reasoning_start, reasoning_thinking, tool_planning]
            }
        else:
            # Direct response without tools
            reasoning_complete = {
                "type": "reasoning_complete",
                "content": "Analysis complete - providing direct response",
                "confidence": "high"
            }
            
            return {
                "agent_outcome": {"output": response.content},
                "final_response": response.content,
                "reasoning_events": [reasoning_start, reasoning_thinking, reasoning_complete]
            }
    
    return agent_node

def create_tool_node(tools: list):
    """Create a ToolNode for tool execution."""
    wrapped_tools = wrap_tools_with_state_injection(tools)
    
    async def tool_execution_node(state: AgentState):
        """Execute tools with state injection and reasoning streams."""
        log.info(f"--- 🔧 TOOL NODE ---")
        
        agent_outcome = state.get("agent_outcome", {})
        tool_calls = agent_outcome.get("tool_calls", [])
        reasoning_events = []
        
        if not tool_calls:
            # No tools to execute, return current state
            return state
        
        # Stream tool execution start
        reasoning_events.append({
            "type": "reasoning_chunk",
            "content": f"⚙️ Executing {len(tool_calls)} tool{'s' if len(tool_calls) > 1 else ''}...",
            "step": "tool_execution_start",
            "tool_count": len(tool_calls)
        })
        
        tool_results = []
        for i, tool_call in enumerate(tool_calls, 1):
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Stream individual tool progress
            reasoning_events.append({
                "type": "reasoning_chunk",
                "content": f"🔧 Running {tool_name} ({i}/{len(tool_calls)})",
                "step": "tool_progress",
                "tool_name": tool_name,
                "progress": f"{i}/{len(tool_calls)}"
            })
            
            # Find the matching tool
            matching_tool = None
            for tool in wrapped_tools:
                if getattr(tool, 'name', tool.__name__) == tool_name:
                    matching_tool = tool
                    break
            
            if matching_tool:
                try:
                    result = await matching_tool(**tool_args, state=state)
                    tool_results.append(f"Tool {tool_name}: {result}")
                    
                    # Stream tool success
                    reasoning_events.append({
                        "type": "reasoning_chunk",
                        "content": f"✅ {tool_name} completed successfully",
                        "step": "tool_success",
                        "tool_name": tool_name
                    })
                except Exception as e:
                    error_msg = f"Tool {tool_name} failed: {str(e)}"
                    log.error(f"Tool execution error for {tool_name}: {e}")
                    tool_results.append(error_msg)
                    
                    # Stream tool error
                    reasoning_events.append({
                        "type": "reasoning_chunk", 
                        "content": f"❌ {tool_name} encountered an error",
                        "step": "tool_error",
                        "tool_name": tool_name,
                        "error": str(e)
                    })
            else:
                error_msg = f"Tool {tool_name} not found"
                tool_results.append(error_msg)
                reasoning_events.append({
                    "type": "reasoning_chunk",
                    "content": f"⚠️ {tool_name} not available",
                    "step": "tool_not_found",
                    "tool_name": tool_name
                })
        
        # Stream completion
        reasoning_events.append({
            "type": "reasoning_chunk",
            "content": "🎯 Tool execution complete - preparing response",
            "step": "tool_execution_complete"
        })
        
        # Combine tool results into final response
        final_response = "\n".join(tool_results)
        
        return {
            "agent_outcome": {"output": final_response},
            "final_response": final_response,
            "reasoning_events": reasoning_events
        }
    
    return tool_execution_node

# --- 3. Graph Node Functions ---

async def router_node(state: AgentState):
    """Classifies the user input and decides the route."""
    log.info("--- 🚦 ROUTER ---")
    prompt = f"""You are an expert at routing a user's request to the correct specialist.
    Based on the user's query, select the appropriate specialist from the available choices.

    User Query:
    {state['input']}"""
    
    # Use a faster, cheaper model for routing
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.0)
    structured_llm = llm.with_structured_output(RouteQuery)
    response = await structured_llm.ainvoke(prompt)
    
    log.info(f"Route selected: {response.datasource}")
    return {"route": response.datasource, "retry_count": 0, "critique": ""}

async def validator_node(state: AgentState):
    """Evaluates the worker's output and decides if it's sufficient."""
    log.info("--- 🕵️ VALIDATOR ---")
    
    # Get agent output and handle different formats
    agent_outcome = state.get('agent_outcome', {})
    agent_output = agent_outcome.get('output', '')
    
    # Handle LangChain message objects
    if hasattr(agent_output, 'content'):
        agent_output = agent_output.content
    elif not isinstance(agent_output, str):
        agent_output = str(agent_output)
    
    if not agent_output or not agent_output.strip():
        # Handle cases where the agent might fail and produce no output
        log.warning("Validator received no agent output. Forcing retry.")
        log.info(f"Agent outcome debug: {agent_outcome}")
        return {"critique": "The previous attempt failed to generate a response. Please try again.", "retry_count": state.get('retry_count', 0) + 1}

    prompt = f"""You are a meticulous Quality Assurance agent. Your role is to validate the response generated by another AI agent.

    User's Original Query:
    {state['input']}

    Agent's Generated Response:
    {agent_output}

    Your Tasks:
    1.  **Check for Correctness**: Does the response accurately and completely answer the user's query?
    2.  **Check for Quality**: Is the response well-written, professional, and free of grammatical errors?
    3.  **Check for Hallucinations**: Does the agent claim to have done something it cannot do? (e.g., "I've emailed you the resume" - it cannot email).

    Based on your evaluation, decide if the response is sufficient. If not, provide a concise, actionable critique for the agent to use on its next attempt.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.0)
    structured_llm = llm.with_structured_output(Validation)
    response = await structured_llm.ainvoke(prompt)

    if response.is_sufficient:
        log.info("Validation PASSED.")
        # --- CORRECTED: Access the 'output' key directly ---
        return {"final_response": agent_output}
    else:
        log.info(f"Validation FAILED. Critique: {response.critique}")
        return {"critique": response.critique, "retry_count": state.get('retry_count', 0) + 1}

# --- Main WebSocket Function ---

@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_active_user_ws),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    log.info(f"WebSocket connected for user: {user.id}")

    # --- Tool Setup without functools.partial ---
    # Dependencies will be injected through state at runtime
    
    profile_tools = [
        update_personal_information,
        add_work_experience,
        add_education,
        set_skills,
        manage_skills_comprehensive,
        add_projects,
        add_certification,
    ]
    document_tools = [
        list_documents,
        read_document,
        enhanced_document_search,
        analyze_specific_document,
    ]
    resume_cv_tools = [
        create_resume_from_scratch,
        generate_tailored_resume,
        refine_cv_for_role,
        enhance_resume_section,
        generate_resume_pdf,
        show_resume_download_options,
    ]
    job_search_tools = [search_jobs_linkedin_api, browse_web_with_langchain]
    career_guidance_tools = [
        get_interview_preparation_guide,
        get_salary_negotiation_advice,
        create_career_development_plan,
        get_cv_best_practices,
        get_ats_optimization_tips,
        analyze_skills_gap,
    ]
    cover_letter_tools = [
        generate_cover_letter,
        refine_cover_letter_from_url,
    ]

    # --- Worker Definitions ---
    # Load the specific prompt for the conversational agent
    general_prompt = load_prompt_from_file("general_conversation_prompt.txt") or "You are a helpful assistant."

    # Create agent and tool nodes for each specialist
    agent_nodes = {}
    tool_nodes = {}
    
    specialist_configs = {
        "profile_management": (profile_tools, MAIN_SYSTEM_PROMPT),
        "document_interaction": (document_tools, MAIN_SYSTEM_PROMPT),
        "resume_cv": (resume_cv_tools + cover_letter_tools, MAIN_SYSTEM_PROMPT),
        "job_search": (job_search_tools, MAIN_SYSTEM_PROMPT),
        "career_guidance": (career_guidance_tools, MAIN_SYSTEM_PROMPT),
        "general_conversation": ([], general_prompt),
    }
    
    for route_name, (tools, system_prompt) in specialist_configs.items():
        agent_nodes[route_name] = create_agent_node(tools, system_prompt)
        tool_nodes[route_name] = create_tool_node(tools)

    # --- Graph Construction ---
    workflow = StateGraph(AgentState)
    workflow.add_node("router", router_node)

    # Add agent and tool nodes for each specialist
    for route_name in specialist_configs.keys():
        # Add agent decision node
        workflow.add_node(f"{route_name}_agent", agent_nodes[route_name])
        # Add tool execution node  
        workflow.add_node(f"{route_name}_tools", tool_nodes[route_name])
        
        # Connect agent to tools, then tools to validator
        workflow.add_edge(f"{route_name}_agent", f"{route_name}_tools")
        workflow.add_edge(f"{route_name}_tools", "validator")
    
    workflow.add_node("validator", validator_node)

    def route_to_worker(state: AgentState):
        """Route to the appropriate agent node."""
        route = state["route"]
        return f"{route}_agent"

    workflow.add_conditional_edges("router", route_to_worker)

    def check_validation(state: AgentState):
        """Check if response is valid or needs retry."""
        if state.get("final_response"):
            return END
        if state["retry_count"] >= 2:
            log.warning("Max retries reached. Exiting graph.")
            return END
        # Loop back to the correct agent for retry
        return f"{state['route']}_agent"

    workflow.add_conditional_edges("validator", check_validation)
    workflow.set_entry_point("router")
    graph = workflow.compile()
    
    # --- Main WebSocket Loop ---
    memory_manager = EnhancedMemoryManager(db, user)
    
    # This outer try/except is for connection-level errors (e.g., the client disconnects)
    try:
        while True:
            # --- NEW: Inner try/except for message-level errors ---
            # This ensures that an error processing one message does not kill the entire connection.
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                message_content = message_data.get("content")
                page_id = message_data.get("page_id")

                # 1. Validate incoming user message
                if not message_content or not message_content.strip():
                    log.warning(f"User {user.id} sent an empty message. Ignoring.")
                    await websocket.send_json({"type": "error", "message": "Cannot process an empty message."})
                    continue # Wait for the next message

                # Validate or create page
                if not page_id:
                    new_page = Page(user_id=user.id, title=message_content[:50])
                    db.add(new_page)
                    await db.commit()
                    await db.refresh(new_page)
                    page_id = new_page.id
                    await websocket.send_json({"type": "page_created", "page_id": page_id, "title": new_page.title})
                else:
                    # Verify the page exists and belongs to the user
                    existing_page = await db.execute(
                        select(Page).where(Page.id == page_id, Page.user_id == user.id)
                    )
                    if not existing_page.scalar_one_or_none():
                        log.warning(f"Page {page_id} not found for user {user.id}, creating new page")
                        new_page = Page(user_id=user.id, title=message_content[:50])
                        db.add(new_page)
                        await db.commit()
                        await db.refresh(new_page)
                        page_id = new_page.id
                        await websocket.send_json({"type": "page_created", "page_id": page_id, "title": new_page.title})

                # Save user message (already validated)
                try:
                    db.add(ChatMessage(id=str(uuid.uuid4()), user_id=user.id, page_id=page_id, message=message_content, is_user_message=True))
                    await db.commit()
                except Exception as db_error:
                    log.error(f"Failed to save user message to database for user {user.id}, page {page_id}: {db_error}")
                    await db.rollback()
                    # Send error to user and continue
                    await websocket.send_json({
                        "type": "error", 
                        "message": "Failed to save your message. Please try again."
                    })
                    continue
                
                # Load history
                context = await memory_manager.get_conversation_context(page_id)
                chat_history = [HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]) for msg in context.recent_messages]

                initial_state = {
                    "input": message_content, 
                    "chat_history": chat_history,
                    "db_session": db,
                    "current_user": user
                }
                
                # Invoke Graph and stream intermediate steps
                final_response = None # Start with None
                async for event in graph.astream(initial_state):
                    log.info(f"Graph event: {list(event.keys())}")  # Debug logging
                    
                    if "router" in event:
                        await websocket.send_json({"type": "info", "message": f"Routing to {event['router']['route']} specialist..."})
                    
                    if "validator" in event:
                        if event['validator'].get('critique'):
                            await websocket.send_json({"type": "info", "message": f"Refining response... Critique: {event['validator']['critique']}"})
                        else:
                            await websocket.send_json({"type": "info", "message": "Validating response..."})
                    
                    # Handle agent responses (both with and without tools)
                    for node_name, node_data in event.items():
                        if node_name.endswith("_agent") or node_name.endswith("_tools"):
                            await websocket.send_json({"type": "info", "message": f"Processing with {node_name}..."})
                        
                        # Stream reasoning events
                        if isinstance(node_data, dict) and node_data.get("reasoning_events"):
                            for reasoning_event in node_data["reasoning_events"]:
                                await websocket.send_json({
                                    "type": reasoning_event["type"],
                                    "data": reasoning_event,
                                    "timestamp": datetime.now().isoformat()
                                })
                        
                        # Check for final response in any node
                        if isinstance(node_data, dict) and node_data.get("final_response"):
                            final_response = node_data["final_response"]
                            log.info(f"Found final_response in {node_name}: {final_response[:100]}...")
                    
                    # Check END event
                    if END in event:
                        final_response = event[END].get("final_response")
                        if final_response:
                            log.info(f"Found final_response in END: {final_response[:100]}...")

                # 2. Validate the final AI response before sending and saving
                if not final_response or not final_response.strip():
                    log.error(f"AI failed to generate a valid response for user {user.id} on page {page_id}.")
                    log.error(f"Final state debug: {list(initial_state.keys())}")
                    
                    # Try to extract any available output from the state
                    fallback_response = None
                    if initial_state.get("agent_outcome"):
                        outcome = initial_state["agent_outcome"]
                        if isinstance(outcome, dict) and outcome.get("output"):
                            output = outcome["output"]
                            if hasattr(output, 'content'):
                                fallback_response = output.content
                            elif isinstance(output, str):
                                fallback_response = output
                    
                    final_response = fallback_response or "I'm sorry, I encountered an issue and couldn't complete your request. Please try again."
                    # We send this error message to the user, but we still save it to the history
                    # to maintain the conversation context.

                # Send final response
                await websocket.send_json({"type": "message", "message": final_response})
                
                # Save AI message (already validated)
                try:
                    db.add(ChatMessage(id=str(uuid.uuid4()), user_id=user.id, page_id=page_id, message=final_response, is_user_message=False))
                    await db.commit()
                except Exception as db_error:
                    log.error(f"Failed to save AI message to database for user {user.id}, page {page_id}: {db_error}")
                    await db.rollback()
                    # Continue anyway - user got the response via WebSocket

            except Exception as e:
                # This block catches errors for a single message, logs them, and informs the user.
                log.error(f"Error processing message for user {user.id}: {e}", exc_info=True)
                # Send a user-friendly error message over the WebSocket
                await websocket.send_json({
                    "type": "error",
                    "message": "An unexpected error occurred. Please try sending your message again."
                })
                # The 'continue' statement is implicit here; the loop will proceed to the next iteration.

    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        # This catches errors that happen outside the message loop (e.g., initial connection).
        log.error(f"A critical WebSocket error occurred for user {user.id}: {e}", exc_info=True)
        # The connection will close, which is appropriate for a critical failure.