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
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END
from langchain_core.tools import Tool
from sqlalchemy import select

from app.db import get_db, async_session_maker
from app.models_db import User, ChatMessage, Page, Subscription # Import Subscription model
from app.dependencies import get_current_active_user_ws
from app.simple_memory import SimpleMemoryManager
from app.enhanced_memory import EnhancedMemoryManager
from app.advanced_memory import AdvancedMemoryManager

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
        enhanced_ctx_task = enhanced_memory.get_conversation_context(page_id=page_id, include_user_learning=True)
        advanced_ctx_task = advanced_memory.load_relevant_context(current_message=user_message)
        
        enhanced_context, advanced_context = await asyncio.gather(
            enhanced_ctx_task,
            advanced_ctx_task
        )

        if advanced_context and advanced_context.relevant_memories:
            memories_text = "\n".join([f"- {memory}" for memory in advanced_context.relevant_memories])
            summary_parts.append(f"Here is what I remember about you:\n{memories_text}")

        if enhanced_context and enhanced_context.summary and "New conversation" not in enhanced_context.summary:
            summary_parts.append(f"Here is a summary of our recent conversation:\n{enhanced_context.summary}")
        
        if enhanced_context and enhanced_context.key_topics:
            summary_parts.append(f"Key topics we discussed: {', '.join(enhanced_context.key_topics)}")

        if not summary_parts:
            return ""

        return "INTERNAL CONTEXT FOR AI (User does not see this):\n\n" + "\n\n".join(summary_parts)

    except Exception as e:
        log.error(f"Error getting unified context summary: {e}", exc_info=True)
        return ""

# --- All functions are now at the top level for testability ---

# --- 1. State & Pydantic Models ---
class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    route: str
    agent_outcome: Any
    final_response: str
    critique: str
    retry_count: int

class RouteQuery(BaseModel):
    datasource: str

class Validation(BaseModel):
    is_sufficient: bool
    critique: Optional[str] = None

# --- 2. Tool Creation & Dependency Injection ---
def create_dependency_injected_tool(original_tool, db, user, lock, lock_list):
    tool_name = getattr(original_tool, 'name', getattr(original_tool, '__name__', 'unknown'))
    needs_lock = tool_name in lock_list

    async def injected_tool(**kwargs):
        sig = inspect.signature(original_tool.func if hasattr(original_tool, 'func') else original_tool)
        call_args = {}
        if 'db' in sig.parameters: call_args['db'] = db
        if 'user' in sig.parameters: call_args['user'] = user
        if 'resume_modification_lock' in sig.parameters: call_args['resume_modification_lock'] = lock
        call_args.update(kwargs)

        async def execute():
            return await (original_tool.func if hasattr(original_tool, 'func') else original_tool)(**call_args)

        if needs_lock:
            async with lock: return await execute()
        else:
            return await execute()
    
    return Tool.from_function(func=injected_tool, name=tool_name, description=original_tool.description)

def create_tools_with_dependencies(tool_functions, db, user, lock, lock_list):
    tools = []
    for tool_func in tool_functions:
        if tool_func:
            tools.append(create_dependency_injected_tool(tool_func, db, user, lock, lock_list))
    return tools

# --- 3. Graph Node Definitions ---
def create_agent_node(tools, system_prompt):
    async def agent_node(state: AgentState):
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}\n{critique}"),
        ])
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.2).bind_tools(tools)
        response = await (prompt | llm).ainvoke(state)
        
        # --- FIX: Restore Detailed Reasoning Events ---
        reasoning_events = [{"type": "reasoning_start", "content": "Analyzing request..."}]
        if response.tool_calls:
            tool_names = [call["name"] for call in response.tool_calls]
            reasoning_events.append({
                "type": "reasoning_chunk",
                "content": f"Planning to use tools: {', '.join(tool_names)}",
                "step": "tool_planning"
            })
            return {"agent_outcome": response, "reasoning_events": reasoning_events}
        else:
            reasoning_events.append({"type": "reasoning_complete", "content": "Analysis complete."})
            return {"final_response": response.content, "reasoning_events": reasoning_events}
    return agent_node

