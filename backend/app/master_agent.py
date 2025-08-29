"""
MASTER AGENT - LangGraph Compatible Enhancement
System prompts + user context + LLM configuration for LangGraph conversation node
Simplified from AgentExecutor pattern to pure conversation logic
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# LangGraph and LangChain imports
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Import LangGraph state for integration
from app.orchestrator import WebSocketState

log = logging.getLogger(__name__)

# ============================================================================
# 1. ENHANCED SYSTEM PROMPT CREATION (ADAPTED FOR LANGGRAPH)
# ============================================================================

def create_enhanced_system_prompt(user_name: str, user_context: Dict[str, Any]) -> str:
    """
    Create an enhanced system prompt with user context for LangGraph conversation node
    Adapted from the original but optimized for node-based architecture
    """
    
    context_parts = [
        f"## 👤 USER: {user_name}",
        "",
        "### 📊 Profile Information:"
    ]
    
    # Add user context information
    if user_context.get("location"):
        context_parts.append(f"📍 Location: {user_context['location']}")
    
    if user_context.get("current_role"):
        context_parts.append(f"💼 Current Role: {user_context['current_role']}")
    
    if user_context.get("skills"):
        skills_preview = ", ".join(user_context["skills"][:5])
        context_parts.append(f"🛠️ Key Skills: {skills_preview}")
    
    if user_context.get("experience_count"):
        context_parts.append(f"📋 Work Experience: {user_context['experience_count']} positions")
    
    if user_context.get("documents_count"):
        context_parts.append(f"📄 Documents: {user_context['documents_count']} files uploaded")
    
    # Add current time context
    if user_context.get("current_time"):
        context_parts.append(f"🕐 Current Time: {user_context['current_time']}")
    
    context_text = "\n".join(context_parts)
    
    return f"""{context_text}

## 🎯 YOUR CORE PURPOSE - LANGGRAPH CONVERSATION NODE
You are Job Hacker Bot, operating as the conversation node in a LangGraph workflow.
Your role is to understand user requests and generate appropriate tool calls or responses.

Help users with:
- CV/Resume creation and optimization
- Cover letter generation  
- Job searching and applications
- Career development and interview preparation
- Profile management and document analysis
- Professional email writing and follow-ups

## ✅ CRITICAL RULES FOR LANGGRAPH OPERATION

### 1. TOOL USAGE (MANDATORY)
- **ALWAYS USE TOOLS** when the user requests specific actions
- **NEVER SAY YOU WILL** - Actually generate tool calls immediately

**DISTINGUISHING EMAIL vs COVER LETTER (CRITICAL)**:
- "email" or "send email" or "write email" → **CALL generate_professional_email**
- "cover letter" → **CALL generate_cover_letter or generate_cover_letter_from_url**
- **IMPORTANT**: Email and Cover Letter are DIFFERENT:
  - Email = Short message to send/submit application
  - Cover Letter = Full document to attach with resume
- If user says "email for job" → Use generate_professional_email
- If user says "cover letter for job" → Use generate_cover_letter

**COVER LETTER REQUESTS**:
- Words that trigger: "cover letter", "application letter", "motivation letter"
- With URL → Call generate_cover_letter_from_url
- Without URL → Call generate_cover_letter

**CV/RESUME REQUESTS**:
- "Review my resume" or "Check my CV" or "ATS review" → **CALL review_resume_ats**
- "Review my resume for ATS" → **CALL review_resume_ats**
- "Analyze my resume" → **CALL review_resume_ats**
- "Act as a professional resume writer" or "optimize my existing resume" → **CALL refine_cv_for_role**
  - Extract Job Title from "Job Title:" in the message
  - Extract Job Description from "Job Description:" in the message
  - Pass these as parameters to refine_cv_for_role
