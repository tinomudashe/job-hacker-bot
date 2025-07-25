import os
import logging
import uuid
import json
import asyncio
import re
import inspect
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

from app.db import get_db, SessionLocal # Import the session factory
from app.models_db import User, ChatMessage, Document, Page
from app.dependencies import get_current_active_user_ws
from app.vector_store import get_user_vector_store
from langchain.tools.retriever import create_retriever_tool
from app.enhanced_memory import EnhancedMemoryManager
from app.simple_memory import SimpleMemoryManager
from app.advanced_memory import AdvancedMemoryManager, create_memory_tools

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
MAIN_SYSTEM_PROMPT = """You are Job Hacker Bot, an expert AI career assistant. Your primary goal is to provide specific, actionable, and personalized advice based on the user's documents and profile.

**Your Core Directives:**
1.  **ALWAYS Check for User Documents First:** Before answering any question about a user's CV, resume, skills, or experience, you MUST use the `list_documents` or `enhanced_document_search` tools to see if you have access to their files.
2.  **NEVER Say "I haven't seen your CV":** If you have access to documents, state that you have found them. If you cannot find any documents, politely ask the user to upload one first.
3.  **Be Proactive, Not Passive:** Instead of waiting for the user to ask, suggest actions. For example: "I found your resume. It seems to be focused on backend development. Would you like me to help you tailor it for a DevOps role?"
4.  **Use Tools to Answer Questions:** When asked to analyze something, use your document analysis tools. When asked about jobs, use your job search tools. Your answers should be based on the information retrieved from your tools.
5.  **Provide Specific, Concrete Feedback:** Avoid generic advice. Instead of "Use quantifiable achievements," say "In your experience at Acme Corp, you mentioned you 'developed a new feature.' Let's refine that. Can you estimate how much it improved performance or user engagement?"
"""
if not MAIN_SYSTEM_PROMPT:
    MAIN_SYSTEM_PROMPT = load_prompt_from_file("fallback_system_prompt.txt")
    if not MAIN_SYSTEM_PROMPT:
        # If both fail, use a hardcoded, basic prompt to prevent a crash.
        log.error("CRITICAL: Both main and fallback prompts are missing. Agent will be unreliable.")
        MAIN_SYSTEM_PROMPT = "You are a helpful assistant."


def _redact_pii(text: str) -> str:
    """Redacts common PII patterns from a string for safe memory processing."""
    if not isinstance(text, str):
        return text

    # Simple regex for emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    # Simple regex for phone numbers (covers many common formats)
    phone_pattern = r'\(?\b\d{3}\b\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    text = re.sub(email_pattern, '[REDACTED_EMAIL]', text, flags=re.IGNORECASE)
    text = re.sub(phone_pattern, '[REDACTED_PHONE]', text)
    
    return text


async def _get_unified_context_summary(
    simple_memory: SimpleMemoryManager,
    enhanced_memory: EnhancedMemoryManager,
    advanced_memory: AdvancedMemoryManager,
    user_message: str,
    page_id: Optional[str]
) -> str:
    """
    Fetches context from all memory managers and creates a unified summary string
    for the agent. This context is NOT shown to the user.
    """
    summary_parts = []
    try:
        # Use asyncio.gather to fetch contexts concurrently for efficiency
        enhanced_ctx_task = enhanced_memory.get_conversation_context(page_id=page_id, include_user_learning=True)
        advanced_ctx_task = advanced_memory.load_relevant_context(current_message=user_message)
        
        enhanced_context, advanced_context = await asyncio.gather(
            enhanced_ctx_task,
            advanced_ctx_task
        )

        # 1. Add long-term memories from AdvancedMemoryManager
        if advanced_context and advanced_context.relevant_memories:
            memories_text = "\n".join([f"- {memory}" for memory in advanced_context.relevant_memories])
            summary_parts.append(f"Here is what I remember about you:\n{memories_text}")

        # 2. Add conversation summary from EnhancedMemoryManager
        if enhanced_context and enhanced_context.summary and "New conversation" not in enhanced_context.summary:
            summary_parts.append(f"Here is a summary of our recent conversation:\n{enhanced_context.summary}")
        
        # 3. Add key topics from EnhancedMemoryManager
        if enhanced_context and enhanced_context.key_topics:
            summary_parts.append(f"Key topics we discussed: {', '.join(enhanced_context.key_topics)}")

        if not summary_parts:
            return ""

        final_summary = "INTERNAL CONTEXT FOR AI (User does not see this):\n\n" + "\n\n".join(summary_parts)
        return final_summary

    except Exception as e:
        log.error(f"Error getting unified context summary: {e}", exc_info=True)
        return "" # Return empty string on error to not break the flow


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
    # Dependencies are now pre-injected into tools during creation

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