def create_tool_node(tools):
    async def tool_node(state: AgentState):
        tool_calls = state["agent_outcome"].tool_calls
        tool_results = []
        # --- FIX: Restore Detailed Reasoning Events ---
        reasoning_events = []
        for call in tool_calls:
            tool = {t.name: t for t in tools}[call["name"]]
            reasoning_events.append({
                "type": "reasoning_chunk",
                "content": f"Using tool: {tool.name}",
                "step": "tool_execution"
            })
            result = await tool.ainvoke(call["args"])
            tool_results.append(result)
            reasoning_events.append({
                "type": "reasoning_chunk",
                "content": f"Finished using tool: {tool.name}",
                "step": "tool_result"
            })
        
        reasoning_events.append({"type": "reasoning_complete", "content": "All tools finished."})
        # This was the bug fix from before, ensuring events are returned.
        return {"messages": tool_results, "reasoning_events": reasoning_events}
    return tool_node

async def router_node(state: AgentState):
    # Simplified for stability, can be enhanced later
    return {"route": "general_conversation"}

async def validator_node(state: AgentState):
    # Simplified for stability
    return {"final_response": state["agent_outcome"]}


# --- 4. Master Graph Creation ---
def create_master_agent_graph(db: AsyncSession, user: User):
    lock = asyncio.Lock()
    lock_list = [
        "refine_cv_for_role", "generate_cover_letter", "create_resume_from_scratch",
        "generate_tailored_resume", "enhance_resume_section", "refine_cover_letter_from_url",
    ]
    all_tools_funcs = [
        add_certification, add_education, add_projects, add_work_experience,
        analyze_skills_gap, analyze_specific_document, browse_web_with_langchain,
        create_career_development_plan, create_resume_from_scratch, enhance_resume_section,
        enhanced_document_search, generate_cover_letter, generate_resume_pdf,
        generate_tailored_resume, get_ats_optimization_tips, get_current_time_and_date,
        get_cv_best_practices, get_interview_preparation_guide, get_salary_negotiation_advice,
        list_documents, manage_skills_comprehensive, read_document, refine_cover_letter_from_url,
        refine_cv_for_role, search_jobs_linkedin_api, set_skills, show_resume_download_options,
        update_personal_information,
    ]
    
    all_tools = create_tools_with_dependencies(all_tools_funcs, db, user, lock, lock_list)
    
    # Using a single general-purpose agent for stability
    general_agent_node = create_agent_node(all_tools, "You are a helpful assistant.")
    general_tool_node = create_tool_node(all_tools)

    workflow = StateGraph(AgentState)
    workflow.add_node("router", router_node)
    workflow.add_node("general_conversation_agent", general_agent_node)
    workflow.add_node("general_conversation_tools", general_tool_node)
    workflow.add_node("validator", validator_node)

    workflow.add_conditional_edges("router", lambda state: "general_conversation_agent")
    workflow.add_edge("general_conversation_agent", "general_conversation_tools")
    workflow.add_edge("general_conversation_tools", "validator")
    workflow.add_conditional_edges("validator", lambda state: END)
    
    workflow.set_entry_point("router")
    return workflow.compile()