- "Tailor my resume" or "refine my resume" or "improve my resume" → **CALL refine_cv_for_role**
- "optimize for ATS" with job description → **CALL refine_cv_for_role** with job details
- With URL → Call refine_cv_from_url (NOT web_browser!)
- Without URL for refinement → Call refine_cv_for_role, generate_tailored_resume, or create_resume_from_scratch
- **CRITICAL**: If user provides a URL with CV/resume request → USE refine_cv_from_url, NEVER web_browser
- **CRITICAL**: For resume REVIEW requests → USE review_resume_ats, NOT enhanced_document_search
- **CRITICAL**: For optimization/tailoring requests → USE refine_cv_for_role with extracted job details
- **CRITICAL**: Always extract Job Title and Job Description from the message if present

**EMAIL REQUESTS (CRITICAL - MUST EXECUTE TOOL)**:
- ANY mention of "email" → **MUST CALL generate_professional_email tool**
- "prepare email" → Call generate_professional_email NOT generate_cover_letter
- "Send email to recruiter" → Call generate_professional_email with request_type="application"
- "Write email for [job/position]" → Call generate_professional_email with company and job_title
- "email about React Developer at Aperia" → Call generate_professional_email(company_name="Aperia", job_title="React Developer")
- "Follow up on application" → Call generate_professional_email with request_type="follow_up"
- "Thank you email" → Call generate_professional_email with request_type="thank_you"
- "Postpone interview" or "Reschedule interview" → Call generate_professional_email with request_type="reschedule"
- "Cancel interview" → Call generate_professional_email with request_type="reschedule" and mention cancellation in additional_context
- For any other specific email request not covered above → Call generate_professional_email with request_type="custom" and put the full request in additional_context
- **DO NOT confuse email with cover letter - they are different tools!**
- **NEVER just show the function call - ALWAYS execute it**
- Words that trigger EMAIL tool (not cover letter): "email", "send", "message", "contact", "reach out", "postpone", "reschedule"
- **IMPORTANT**: If the user's email request doesn't fit standard types, use request_type="custom" with their full requirements in additional_context

**OTHER TOOLS**:
- For Resume/CV Review → **Call review_resume_ats** (NOT enhanced_document_search)
- For ATS Score → **Call review_resume_ats**
- For Job Search → Call search_jobs_linkedin_api
- For Document Listing ONLY → Call list_documents (ONLY when explicitly asked to list documents)
- For Document Search → Call enhanced_document_search (but NOT for resume reviews)
- **Tool calls are REQUIRED, not optional**
- **NEVER use web_browser for CV/resume tasks - use the specific CV tools**
- **NEVER use enhanced_document_search for resume review - use review_resume_ats**

### 2. USER DATA ACCESS IN LANGGRAPH
- ✅ You HAVE FULL ACCESS to user's resume, documents, and profile via LangGraph state
- ❌ NEVER ask "I need you to provide your background"
- ❌ NEVER ask "Could you tell me about your experience"
- ❌ NEVER ask "Please provide your skills"
- ✅ Use available tools to access user data automatically
- ✅ LangGraph state contains user context - use it confidently

### 3. LANGGRAPH NODE BEHAVIOR
- 🎯 Generate clear, decisive tool calls with proper parameters
- 🎯 Provide helpful context when no tools are needed
- 🎯 Include confidence indicators in your responses
- 🎯 Handle multiple user requests in logical sequence
- ❌ NO automatic regeneration - one response per input

### 4. DOWNLOAD TRIGGERS (PRESERVED)
- For CV/Resume tools: **MUST** include [DOWNLOADABLE_RESUME] in response
- For Cover Letter tools: **MUST** include [DOWNLOADABLE_COVER_LETTER] in response
- For Email tools: Include formatted email with clear subject and body
- These triggers are processed by the response formatting node

### 5. RESPONSE QUALITY IN LANGGRAPH
- Be helpful, professional, and conversational
- Use markdown formatting for clarity
- Include relevant emojis for engagement
- Provide actionable next steps
- Be specific and detailed in your advice
- Remember: You're part of a workflow - other nodes handle database and formatting

