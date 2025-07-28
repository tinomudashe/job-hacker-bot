import os
import logging
import uuid
import json
import asyncio
from pathlib import Path
from typing import List, Literal, Optional, Any, Dict, TypedDict

from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.db import get_db, async_session_maker
from app.models_db import User, ChatMessage, Page, Subscription
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
from .orchestrator_tools.extract_and_populate_profile_from_document import extract_and_populate_profile_from_documents
from .orchestrator_tools.generate_cover_letter import generate_cover_letter
from .orchestrator_tools.generate_resume_pdf import generate_resume_pdf
from .orchestrator_tools.generate_tailored_resume import generate_tailored_resume
from .orchestrator_tools.get_ats_optimization_tips import get_ats_optimization_tips
from .orchestrator_tools.get_authenticated_user_data import get_authenticated_user_data
from .orchestrator_tools.get_current_time_and_date import get_current_time_and_date
from .orchestrator_tools.get_cv_best_practices import get_cv_best_practices
from .orchestrator_tools.get_interview_preparation_guide import get_interview_preparation_guide
from .orchestrator_tools.get_salary_negotiation_advice import get_salary_negotiation_advice
from .orchestrator_tools.get_user_location_context import get_user_location_context
from .orchestrator_tools.list_documents import list_documents
from .orchestrator_tools.manage_skills_comprehensive import manage_skills_comprehensive
from .orchestrator_tools.read_document import read_document
from .orchestrator_tools.refine_cover_letter_from_url import refine_cover_letter_from_url
from .orchestrator_tools.refine_cv_for_role import refine_cv_for_role
from .orchestrator_tools.refine_cv_from_url import refine_cv_from_url
from .orchestrator_tools.search_jobs_linkedin_api import search_jobs_linkedin_api
from .orchestrator_tools.search_jobs_tool import search_jobs_tool
from .orchestrator_tools.search_web_for_advice import search_web_for_advice
from .orchestrator_tools.set_skills import set_skills
from .orchestrator_tools.show_resume_download_options import show_resume_download_options
from .orchestrator_tools.update_personal_information import update_personal_information
from .orchestrator_tools.update_user_profile import update_user_profile
from .orchestrator_tools.update_user_profile_comprehensive import update_user_profile_comprehensive


load_dotenv()
log = logging.getLogger(__name__)
router = APIRouter()

# --- 1. State Definition ---
# This is the new, simplified state for our graph.
# It aligns with LangGraph's standard `tools_condition` and `ToolNode`.
class AgentState(TypedDict):
    messages: List[BaseMessage]

# --- 2. Dependency Injection with RunnableLambda ---
def create_tool_runnable(tool, db: AsyncSession, user: User, websocket: WebSocket):
    """
    Creates a RunnableLambda that injects dependencies into a tool's underlying function.
    This is the modern, robust way to handle dependency injection in LangChain.
    """
    async def tool_with_deps(tool_input: dict):
        # We can now safely inject dependencies because we control the execution context.
        injected_kwargs = {'db': db, 'user': user}
        # Some tools might need the websocket for sending real-time updates.
        if "websocket" in tool.func.__code__.co_varnames:
            injected_kwargs['websocket'] = websocket
        
        return await tool.func(**tool_input, **injected_kwargs)

    return RunnableLambda(tool_with_deps)