from pydantic import create_model
from functools import wraps

def get_clean_tool_schema(original_tool):
    """Create a clean schema that excludes db/user parameters for LangChain."""
    if not hasattr(original_tool, 'args_schema') or not original_tool.args_schema:
        return None
    
    original_schema = original_tool.args_schema
    
    # Get fields from Pydantic model (v2 compatibility)
    if hasattr(original_schema, 'model_fields'):
        fields = original_schema.model_fields
    elif hasattr(original_schema, '__fields__'):
        fields = original_schema.__fields__
    else:
        return None
    
    # Remove db, user, and lock parameters from schema
    clean_fields = {k: v for k, v in fields.items() if k not in ['db', 'user', 'resume_modification_lock']}
    
    if not clean_fields:
        return None
    
    # Create new Pydantic model with only user-facing parameters
    CleanSchema = create_model(
        f"{original_schema.__name__}Clean",
        **{k: (v.annotation, v.default) if hasattr(v, 'annotation') else (v.type_, v.default) 
           for k, v in clean_fields.items()}
    )
    
    return CleanSchema

def check_tool_needs_injection(original_tool):
    """Check if tool needs db/user injection by examining its parameters."""
    import inspect
    
    # For StructuredTool objects, check args_schema
    if hasattr(original_tool, 'args_schema') and original_tool.args_schema:
        # Get field names
        if hasattr(original_tool.args_schema, 'model_fields'):
            field_names = list(original_tool.args_schema.model_fields.keys())
        elif hasattr(original_tool.args_schema, '__fields__'):
            field_names = list(original_tool.args_schema.__fields__.keys())
        else:
            field_names = []
        
        # Check if first two parameters are db and user
        return len(field_names) >= 2 and field_names[0] == 'db' and field_names[1] == 'user'
    
    # For raw functions, check function signature
    if callable(original_tool):
        try:
            sig = inspect.signature(original_tool)
            param_names = list(sig.parameters.keys())
            # Restore the check for the lock parameter to correctly identify tools that need it.
            return (len(param_names) >= 2 and param_names[0] == 'db' and param_names[1] == 'user') or \
                   (len(param_names) >= 3 and param_names[0] == 'db' and param_names[1] == 'user' and 'resume_modification_lock' in param_names[2])
        except (ValueError, TypeError):
            return False
    
    return False