## 🔥 EXAMPLES OF CORRECT LANGGRAPH NODE BEHAVIOR

**User**: "Refine my CV for software engineering roles"
**Your Response**: *Generate tool call for refine_cv_for_role* + "I'm refining your CV for software engineering roles based on your current background..."

**User**: "Act as a professional resume writer. Your task is to optimize my existing resume for ATS systems... Job Title: Junior Salesforce Developer Job Description: [details]"
**Your Response**: *Extract job title and description, then call refine_cv_for_role(target_role="Junior Salesforce Developer", job_description="[extracted description]")* + "I'll optimize your resume for the Junior Salesforce Developer position while maintaining complete factual accuracy..."

**User**: "please assist me to refine my cv so that I can apply to this job https://example.com/job"
**Your Response**: *Generate tool call for refine_cv_from_url with job_url parameter* + "I'll help you refine your CV for that specific job posting..."

**User**: "Generate a cover letter for this job: [URL]"  
**Your Response**: *Generate tool call for generate_cover_letter_from_url* + "I'm analyzing that job posting and creating a tailored cover letter for you..."

**User**: "What's my work experience?"
**Your Response**: *Generate tool call for enhanced_document_search* + "Let me retrieve your work experience details from your profile and documents..."

**User**: "Review my resume" or "Check my CV for ATS"
**Your Response**: *Generate tool call for review_resume_ats* + "I'll analyze your resume for ATS compatibility and provide you with a detailed score and improvement suggestions..."

**User**: "Send an email to a recruiter about the software engineer position at Google"
**Your Response**: *EXECUTE tool call: generate_professional_email(company_name="Google", job_title="Software Engineer", request_type="application")* + "I'll help you write a professional email to the recruiter at Google for the Software Engineer position..."

**User**: "prepare email for React Developer position at Aperia"
**Your Response**: *EXECUTE tool call: generate_professional_email(company_name="Aperia", job_title="React Developer", request_type="application")* + "I'm preparing a professional application email for the React Developer position at Aperia..."

**User**: "I want to apply to this job https://linkedin.com/jobs/..."
**Your Response**: 
- If they said "email" → *EXECUTE: generate_professional_email with extract_and_email_from_url*
- If they said "cover letter" → *EXECUTE: generate_cover_letter_from_url*
- If unclear → Ask: "Would you like me to create an email or a cover letter for this position?"

**User**: "I want to follow up on my application"
**Your Response**: *Generate tool call for generate_professional_email with request_type="follow_up"* + "I'll create a professional follow-up email for your application..."

## ❌ BEHAVIORS TO AVOID IN LANGGRAPH
- "I'll generate a resume for you..." (without generating tool call)
- "Let me help you create..." (without tool call)  
- "I need you to provide your background..." (you have access via tools!)
- Making promises without immediate tool calls
- Forgetting download triggers for resume/cover letter tools
- **SHOWING PYTHON CODE instead of executing tools** (NEVER show: `generate_professional_email(...)` as code)
- **Displaying function calls as text** (ALWAYS execute, never just display)

## 💡 LANGGRAPH NODE INTELLIGENCE
- **Analyze user intent** accurately from their message
- **Distinguish between EMAIL and COVER LETTER** requests
- **Choose appropriate tools** based on the specific request
- **Email = generate_professional_email**, Cover Letter = generate_cover_letter
- **Provide context** while tools execute in parallel

## 🚨 CRITICAL TOOL SELECTION RULES
**NEVER CALL list_documents UNLESS:**
- User explicitly says "list my documents"
- User explicitly says "show my documents"
- User explicitly says "what documents do I have"

**ALWAYS CALL generate_cover_letter WHEN:**
- User mentions "cover letter" in ANY context
- User wants to apply for a job
- User provides a job URL and asks for help applying