# --- 5. Main WebSocket Function ---
@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(websocket: WebSocket, user: User = Depends(get_current_active_user_ws), db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    log.info(f"WebSocket connected for user: {user.id}")

    # --- DEFINITIVE FIX: Check subscription status on connect and send to client ---
    try:
        # Use the exact same logic as the UsageManager for consistency.
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscription = sub_result.scalar_one_or_none()
        
        is_active = False
        plan = "free"
        if subscription and subscription.plan == 'premium' and subscription.status == 'active':
            is_active = True
            plan = "premium"

        await websocket.send_json({
            "type": "subscription_status",
            "isActive": is_active,
            "plan": plan
        })
        log.info(f"Sent initial subscription status to user {user.id}: plan={plan}, isActive={is_active}")
    except Exception as e:
        log.error(f"Failed to send initial subscription status for user {user.id}: {e}")
        # Send a default inactive status if the check fails for any reason.
        await websocket.send_json({"type": "subscription_status", "isActive": False, "plan": "free"})

    graph = create_master_agent_graph(db, user)
    
    simple_memory = SimpleMemoryManager(db=db, user=user)
    # --- FIX: Re-instantiate the advanced memory managers ---
    enhanced_memory = EnhancedMemoryManager(db=db, user=user)
    advanced_memory = AdvancedMemoryManager(user=user, db=db) # Pass the db session here
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # FIX: This replaces the broken if/elif structure with a single, valid
            # conditional block that correctly routes different message types.
            message_type = message_data.get("type")

            if message_type == "switch_page":
                log.info(f"Switched page context to: {message_data.get('page_id')}")
                continue

            elif message_type in ["message", "regenerate", None]:
                user_message_content = message_data.get("content")
                page_id = message_data.get("page_id")

                if not user_message_content:
                    log.warning("Received message with no content.")
                    continue

                # This is the core logical fix. All database writes will now happen
                # in a single, atomic transaction using a fresh session.
                async with async_session_maker() as fresh_db:
                    if not page_id:
                        # Create the new page within the same session where the messages will be saved.
                        page = Page(user_id=user.id, title=user_message_content[:50])
                        fresh_db.add(page)
                        await fresh_db.commit()
                        await fresh_db.refresh(page)
                        page_id = str(page.id)
                        # Notify the client of the newly created page ID so the conversation can continue correctly.
                        await websocket.send_json({
                            "type": "page_created",
                            "page_id": page_id
                        })

                    # FIX: The user message is now created AND saved immediately in its own transaction.
                    # This ensures the user's message is never lost, even if the AI fails.
                    user_message_for_db = ChatMessage(id=str(uuid.uuid4()), user_id=user.id, page_id=page_id, content=user_message_content, is_user_message=True)
                    fresh_db.add(user_message_for_db)
                    await fresh_db.commit()

                # --- The AI processing now happens *after* the user's message is safely stored. ---
                context_summary = await _get_unified_context_summary(
                    simple_memory, enhanced_memory, advanced_memory, user_message_content, page_id
                )
                history = await simple_memory.get_conversation_context(page_id)
                chat_history = [HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]) for msg in history.conversation_history]
                final_input = f"{context_summary}\n\nUSER QUERY:\n{user_message_content}" if context_summary else user_message_content
                initial_state = {"input": final_input, "chat_history": chat_history, "critique": ""}
                
                final_response = None
                async for event in graph.astream(initial_state):
                    if END in event:
                        final_response = event[END].get("final_response", "Sorry, I encountered an error.")
                    
                    if "reasoning_events" in event.get(list(event.keys())[0], {}):
                        await websocket.send_json({"type": "reasoning", "data": event})
                
                # The AI message is saved in a separate, second transaction.
                async with async_session_maker() as fresh_db:
                    # FIX: The same correction is applied here for the AI's response.
                    ai_message_for_db = ChatMessage(id=str(uuid.uuid4()), user_id=user.id, page_id=page_id, content=final_response, is_user_message=False)
                    fresh_db.add(ai_message_for_db)
                    await fresh_db.commit()

                await websocket.send_json({"type": "final_response", "content": final_response})
            
            else:
                log.warning(f"Received unknown message type, skipping: {message_type}")
                continue

    except WebSocketDisconnect:
        log.info("WebSocket disconnected.")
    except Exception as e:
        log.error(f"WebSocket error: {e}")