def create_dependency_injected_tool(
    original_tool, 
    db_session: AsyncSession, 
    current_user: User, 
    resume_lock: asyncio.Lock,
    tools_that_need_lock: List[str]
):
    """Create a tool with dependencies and optional locking pre-injected."""
    
    needs_injection = check_tool_needs_injection(original_tool)
    tool_name = getattr(original_tool, 'name', getattr(original_tool, '__name__', 'unknown_tool'))
    
    # Check if this specific tool's execution should be locked
    needs_lock = tool_name in tools_that_need_lock

    if needs_injection:
        # Create wrapper that injects dependencies and handles locking
        @wraps(original_tool)
        async def injected_tool(**kwargs):
            try:
                log.info(f"Executing tool {tool_name} with injected dependencies. Needs lock: {needs_lock}")

                # --- DEFINITIVE BUG FIX ---
                # This new, robust logic uses `inspect` to dynamically build the
                # argument list for any tool, ensuring all parameters are passed correctly.
                
                # Get the signature of the original tool function.
                sig = inspect.signature(original_tool.func if hasattr(original_tool, 'func') else original_tool)
                params = sig.parameters

                # Build the dictionary of arguments to pass to the original tool.
                call_args = {}
                if 'db' in params:
                    call_args['db'] = db_session
                if 'user' in params:
                    call_args['user'] = current_user
                if 'resume_modification_lock' in params:
                    call_args['resume_modification_lock'] = resume_lock
                
                # Add the keyword arguments from the AI's call.
                call_args.update(kwargs)

                # Define the core execution logic.
                async def execute_tool():
                    return await (original_tool.func if hasattr(original_tool, 'func') else original_tool)(**call_args)

                # Use the lock if needed, but the arguments are now always correct.
                if needs_lock:
                    log.info(f"Acquiring lock for tool: {tool_name}")
                    async with resume_lock:
                        log.info(f"Lock acquired for tool: {tool_name}")
                        result = await execute_tool()
                    log.info(f"Lock released for tool: {tool_name}")
                else:
                    result = await execute_tool()
                
                # Add UI data validation for specific tools
                if tool_name == 'generate_cover_letter':
                    if result and '[DOWNLOADABLE_COVER_LETTER]' not in str(result):
                        result = f"[DOWNLOADABLE_COVER_LETTER]\n{result}"
                elif tool_name == 'create_resume_from_scratch' or tool_name == 'generate_tailored_resume':
                    if result and '[DOWNLOADABLE_RESUME]' not in str(result):
                        result = f"[DOWNLOADABLE_RESUME]\n{result}"
                elif tool_name == 'get_interview_preparation_guide':
                    if result and '[INTERVIEW_FLASHCARDS_AVAILABLE]' not in str(result):
                        result = f"{result}\n\n[INTERVIEW_FLASHCARDS_AVAILABLE]"
                
                return result
                
            except Exception as e:
                log.error(f"Tool {tool_name} execution failed: {e}", exc_info=True)
                # Return user-friendly error message instead of crashing
                return f"⚠️ The {tool_name.replace('_', ' ')} tool encountered an issue: {str(e)}\n\nPlease try again or contact support if this continues."
        
        # Create Tool with clean schema (no db/user parameters exposed)
        return Tool.from_function(
            func=injected_tool,
            name=tool_name,
            description=getattr(original_tool, 'description', original_tool.__doc__ or f"{tool_name} tool"),
            args_schema=get_clean_tool_schema(original_tool)
        )
    else:
        # Tool doesn't need injection, but check if schema needs cleaning
        if hasattr(original_tool, 'args_schema') and original_tool.args_schema:
            # Get original and clean schemas to compare
            original_schema = original_tool.args_schema
            clean_schema = get_clean_tool_schema(original_tool)
            
            # Get field names for comparison
            if hasattr(original_schema, 'model_fields'):
                orig_fields = set(original_schema.model_fields.keys())
            elif hasattr(original_schema, '__fields__'):
                orig_fields = set(original_schema.__fields__.keys())
            else:
                orig_fields = set()
            
            if clean_schema:
                if hasattr(clean_schema, 'model_fields'):
                    clean_fields = set(clean_schema.model_fields.keys())
                elif hasattr(clean_schema, '__fields__'):
                    clean_fields = set(clean_schema.__fields__.keys())
                else:
                    clean_fields = set()
            else:
                clean_fields = set()
            
            # Only create wrapper if fields were actually removed
            if orig_fields != clean_fields and clean_schema:
                # Tool schema had db/user params that were removed, create clean version
                return Tool.from_function(
                    func=original_tool,
                    name=tool_name,
                    description=getattr(original_tool, 'description', original_tool.__doc__ or f"{tool_name} tool"),
                    args_schema=clean_schema
                )
        
        # Tool doesn't have db/user params or no cleaning needed, return as-is
        return original_tool

