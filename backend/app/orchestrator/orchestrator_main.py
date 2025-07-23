import os
import logging
from functools import partial
import uuid
import json
from pathlib import Path
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
from .orchestrator_tools.show_resume_download_option import show_resume_download_option
from .orchestrator_tools.update_personal_information import update_personal_information

load_dotenv()
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter()

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

def create_worker(tools: list, system_prompt: str):
    """Helper function to create a specialist agent executor."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}\n{critique}"), # Add critique to the prompt for refinement
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    # Use a faster model for specialists if desired, for now use pro
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.2)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

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
    prompt = f"""You are a meticulous Quality Assurance agent. Your role is to validate the response generated by another AI agent.

    User's Original Query:
    {state['input']}

    Agent's Generated Response:
    {state['agent_outcome'].return_values['output']}

    Your Tasks:
    1.  **Check for Correctness**: Does the response accurately and completely answer the user's query?
    2.  **Check for Quality**: Is the response well-written, professional, and free of grammatical errors?
    3.  **Check for Hallucinations**: Does the agent claim to have done something it cannot do? (e.g., "I've emailed you the resume" - it cannot email).
    4.  **Database Action Verification (Future)**: For now, assume tools worked unless the agent reports an error.

    Based on your evaluation, decide if the response is sufficient. If not, provide a concise, actionable critique for the agent to use on its next attempt.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.0)
    structured_llm = llm.with_structured_output(Validation)
    response = await structured_llm.ainvoke(prompt)

    if response.is_sufficient:
        log.info("Validation PASSED.")
        return {"final_response": state['agent_outcome'].return_values['output']}
    else:
        log.info(f"Validation FAILED. Critique: {response.critique}")
        return {"critique": response.critique, "retry_count": state['retry_count'] + 1}

# --- Main WebSocket Function ---

@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_active_user_ws),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    log.info(f"WebSocket connected for user: {user.id}")

    # --- Tool Definitions and Dependency Injection ---
    profile_tools = [
        partial(update_personal_information, db=db, user=user),
        partial(add_work_experience, db=db, user=user),
        partial(add_education, db=db, user=user),
        partial(set_skills, db=db, user=user),
        partial(manage_skills_comprehensive, db=db, user=user),
        partial(add_projects, db=db, user=user),
        partial(add_certification, db=db, user=user),
    ]
    document_tools = [
        partial(list_documents, db=db, user=user),
        partial(read_document, db=db, user=user),
        partial(enhanced_document_search, db=db, user=user),
        partial(analyze_specific_document, db=db, user=user),
    ]
    resume_cv_tools = [
        partial(create_resume_from_scratch, db=db, user=user),
        partial(generate_tailored_resume, db=db, user=user),
        partial(refine_cv_for_role, db=db, user=user),
        partial(enhance_resume_section, db=db, user=user),
        partial(generate_resume_pdf, db=db, user=user),
        partial(show_resume_download_option, db=db, user=user),
    ]
    job_search_tools = [search_jobs_linkedin_api, browse_web_with_langchain]
    career_guidance_tools = [
        get_interview_preparation_guide,
        get_salary_negotiation_advice,
        create_career_development_plan,
        get_cv_best_practices,
        get_ats_optimization_tips,
        partial(analyze_skills_gap, db=db, user=user),
    ]
    cover_letter_tools = [
        partial(generate_cover_letter, db=db, user=user),
        partial(refine_cover_letter_from_url, db=db, user=user),
    ]

    # --- Worker Definitions ---
    workers = {
        "profile_management": create_worker(profile_tools, "You are a specialist in managing user profile and resume data. Use the provided tools to add, update, or modify the user's information."),
        "document_interaction": create_worker(document_tools, "You are a specialist in interacting with user-uploaded documents. Use your tools to list, read, and search through documents."),
        "resume_cv": create_worker(resume_cv_tools, "You are an expert resume and CV writer. Use your tools to create, refine, and generate resumes."),
        "job_search": create_worker(job_search_tools, "You are a job search specialist. Use your tools to find job opportunities online."),
        "career_guidance": create_worker(career_guidance_tools, "You are a career coach. Provide advice and guidance using your tools."),
        "general_conversation": create_worker([], "You are a helpful assistant. Respond to the user directly for general conversation, greetings, or questions where no specific tool is needed."),
    }

    # --- Graph Construction ---
    workflow = StateGraph(AgentState)
    workflow.add_node("router", router_node)

    for route_name, worker_executor in workers.items():
        workflow.add_node(route_name, worker_executor)
        workflow.add_edge(route_name, "validator")
    
    workflow.add_node("validator", validator_node)

    def route_to_worker(state: AgentState):
        return state["route"]

    workflow.add_conditional_edges("router", route_to_worker)

    def check_validation(state: AgentState):
        if state.get("final_response"):
            return END
        if state["retry_count"] >= 2:
            log.warning("Max retries reached. Exiting graph.")
            return END
        return state["route"] # Loop back to the correct worker

    workflow.add_conditional_edges("validator", check_validation)
    workflow.set_entry_point("router")
    graph = workflow.compile()
    
    # --- Main WebSocket Loop ---
    try:
        memory_manager = EnhancedMemoryManager(db, user)
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_content = message_data.get("content")
            page_id = message_data.get("page_id")

            if not page_id:
                # Create a new page if one doesn't exist
                # (Simplified for brevity)
                new_page = Page(user_id=user.id, title=message_content[:50])
                db.add(new_page)
                await db.commit()
                page_id = new_page.id
                await websocket.send_json({"type": "page_created", "page_id": page_id, "title": new_page.title})

            # Save user message
            db.add(ChatMessage(id=str(uuid.uuid4()), user_id=user.id, page_id=page_id, message=message_content, is_user_message=True))
            await db.commit()
            
            # Load history
            context = await memory_manager.get_conversation_context(page_id)
            chat_history = [HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]) for msg in context.recent_messages]

            initial_state = {"input": message_content, "chat_history": chat_history}
            
            # Invoke Graph and stream intermediate steps
            final_response = "I'm sorry, I encountered an issue and couldn't complete your request." # Default error message
            async for event in graph.astream(initial_state):
                if "router" in event:
                    await websocket.send_json({"type": "info", "message": f"Routing to {event['router']['route']} specialist..."})
                if "validator" in event:
                    if event['validator'].get('critique'):
                        await websocket.send_json({"type": "info", "message": f"Refining response... Critique: {event['validator']['critique']}"})
                    else:
                        await websocket.send_json({"type": "info", "message": "Validating response..."})
                if END in event:
                    final_response = event[END].get("final_response") or "I was unable to finalize a response."

            # Send final response
            await websocket.send_json({"type": "message", "message": final_response})
            
            # Save AI message
            db.add(ChatMessage(id=str(uuid.uuid4()), user_id=user.id, page_id=page_id, message=final_response, is_user_message=False))
            await db.commit()

    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        log.error(f"WebSocket error for user {user.id}: {e}", exc_info=True)