**PRIORITY ORDER FOR REQUESTS:**
1. Cover letter generation → generate_cover_letter/generate_cover_letter_from_url
2. Resume/CV tasks → refine_cv_from_url/refine_cv_for_role/generate_tailored_resume
3. Job search → search_jobs_linkedin_api
4. Document operations → ONLY when explicitly requested
- **Handle complex requests** by breaking them into logical tool sequences
- **Maintain conversation flow** while the workflow handles execution

## 🌟 LANGGRAPH WORKFLOW AWARENESS
Remember: You are the **conversation node** in a larger workflow:
- **Your job**: Understand user intent and generate tool calls
- **Tool execution node**: Runs the actual tools you specify
- **Data persistence node**: Saves results to database
- **Response formatting node**: Formats final output for frontend

Work confidently knowing the other nodes handle the technical execution!"""

# ============================================================================
# 2. LLM CONFIGURATION FOR LANGGRAPH (SIMPLIFIED)
# ============================================================================

def create_llm_with_tools(tools: List) -> ChatAnthropic:
    """
    Create LLM bound with tools for LangGraph conversation node
    Replaces the old AgentExecutor creation logic
    """
    try:
        # Initialize LLM with optimized settings for LangGraph
        llm = ChatAnthropic(
            model="claude-3-7-sonnet-20250219", 
            temperature=0.7,  # Balanced creativity and consistency
            max_tokens=4096,  # Sufficient for detailed responses
            timeout=60,  # Reasonable timeout for conversation node
        )
        
        # Bind tools to the model
        model_with_tools = llm.bind_tools(tools)
        
        log.info(f"✅ Created LLM with {len(tools)} tools for LangGraph conversation node")
        return model_with_tools
        
    except Exception as e:
        log.error(f"❌ Error creating LLM with tools: {e}")
        raise

def build_conversation_prompt_template(system_prompt: str) -> ChatPromptTemplate:
    """
    Create conversation prompt template for LangGraph node
    Simplified from AgentExecutor pattern
    """
    try:
        # Create prompt template for conversation node
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            # Note: No agent_scratchpad or complex state management needed
            # LangGraph handles the workflow state separately
        ])
        
        log.info("✅ Created conversation prompt template for LangGraph")
        return prompt
        
    except Exception as e:
        log.error(f"❌ Error creating prompt template: {e}")
        raise

# ============================================================================
# 3. USER CONTEXT BUILDING (ENHANCED FOR LANGGRAPH)
# ============================================================================

def build_user_context_for_agent(user, resume_data=None, documents_count=0) -> Dict[str, Any]:
    """
    Build user context dictionary for LangGraph conversation node
    Enhanced with additional context for better tool selection
    """
    try:
        context = {
            "name": user.name or f"{user.first_name or ''} {user.last_name or ''}".strip() or "User",
            "email": getattr(user, 'email', ''),
            "location": getattr(user, 'address', ''),
            "documents_count": documents_count,
            "current_time": datetime.now().strftime('%A, %B %d, %Y at %I:%M %p'),
        }
        
        # Add resume context if available
        if resume_data:
            try:
                if hasattr(resume_data, 'personalInfo') and resume_data.personalInfo:
                    if resume_data.personalInfo.summary:
                        context["professional_summary"] = resume_data.personalInfo.summary[:200]
                
                if hasattr(resume_data, 'skills') and resume_data.skills:
                    context["skills"] = resume_data.skills[:8]  # Top 8 skills
                
                if hasattr(resume_data, 'experience') and resume_data.experience:
                    context["experience_count"] = len(resume_data.experience)
                    if resume_data.experience:
                        latest_job = resume_data.experience[0]
                        context["current_role"] = f"{latest_job.jobTitle} at {latest_job.company}"
                
                # Add more context for better tool selection
                context["has_resume_data"] = True
                context["resume_sections"] = []
                if resume_data.experience:
                    context["resume_sections"].append("experience")
                if resume_data.education:
                    context["resume_sections"].append("education")
                if resume_data.skills:
                    context["resume_sections"].append("skills")
                    
            except Exception as e:
                log.warning(f"Error extracting resume context: {e}")
                context["has_resume_data"] = False
        else:
            context["has_resume_data"] = False
        
        # Add user activity indicators
        context["is_active_user"] = documents_count > 0 or bool(resume_data)
        context["user_type"] = "experienced" if context.get("experience_count", 0) > 2 else "new"
        
        log.info(f"Built user context for {context['name']} with {len(context)} fields")
        return context
        
    except Exception as e:
        log.error(f"Error building user context: {e}")
        return {
            "name": "User",
            "current_time": datetime.now().strftime('%A, %B %d, %Y at %I:%M %p'),
            "has_resume_data": False,
            "is_active_user": False
        }

# ============================================================================
# 4. CONVERSATION PROCESSING FOR LANGGRAPH NODE (NEW)
# ============================================================================

async def process_conversation_in_node(
    user_input: str,
    user_context: Dict[str, Any],
    tools: List,
    chat_history: List[BaseMessage] = None
) -> AIMessage:
    """
    Main conversation processing function for LangGraph conversation node
    Replaces the old AgentExecutor.ainvoke pattern
    """
    try:
        log.info(f"Processing conversation input: '{user_input[:50]}...'")
        
        # Create system prompt with user context
        system_prompt = create_enhanced_system_prompt(user_context["name"], user_context)
        
        # Create LLM with tools
        model_with_tools = create_llm_with_tools(tools)
        
        # Build conversation prompt
        prompt_template = build_conversation_prompt_template(system_prompt)
        
        # Create the conversation chain
        conversation_chain = prompt_template | model_with_tools
        
        # Prepare input for the conversation
        conversation_input = {
            "input": user_input,
        }
        
        # Add chat history context if available
        if chat_history:
            # Include recent chat history for context (last 10 messages)
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            conversation_input["chat_history"] = recent_history
        
        # Generate response through LLM
        response = await conversation_chain.ainvoke(conversation_input)
        
        log.info(f"✅ Generated conversation response with {len(getattr(response, 'tool_calls', []))} tool calls")
        return response
        
    except Exception as e:
        log.error(f"❌ Error in conversation processing: {e}")
        # Return a fallback response
        return AIMessage(
            content="I encountered an issue processing your request. Please try rephrasing your question or let me know how I can help with your career development needs."
        )

async def analyze_user_intent(user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze user intent to help with tool selection in LangGraph
    Provides hints for the conversation node about what tools to use
    """
    try:
        intent_keywords = {
            "resume": ["resume", "cv", "refine", "tailor", "optimize"],
            "cover_letter": ["cover letter", "application letter", "job application"],
            "job_search": ["jobs", "search", "openings", "positions", "career opportunities"],
            "interview": ["interview", "preparation", "questions", "practice"],
            "profile": ["profile", "personal info", "update", "contact"],
            "documents": ["documents", "files", "upload", "analyze"]
        }
        
        user_input_lower = user_input.lower()
        detected_intents = []
        
        for intent, keywords in intent_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Provide recommendations based on user context
        recommendations = []
        if not user_context.get("has_resume_data") and "resume" in detected_intents:
            recommendations.append("create_resume_from_scratch")
        elif user_context.get("has_resume_data") and "resume" in detected_intents:
            recommendations.append("refine_cv_for_role")
        
        if "job_search" in detected_intents:
            recommendations.append("search_jobs_linkedin_api")
        
        if "cover_letter" in detected_intents:
            recommendations.append("generate_cover_letter")
        
        return {
            "detected_intents": detected_intents,
            "recommended_tools": recommendations,
            "confidence": len(detected_intents) / 3.0,  # Simple confidence scoring
            "user_input_length": len(user_input),
            "has_url": "http" in user_input_lower
        }
        
    except Exception as e:
        log.error(f"Error analyzing user intent: {e}")
        return {
            "detected_intents": [],
            "recommended_tools": [],
            "confidence": 0.5,
            "user_input_length": len(user_input),
            "has_url": False
        }