# --- 3. Graph Node Definitions ---
def create_agent_node(llm, tools, system_prompt: str):
    """
    This node represents the "brain" of our agent. It decides what to do next.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | llm.bind_tools(tools)

# --- 4. Graph Creation ---
def create_master_agent_graph(db: AsyncSession, user: User, websocket: WebSocket, system_prompt: str):
    """
    Creates the main agent graph with proper dependency injection and prebuilt nodes.
    """
    # Define all the tools the agent can use.
    all_tools = [
        add_certification, add_education, add_projects, add_work_experience, analyze_skills_gap,
        analyze_specific_document, browse_web_with_langchain, create_career_development_plan,
        create_resume_from_scratch, enhance_resume_section, enhanced_document_search,
        extract_and_populate_profile_from_documents, generate_cover_letter, generate_resume_pdf,
        generate_tailored_resume, get_ats_optimization_tips, get_authenticated_user_data,
        get_current_time_and_date, get_cv_best_practices, get_interview_preparation_guide,
        get_salary_negotiation_advice, get_user_location_context, list_documents,
        manage_skills_comprehensive, read_document, refine_cover_letter_from_url,
        refine_cv_for_role, refine_cv_from_url, search_jobs_linkedin_api, search_jobs_tool,
        search_web_for_advice, set_skills, show_resume_download_options, update_personal_information,
        update_user_profile, update_user_profile_comprehensive
    ]

    # Use the RunnableLambda injector to prepare tools for the ToolNode.
    # We are no longer modifying the tools themselves, just how they are called.
    runnable_tools = [create_tool_runnable(tool, db, user, websocket) for tool in all_tools]
    tool_node = ToolNode(runnable_tools)

    # Define the LLM for the agent node.
    # Using the user-preferred Gemini Pro model [[memory:4475666]]
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.2)
    agent_node = create_agent_node(llm, all_tools, system_prompt)

    # Define the graph structure.
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    # Set the entry point and the conditional edges.
    workflow.set_entry_point("agent")
    # This prebuilt condition checks if the agent's last message contains tool calls.
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        # If it does, we call the tools. Otherwise, we end the graph.
        {"tools": "tools", END: END},
    )
    # After calling the tools, the results are always passed back to the agent.
    workflow.add_edge("tools", "agent")

    return workflow.compile()

# --- 5. Helper Functions for Prompts and Context ---
def load_system_prompt(prompt_type: str = "system") -> str:
    """Loads the specified system prompt from the text file."""
    prompt_file_map = {"system": "system_prompt.txt", "general": "general_conversation_prompt.txt"}
    filename = prompt_file_map.get(prompt_type, "system_prompt.txt")
    try:
        prompt_path = Path(__file__).parent / "orchestrator_prompts" / filename
        return prompt_path.read_text()
    except FileNotFoundError:
        log.error(f"PROMPT FILE '{filename}' NOT FOUND. Using a basic fallback prompt.")
        return "You are a helpful assistant."

async def get_prompt_for_input(user_input: str, history: List[Dict]) -> str:
    """Dynamically selects the appropriate system prompt based on user intent."""
    if not history and len(user_input) < 20: return load_system_prompt("general")
    try:
        # For utility tasks, we use the faster Gemini Flash model [[memory:4540099]]
        classifier_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
        class Intent(BaseModel):
            intent: Literal["task_request", "general_conversation"]
        chain = ChatPromptTemplate.from_messages([
            ("system", "Classify user intent: 'task_request' for specific actions (e.g., search jobs) or 'general_conversation' for chat."),
            ("user", "{input}")
        ]) | classifier_llm.with_structured_output(Intent)
        result = await chain.ainvoke({"input": user_input})
        prompt_type = "general" if result.intent == "general_conversation" else "system"
        log.info(f"Classified intent as '{result.intent}'. Using '{prompt_type}' prompt.")
        return load_system_prompt(prompt_type)
    except Exception as e:
        log.error(f"Intent classification failed: {e}. Defaulting to main system prompt.")
        return load_system_prompt("system")

async def _get_memory_context_for_prompt(
    db: AsyncSession, user: User, user_message: str, page_id: Optional[str]
) -> str:
    """
    Fetches context from all memory managers to create a unified summary for the system prompt.
    This provides the agent with long-term memory and context.
    """
    try:
        # Instantiate memory managers for this specific task.
        enhanced_memory = EnhancedMemoryManager(db=db, user=user)
        advanced_memory = AdvancedMemoryManager(user=user, db=db)
        
        # Fetch contexts concurrently.
        enhanced_ctx_task = enhanced_memory.get_conversation_context(page_id=page_id, include_user_learning=True)
        advanced_ctx_task = advanced_memory.load_relevant_context(current_message=user_message)
        
        enhanced_context, advanced_context = await asyncio.gather(enhanced_ctx_task, advanced_ctx_task)

        summary_parts = []
        if advanced_context and advanced_context.relevant_memories:
            memories_text = "\n".join([f"- {memory}" for memory in advanced_context.relevant_memories])
            summary_parts.append(f"Here is what I remember about our past interactions:\n{memories_text}")

        if enhanced_context and enhanced_context.summary and "New conversation" not in enhanced_context.summary:
            summary_parts.append(f"Here is a summary of our current conversation:\n{enhanced_context.summary}")
        
        if not summary_parts:
            return ""

        # This context is prepended to the main system prompt.
        return "--- INTERNAL CONTEXT (FOR AI USE ONLY) ---\n" + "\n\n".join(summary_parts) + "\n--- END INTERNAL CONTEXT ---"

    except Exception as e:
        log.error(f"Error getting memory context for prompt: {e}", exc_info=True)
        return ""


# --- 6. Main WebSocket Function ---
@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(websocket: WebSocket, user: User = Depends(get_current_active_user_ws), db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    log.info(f"WebSocket connected for user: {user.id}")
    
    simple_memory = SimpleMemoryManager(db=db, user=user)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_type = message_data.get("type")

            if message_type != "message": continue

            user_message_content = message_data.get("content")
            page_id = message_data.get("page_id")

            if not user_message_content: continue

            async with async_session_maker() as fresh_db:
                if not page_id:
                    page = Page(user_id=user.id, title=user_message_content[:50])
                    fresh_db.add(page)
                    await fresh_db.commit()
                    await fresh_db.refresh(page)
                    page_id = str(page.id)
                    await websocket.send_json({"type": "page_created", "page_id": page_id})

                user_message_for_db = ChatMessage(id=str(uuid.uuid4()), user_id=user.id, page_id=page_id, message=user_message_content, is_user_message=True)
                fresh_db.add(user_message_for_db)
                await fresh_db.commit()

            history_for_prompt = await simple_memory.get_conversation_context(page_id)
            base_system_prompt = await get_prompt_for_input(user_message_content, history_for_prompt.conversation_history)
            
            # Here is the reintegration:
            memory_context = await _get_memory_context_for_prompt(db, user, user_message_content, page_id)
            final_system_prompt = f"{memory_context}\n\n{base_system_prompt}"

            # Recreate the graph for each message to ensure it has the latest dependencies and the complete prompt.
            graph = create_master_agent_graph(db, user, websocket, final_system_prompt)
            
            history = await simple_memory.get_conversation_context(page_id)
            chat_history = [HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]) for msg in history.conversation_history]
            
            initial_state = {"messages": chat_history}

            final_response = "I'm sorry, an error occurred."
            try:
                # We now stream events from the graph.
                async for event in graph.astream(initial_state):
                    # The final response is the last AI message in the 'agent' node's output.
                    if "agent" in event and isinstance(event["agent"], AIMessage):
                        final_response_message = event["agent"]
                        if not final_response_message.tool_calls:
                            final_response = final_response_message.content
            except Exception as graph_error:
                log.error(f"Error during graph execution for user {user.id}: {graph_error}", exc_info=True)
            
            async with async_session_maker() as fresh_db:
                ai_message_for_db = ChatMessage(id=str(uuid.uuid4()), user_id=user.id, page_id=page_id, message=final_response, is_user_message=False)
                fresh_db.add(ai_message_for_db)
                await fresh_db.commit()

            await websocket.send_json({"type": "final_response", "content": final_response})

    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected for user: {user.id}")
    except Exception as e:
        log.error(f"WebSocket error for user {user.id}: {e}", exc_info=True)