def create_tools_with_dependencies(
    tool_functions: list, 
    db_session: AsyncSession, 
    current_user: User,
    resume_lock: asyncio.Lock,
    tools_that_need_lock: List[str]
) -> list:
    """Create all tools with dependencies pre-injected."""
    injected_tools = []
    
    for tool_func in tool_functions:
        try:
            injected_tool = create_dependency_injected_tool(
                tool_func, db_session, current_user, resume_lock, tools_that_need_lock
            )
            injected_tools.append(injected_tool)
            log.info(f"Successfully created tool: {getattr(tool_func, 'name', getattr(tool_func, '__name__', 'unknown_tool'))}")
        except Exception as e:
            log.error(f"Failed to create tool {getattr(tool_func, 'name', getattr(tool_func, '__name__', 'unknown_tool'))}: {e}")
            # Continue with other tools rather than failing completely
            continue
    
    return injected_tools

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
            "content": f"🧠 {route.replace('_', ' ').title()} specialist is analyzing your request..."
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}\n{critique}"),
        ])
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.2)
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
    """Create a ToolNode for tool execution with guaranteed UI completion events."""
    
    async def tool_execution_node(state: AgentState):
        """Execute tools with guaranteed reasoning stream completion."""
        log.info(f"--- 🔧 TOOL NODE ---")
        
        agent_outcome = state.get("agent_outcome", {})
        tool_calls = agent_outcome.get("tool_calls", [])
        reasoning_events = []
        
        if not tool_calls:
            # No tools to execute, still send completion event for UI
            reasoning_events.append({
                "type": "reasoning_complete",
                "content": "✨ Analysis complete - no tools needed",
                "step": "direct_response"
            })
            return {
                "reasoning_events": reasoning_events
            }
        
        # Stream tool execution start
        reasoning_events.append({
            "type": "reasoning_chunk",
            "content": f"⚙️ Executing {len(tool_calls)} tool{'s' if len(tool_calls) > 1 else ''}...",
            "step": "tool_execution_start",
            "tool_count": len(tool_calls)
        })
        
        tool_results = []
        successful_tools = 0
        
        # Execute each tool with error recovery
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
            
            # Find the matching tool (tools are now pre-created with dependencies)
            matching_tool = None
            for tool in tools:
                if getattr(tool, 'name', getattr(tool, '__name__', 'unknown_tool')) == tool_name:
                    matching_tool = tool
                    break
            
            if matching_tool:
                try:
                    # Execute tool - handle both injected tools and original StructuredTools
                    # Check for StructuredTool first (has ainvoke and is from @tool decorator)
                    if hasattr(matching_tool, 'ainvoke') and hasattr(matching_tool, '__class__') and 'StructuredTool' in str(matching_tool.__class__):
                        # Original StructuredTool - use ainvoke method
                        result = await matching_tool.ainvoke(tool_args)
                    elif hasattr(matching_tool, 'func') and callable(matching_tool.func):
                        # Injected tool (Tool.from_function wrapper) - use .func
                        result = await matching_tool.func(**tool_args)
                    else:
                        # Fallback for other tool types
                        result = await matching_tool(**tool_args)
                    tool_results.append(f"Tool {tool_name}: {result}")
                    successful_tools += 1
                    
                    # Stream tool success
                    reasoning_events.append({
                        "type": "reasoning_chunk",
                        "content": f"✅ {tool_name} completed successfully",
                        "step": "tool_success",
                        "tool_name": tool_name
                    })
                    
                except Exception as e:
                    error_msg = f"⚠️ {tool_name} had an issue but I'll continue with your request: {str(e)}"
                    log.error(f"Tool execution error for {tool_name}: {e}", exc_info=True)
                    tool_results.append(error_msg)
                    
                    # Stream tool error with recovery message
                    reasoning_events.append({
                        "type": "reasoning_chunk",
                        "content": f"⚠️ {tool_name} had an issue, but continuing",
                        "step": "tool_error",
                        "tool_name": tool_name,
                        "recovery": "continuing_with_fallback"
                    })
            else:
                error_msg = f"⚠️ {tool_name} tool is not available right now"
                tool_results.append(error_msg)
                reasoning_events.append({
                    "type": "reasoning_chunk",
                    "content": f"⚠️ {tool_name} not available",
                    "step": "tool_not_found",
                    "tool_name": tool_name
                })
        
        # ALWAYS send completion event for UI consistency
        if successful_tools > 0:
            reasoning_events.append({
                "type": "reasoning_complete",
                "content": f"🎯 Successfully completed {successful_tools}/{len(tool_calls)} tools",
                "step": "tool_execution_complete",
                "success_rate": f"{successful_tools}/{len(tool_calls)}"
            })
        else:
            reasoning_events.append({
                "type": "reasoning_complete", 
                "content": "🎯 Tool execution completed with issues - providing fallback response",
                "step": "tool_execution_complete_with_fallback"
            })
        
        # Combine tool results into final response
        final_response = "\n\n".join(tool_results) if tool_results else "I encountered some technical difficulties but I'm here to help. Please try rephrasing your request."
        
        # --- DEFINITIVE BUG FIX ---
        # The `reasoning_events` were being created but never returned.
        # This line adds the missing key to the return dictionary, which fixes the stream.
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
    
    try:
        # --- BUG FIX: Make the router more robust ---
        # 1. Isolate the user's actual query from the prepended memory context.
        #    The router only needs the user's latest message to make a decision.
        user_query = state['input']
        if "USER QUERY:" in user_query:
            user_query = user_query.split("USER QUERY:")[1].strip()

        prompt = f"""You are an expert at routing a user's request to the correct specialist.
        Based on the user's query, select the appropriate specialist from the available choices.

        User Query:
        {user_query}"""
        
        # Use a faster, cheaper model for routing
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.0) # Use 0 temp for deterministic routing
        structured_llm = llm.with_structured_output(RouteQuery)
        response = await structured_llm.ainvoke(prompt)
        
        log.info(f"Route selected: {response.datasource}")
        return {"route": response.datasource, "retry_count": 0, "critique": ""}

    except Exception as e:
        log.error(f"CRITICAL: Router node failed: {e}", exc_info=True)
        # 2. Add a fallback mechanism. If routing fails, default to general conversation.
        #    This prevents the graph from crashing silently.
        log.warning("Router failed. Defaulting to 'general_conversation' route.")
        return {"route": "general_conversation", "retry_count": 0, "critique": ""}