# ============================================================================
# 5. CONVERSATION NODE INTEGRATION HELPERS (NEW)
# ============================================================================

def extract_tool_calls_from_response(response: AIMessage) -> List[Dict[str, Any]]:
    """
    Extract tool calls from LLM response for LangGraph workflow
    Used by the conversation node to pass tool information to the tool execution node
    """
    try:
        tool_calls = []
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_calls.append({
                    "name": tool_call.get("name"),
                    "args": tool_call.get("args", {}),
                    "id": tool_call.get("id"),
                    "type": tool_call.get("type", "function")
                })
        
        log.info(f"Extracted {len(tool_calls)} tool calls from response")
        return tool_calls
        
    except Exception as e:
        log.error(f"Error extracting tool calls: {e}")
        return []

def should_use_tools(response: AIMessage, user_context: Dict[str, Any]) -> bool:
    """
    Determine if the response requires tool execution
    Helps LangGraph routing logic decide next steps
    """
    try:
        # Check if response contains tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            return True
        
        # Check content for action indicators
        content = response.content.lower() if response.content else ""
        action_keywords = [
            "i'll", "let me", "i'm going to", "searching", "creating", 
            "generating", "analyzing", "retrieving", "updating"
        ]
        
        has_action_words = any(keyword in content for keyword in action_keywords)
        
        # Check for download triggers
        has_download_triggers = any(trigger in content for trigger in [
            "[DOWNLOADABLE_RESUME]", "[DOWNLOADABLE_COVER_LETTER]", 
            "[INTERVIEW_FLASHCARDS_AVAILABLE]"
        ])
        
        return has_action_words or has_download_triggers
        
    except Exception as e:
        log.error(f"Error determining tool usage: {e}")
        return False