async def validator_node(state: AgentState):
    """Evaluates the worker's output and decides if it's sufficient."""
    log.info("--- 🕵️ VALIDATOR ---")
    
    try:
        # Get agent output and handle different formats
        agent_outcome = state.get('agent_outcome', {})
        agent_output = agent_outcome.get('output', '')
        
        # --- Provide the validator with more context to prevent false negatives ---
        tool_calls = agent_outcome.get("tool_calls", [])
        tools_used = [call["name"] for call in tool_calls] if tool_calls else ["None"]

        memory_context_summary = ""
        if "INTERNAL CONTEXT FOR AI" in state.get('input', ''):
            memory_context_summary = state['input'].split("USER QUERY:")[0]

        if hasattr(agent_output, 'content'):
            agent_output = agent_output.content
        elif not isinstance(agent_output, str):
            agent_output = str(agent_output)
        
        if not agent_output or not agent_output.strip():
            log.warning("Validator received no agent output. Forcing retry.")
            log.debug(f"Agent outcome for empty output: {agent_outcome}")
            return {"critique": "The previous attempt failed to generate a response. Please try again.", "retry_count": state.get('retry_count', 0) + 1}

        prompt = f"""You are a meticulous Quality Assurance agent. Your role is to validate the response generated by another AI agent based on the FULL context provided.

        **CONTEXT GIVEN TO THE AGENT:**
        ---
        {memory_context_summary}
        ---

        **TOOLS USED BY THE AGENT:** {', '.join(tools_used)}

        **USER'S ORIGINAL QUERY:**
        ---
        {state['input']}
        ---

        **AGENT'S GENERATED RESPONSE:**
        ---
        {agent_output}
        ---

        **YOUR TASKS (CRITICAL):**
        1.  **Check for Grounding:** The agent's response MUST be grounded in the provided context or the output of the tools it used. If the agent used tools like `enhanced_document_search`, it has access to the user's files. Do NOT flag responses as hallucinations if they are based on this external knowledge.
        2.  **Check for Correctness:** Does the response accurately and completely answer the user's query?
        3.  **Check for Quality:** Is the response well-written, professional, and free of grammatical errors?

        Based on your evaluation, decide if the response is sufficient. If not, provide a concise, actionable critique.
        """
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.5)
        structured_llm = llm.with_structured_output(Validation)
        response = await structured_llm.ainvoke(prompt)

        if response.is_sufficient:
            log.info("Validation PASSED.")
            return {"final_response": agent_output}
        else:
            log.info(f"Validation FAILED. Critique: {response.critique}")
            return {"critique": response.critique, "retry_count": state.get('retry_count', 0) + 1}

    except Exception as e:
        log.error(f"CRITICAL: Validator node failed with error: {e}", exc_info=True)
        # --- FALLBACK MECHANISM ---
        # If the validator itself fails, we must not leave the user hanging.
        # We will bypass validation and send the agent's last output directly.
        agent_outcome = state.get('agent_outcome', {})
        agent_output = agent_outcome.get('output', '')
        if hasattr(agent_output, 'content'):
            agent_output = agent_output.content
        elif not isinstance(agent_output, str):
            agent_output = str(agent_output)
        
        fallback_response = agent_output or "I'm sorry, I encountered a technical issue while processing your request. Could you please try rephrasing?"
        log.warning(f"Validator failed. Bypassing and sending fallback response.")
        return {"final_response": fallback_response}

# --- Main WebSocket Function ---

@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_active_user_ws),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    log.info(f"WebSocket connected for user: {user.id}")

    # --- Memory Manager Instantiation ---
    simple_memory = SimpleMemoryManager(db=db, user=user)
    enhanced_memory = EnhancedMemoryManager(db=db, user=user)
    advanced_memory = AdvancedMemoryManager(user=user)
    memory_tools = create_memory_tools(advanced_memory)

    # --- Tool Setup with dependency injection ---
    # Create a single lock for all resume/document modification tools
    resume_modification_lock = asyncio.Lock()

    # Define which tools need to be protected by the lock to prevent race conditions
    critical_write_tools = [
        "refine_cv_for_role",
        "generate_cover_letter",
        "create_resume_from_scratch",
        "generate_tailored_resume",
        "enhance_resume_section",
        "refine_cover_letter_from_url",
    ]

    # Create tools with pre-injected dependencies for clean LangChain compatibility
    
    profile_tool_functions = [
        update_personal_information,
        add_work_experience,
        add_education,
        set_skills,
        manage_skills_comprehensive,
        add_projects,
        add_certification,
    ]
    document_tool_functions = [
        list_documents,
        read_document,
        enhanced_document_search,
        analyze_specific_document,
    ]
    resume_cv_tool_functions = [
        create_resume_from_scratch,
        generate_tailored_resume,
        refine_cv_for_role,
        enhance_resume_section,
        generate_resume_pdf,
        show_resume_download_options,
    ]
    job_search_tool_functions = [search_jobs_linkedin_api, browse_web_with_langchain]
    career_guidance_tool_functions = [
        get_interview_preparation_guide,
        get_salary_negotiation_advice,
        create_career_development_plan,
        get_cv_best_practices,
        get_ats_optimization_tips,
        analyze_skills_gap,
    ]
    cover_letter_tool_functions = [
        generate_cover_letter,
        refine_cover_letter_from_url,
    ]

    # Create injected tools for each specialist (this is where dependencies are injected)
    log.info(f"Creating tools with dependencies for user {user.id}")
    
    profile_tools = create_tools_with_dependencies(profile_tool_functions, db, user, resume_modification_lock, critical_write_tools)
    document_tools = create_tools_with_dependencies(document_tool_functions, db, user, resume_modification_lock, critical_write_tools)
    resume_cv_tools = create_tools_with_dependencies(resume_cv_tool_functions + cover_letter_tool_functions, db, user, resume_modification_lock, critical_write_tools)
    job_search_tools = create_tools_with_dependencies(job_search_tool_functions, db, user, resume_modification_lock, critical_write_tools)
    career_guidance_tools = create_tools_with_dependencies(career_guidance_tool_functions, db, user, resume_modification_lock, critical_write_tools)

    # --- Worker Definitions ---
    # Load the specific prompt for the conversational agent
    general_prompt = load_prompt_from_file("general_conversation_prompt.txt") or "You are a helpful assistant."

    # Create agent and tool nodes for each specialist
    agent_nodes = {}
    tool_nodes = {}
    
    specialist_configs = {
        "profile_management": (profile_tools, MAIN_SYSTEM_PROMPT),
        "document_interaction": (document_tools, MAIN_SYSTEM_PROMPT),
        "resume_cv": (resume_cv_tools, MAIN_SYSTEM_PROMPT),
        "job_search": (job_search_tools, MAIN_SYSTEM_PROMPT),
        "career_guidance": (career_guidance_tools, MAIN_SYSTEM_PROMPT),
        "general_conversation": ([], general_prompt),
    }
    
    for route_name, (tools, system_prompt) in specialist_configs.items():
        agent_nodes[route_name] = create_agent_node(tools, system_prompt)
        tool_nodes[route_name] = create_tool_node(tools)
        log.info(f"Created {route_name} specialist with {len(tools)} tools")

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
    # DEPRECATING: The EnhancedMemoryManager is now part of the unified context.
    # memory_manager = EnhancedMemoryManager(db, user)
    
    # This outer try/except is for connection-level errors (e.g., the client disconnects)
    try:
        while True:
            # Receive message - this should be outside inner try/catch to properly handle WebSocket disconnects
            data = await websocket.receive_text()
            
            # --- Inner try/except for message-level errors ---
            # This ensures that an error processing one message does not kill the entire connection.
            try:
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError as e:
                    log.error(f"Invalid JSON received from user {user.id}: {data[:100]}")
                    await websocket.send_json({"type": "error", "message": "Invalid message format."})
                    continue
                message_type = message_data.get("type")
                message_content = message_data.get("content")
                page_id = message_data.get("page_id")

                # Handle different message types
                if message_type == "switch_page":
                    log.info(f"User {user.id} switched to page: {page_id}")
                    continue
                elif message_type == "stop_generation":
                    log.info(f"User {user.id} requested to stop generation")
                    continue
                elif message_type == "clear_context":
                    log.info(f"User {user.id} cleared context")
                    continue

                # 1. Validate incoming user message (for regular chat messages)
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

                # Save user message with robust transaction handling
                try:
                    user_message_id = str(uuid.uuid4())
                    db.add(ChatMessage(id=user_message_id, user_id=user.id, page_id=page_id, message=message_content, is_user_message=True))
                    await db.commit()
                    log.info(f"Saved user message {user_message_id} to DB.")
                except Exception as db_error:
                    log.error(f"Failed to save user message to database for user {user.id}, page {page_id}: {db_error}", exc_info=True)
                    await db.rollback()
                    await websocket.send_json({
                        "type": "error", 
                        "message": "A database error occurred while saving your message. Please try again."
                    })
                    continue
                
                # Sanitize the user message for PII before memory processing.
                sanitized_message_content = _redact_pii(message_content)

                # 1. Get unified context summary from all memory managers.
                context_summary = await _get_unified_context_summary(
                    simple_memory, enhanced_memory, advanced_memory, sanitized_message_content, page_id
                )

                # 2. Get recent chat history from simple memory.
                simple_context = await simple_memory.get_conversation_context(page_id=page_id, limit=20)
                chat_history = [
                    HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]) 
                    for msg in simple_context.conversation_history
                ]

                # 3. Prepare input for the agent graph, prepending the context to the user message.
                final_input = message_content
                if context_summary:
                    final_input = f"{context_summary}\n\nUSER QUERY:\n{message_content}"

                initial_state = {
                    "input": final_input, 
                    "chat_history": chat_history,
                }
                
                # Invoke Graph and stream intermediate steps
                final_response = None # Start with None
                async for event in graph.astream(initial_state):
                    # --- DEFINITIVE BUG FIX ---
                    # This new, corrected logic properly handles the LangGraph event stream.
                    # It streams reasoning events from intermediate nodes and captures the
                    # final response ONLY from the designated END node.
                    log.debug(f"--- Graph Stream Event ---")
                    log.debug(f"Event Keys: {list(event.keys())}")

                    # The event dictionary has one key, which is the name of the node that just ran.
                    node_name = list(event.keys())[0]
                    node_data = event[node_name]
                    log.debug(f"Node '{node_name}' finished with data.")

                    # Check if this node's output contains reasoning events and stream them.
                    if isinstance(node_data, dict) and "reasoning_events" in node_data:
                        log.info(f"Streaming {len(node_data['reasoning_events'])} reasoning events from node '{node_name}'")
                        for reasoning_event in node_data["reasoning_events"]:
                            await websocket.send_json({
                                "type": reasoning_event["type"],
                                "data": reasoning_event,
                                "timestamp": datetime.now().isoformat()
                            })
                    
                    # The final response is only available at the very end of the stream.
                    if END in event:
                        final_response_data = event[END]
                        if isinstance(final_response_data, dict) and "final_response" in final_response_data:
                            final_response = final_response_data["final_response"]
                            log.info(f"Captured final response from END node: {final_response[:100]}...")

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
                
                # --- THE CORRECT FIX ---
                # Save the AI message using a NEW, FRESH database session.
                # This prevents errors from the original, potentially stale session
                # that was held open during the long-running agent process.
                try:
                    async with SessionLocal() as fresh_db:
                        ai_message_id = str(uuid.uuid4())
                        ai_message_to_save = ChatMessage(
                            id=ai_message_id, 
                            user_id=user.id, 
                            page_id=page_id, 
                            message=final_response, # Uses the correct 'message' column
                            is_user_message=False
                        )
                        fresh_db.add(ai_message_to_save)
                        await fresh_db.commit()
                        log.info(f"Saved AI message {ai_message_id} to DB with fresh session.")
                except Exception as db_error:
                    log.error(f"Failed to save AI message to database for user {user.id}, page {page_id}: {db_error}", exc_info=True)
                    # The 'async with' block handles rollback automatically.
                    # We don't need to send another WebSocket error here, as the user has already received the response.

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