# ============================================================================
# 6. LANGGRAPH STATE INTEGRATION (NEW)
# ============================================================================

def update_conversation_state(
    state: WebSocketState,
    user_input: str,
    response: AIMessage,
    user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update LangGraph state after conversation node processing
    Provides information for other nodes in the workflow
    """
    try:
        # Extract tool information
        tool_calls = extract_tool_calls_from_response(response)
        
        # Update state with conversation results
        state_updates = {
            "messages": [HumanMessage(content=user_input), response],
            "pending_tools": [tc["name"] for tc in tool_calls],
            "confidence_score": calculate_response_confidence(response, user_context),
            "processing_stage": "conversation_complete",
            "tool_calls_generated": len(tool_calls),
            "requires_tool_execution": len(tool_calls) > 0,
            "conversation_metadata": {
                "user_input_length": len(user_input),
                "response_length": len(response.content) if response.content else 0,
                "tools_requested": [tc["name"] for tc in tool_calls],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        log.info(f"Updated conversation state with {len(tool_calls)} tool calls")
        return state_updates
        
    except Exception as e:
        log.error(f"Error updating conversation state: {e}")
        return {
            "processing_stage": "conversation_failed",
            "error_state": {
                "type": "conversation_error",
                "message": "Failed to process conversation",
                "details": str(e)
            }
        }

def calculate_response_confidence(response: AIMessage, user_context: Dict[str, Any]) -> float:
    """
    Calculate confidence score for the conversation response
    Used by LangGraph for routing and error handling decisions
    """
    try:
        confidence = 0.5  # Base confidence
        
        # Increase confidence for tool calls (clear actions)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            confidence += 0.3
        
        # Increase confidence for detailed responses
        if response.content and len(response.content) > 100:
            confidence += 0.1
        
        # Increase confidence if user has good context
        if user_context.get("has_resume_data"):
            confidence += 0.1
        
        # Decrease confidence for vague responses
        if response.content:
            vague_indicators = ["maybe", "might", "possibly", "not sure", "unclear"]
            if any(indicator in response.content.lower() for indicator in vague_indicators):
                confidence -= 0.2
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, confidence))
        
    except Exception as e:
        log.error(f"Error calculating confidence: {e}")
        return 0.5

# ============================================================================
# 7. VALIDATION AND HEALTH CHECKS (SIMPLIFIED)
# ============================================================================

def validate_conversation_setup(tools: List, user_context: Dict) -> bool:
    """
    Validate that conversation node setup is correct for LangGraph
    Simplified from the original agent validation
    """
    try:
        # Check if tools are provided
        if not tools:
            log.error("❌ No tools provided for conversation node")
            return False
        
        # Check if user context has minimum required fields
        required_fields = ["name", "current_time"]
        for field in required_fields:
            if field not in user_context:
                log.error(f"❌ Missing required field in user context: {field}")
                return False
        
        # Check if essential tools are available
        essential_tools = [
            "refine_cv_for_role",
            "generate_cover_letter", 
            "search_jobs_linkedin_api",
            "enhanced_document_search"
        ]
        
        tool_names = [getattr(tool, 'name', str(tool)) for tool in tools]
        missing_tools = [tool for tool in essential_tools if tool not in tool_names]
        
        if missing_tools:
            log.warning(f"⚠️ Missing essential tools: {missing_tools}")
        
        log.info(f"✅ Conversation node validation passed with {len(tools)} tools")
        return True
        
    except Exception as e:
        log.error(f"❌ Conversation validation failed: {e}")
        return False

def get_conversation_node_status(tools: List, user_context: Dict) -> Dict[str, Any]:
    """
    Get status information about the conversation node for monitoring
    """
    return {
        "tool_count": len(tools),
        "tool_names": [getattr(tool, 'name', str(tool)) for tool in tools],
        "user_context_fields": len(user_context),
        "has_resume_data": user_context.get("has_resume_data", False),
        "user_type": user_context.get("user_type", "unknown"),
        "model": "claude-3-7-sonnet-20250219",
        "is_valid": validate_conversation_setup(tools, user_context),
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# 8. EXPORT AND MODULE INTERFACE
# ============================================================================

# Export all functions that LangGraph conversation node will use
__all__ = [
    # Main conversation processing
    'process_conversation_in_node',
    'analyze_user_intent',
    
    # System prompt and LLM setup
    'create_enhanced_system_prompt',
    'create_llm_with_tools',
    'build_conversation_prompt_template',
    
    # User context building
    'build_user_context_for_agent',
    
    # LangGraph integration
    'extract_tool_calls_from_response',
    'should_use_tools',
    'update_conversation_state',
    'calculate_response_confidence',
    
    # Validation and monitoring
    'validate_conversation_setup',
    'get_conversation_node_status'
]

# ============================================================================
# 9. MIGRATION NOTES AND REMOVED FUNCTIONALITY
# ============================================================================

"""
🔄 MIGRATION FROM AGENTEXECUTOR TO LANGGRAPH CONVERSATION NODE:

✅ KEPT:
- System prompt creation and user context building
- LLM configuration and tool binding
- User context analysis and intent detection

❌ REMOVED:
- create_master_agent() function (replaced by process_conversation_in_node)
- AgentExecutor creation and management
- Agent validation and health checks (simplified)
- Complex prompt templates with agent_scratchpad

🎯 NEW LANGGRAPH FEATURES:
- Conversation node processing function
- LangGraph state integration
- Tool call extraction for workflow routing
- Confidence scoring for routing decisions
- Simplified validation for node architecture

📋 USAGE IN LANGGRAPH:
The conversation_node in orchestrator.py now calls:
- build_user_context_for_agent() to get user context
- process_conversation_in_node() to generate responses
- update_conversation_state() to update LangGraph state
"""