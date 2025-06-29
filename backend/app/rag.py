from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models_db import Document, User
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.dependencies import get_current_active_user
from app.graph_rag import EnhancedGraphRAG
import os
from langchain.docstore.document import Document as LCDocument
from typing import List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/rag/assist")
async def rag_assist(
    task: str,
    job_description: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
    form_questions: Optional[List[str]] = None,
):
    # Find the latest resume document for the user
    result = await db.execute(
        select(Document).where(Document.user_id == user.id, Document.type == "resume").order_by(Document.date_created.desc())
    )
    doc = result.scalars().first()
    
    if not doc:
        # Instead of failing, provide helpful guidance to use modern tools
        if task == "regenerate_cv":
            return {
                "cv": "I notice you don't have a CV uploaded yet. Let me help you create one! "
                     "I can use my modern resume generation tools to create a tailored resume for AI Engineering roles. "
                     "Please try asking: 'Generate a tailored resume for AI Engineering roles' or "
                     "'Create a resume from scratch for Software Engineer positions'. "
                     "These tools don't require an existing CV and can create professional resumes based on your profile and job requirements.",
                "error": "no_resume_found",
                "suggestion": "use_modern_tools"
            }
        elif task == "cover_letter":
            return {
                "cover_letter": "I can help you create a cover letter! While I don't have your CV on file, "
                              "I can still generate a professional cover letter based on the job description. "
                              f"For the {job_description}, I'll create a compelling cover letter that highlights relevant skills and experience.",
                "error": "no_resume_found",
                "suggestion": "basic_cover_letter"
            }
        else:
            raise HTTPException(status_code=404, detail="No resume found. Please upload your CV first or use the modern resume generation tools.")
    
    try:
        # Load FAISS index
        embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-004")
        vectorstore = FAISS.load_local(doc.vector_store_path, embedding, allow_dangerous_deserialization=True)
        # Retrieve relevant chunks
        relevant_docs = vectorstore.similarity_search(job_description, k=5)
        context = "\n".join([d.page_content for d in relevant_docs])
    except Exception as e:
        logger.warning(f"FAISS loading failed: {e}")
        # Fallback to using the document content directly
        context = doc.content or "No content available"
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    
    if task == "cover_letter":
        prompt = f"You are an expert job applicant. Using the following CV info:\n{context}\nWrite a personalized cover letter for this job:\n{job_description}"
        result = llm.invoke(prompt)
        return {"cover_letter": result.content}
    elif task == "regenerate_cv":
        prompt = f"You are an expert resume writer. Using the following CV info:\n{context}\nRegenerate and tailor the CV for this job:\n{job_description}"
        result = llm.invoke(prompt)
        return {"cv": result.content}
    elif task == "apply":
        if not form_questions:
            raise HTTPException(status_code=400, detail="form_questions required for apply task")
        answers = []
        for q in form_questions:
            prompt = f"Based on this CV:\n{context}\nAnswer this job application question:\n{q}\nJob description:\n{job_description}"
            answer = llm.invoke(prompt)
            answers.append({"question": q, "answer": answer.content})
        return {"answers": answers}
    else:
        raise HTTPException(status_code=400, detail="Invalid task")

@router.post("/rag/graph-assist")
async def graph_rag_assist(
    task: str,
    job_description: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
    form_questions: Optional[List[str]] = None,
):
    """Enhanced RAG assistance using Graph RAG for smarter agent reasoning"""
    
    try:
        # Initialize Graph RAG system
        graph_rag = EnhancedGraphRAG(user.id, db)
        initialized = await graph_rag.initialize()
        
        if not initialized:
            # Fallback to basic assistance
            return {
                "message": "Graph RAG not available, using basic assistance",
                "task": task,
                "fallback": True
            }
        
        if task == "job_application_context":
            # Get comprehensive job application context
            context = await graph_rag.get_job_application_context(job_description, form_questions)
            
            return {
                "task": "job_application_context",
                "job_analysis": context.get("job_analysis", {}),
                "form_answers": context.get("form_answers", []),
                "cover_letter": context.get("cover_letter", ""),
                "optimized_resume": context.get("optimized_resume", ""),
                "relevant_experience": context.get("relevant_experience", []),
                "confidence_score": context.get("confidence_score", 0.5),
                "graph_rag_enabled": True
            }
        
        elif task == "cover_letter":
            # Generate intelligent cover letter
            context = await graph_rag.get_job_application_context(job_description)
            return {
                "cover_letter": context.get("cover_letter", ""),
                "job_analysis": context.get("job_analysis", {}),
                "confidence_score": context.get("confidence_score", 0.5),
                "graph_rag_enabled": True
            }
        
        elif task == "form_answers":
            if not form_questions:
                raise HTTPException(status_code=400, detail="form_questions required for form_answers task")
            
            context = await graph_rag.get_job_application_context(job_description, form_questions)
            return {
                "form_answers": context.get("form_answers", []),
                "job_analysis": context.get("job_analysis", {}),
                "confidence_score": context.get("confidence_score", 0.5),
                "graph_rag_enabled": True
            }
        
        elif task == "intelligent_search":
            # Perform intelligent search using Graph RAG
            search_query = form_questions[0] if form_questions else job_description[:200]
            job_context = await graph_rag._analyze_job_description(job_description)
            
            results = await graph_rag.intelligent_search(search_query, job_context)
            
            return {
                "search_results": [{"content": doc.page_content, "metadata": doc.metadata} for doc in results],
                "query": search_query,
                "context_used": job_context,
                "graph_rag_enabled": True
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid task for Graph RAG. Supported: job_application_context, cover_letter, form_answers, intelligent_search")
            
    except Exception as e:
        logger.error(f"Graph RAG assist failed: {e}")
        raise HTTPException(status_code=500, detail=f"Graph RAG processing failed: {str(e)}")

@router.post("/rag/agent-context")
async def get_agent_context(
    job_url: str,
    job_description: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Get intelligent context for the job application agent using Graph RAG"""
    
    try:
        # Initialize Graph RAG
        graph_rag = EnhancedGraphRAG(user.id, db)
        initialized = await graph_rag.initialize()
        
        if not initialized:
            return {
                "error": "Graph RAG not available",
                "fallback_context": f"User: {user.name}, Job URL: {job_url}"
            }
        
        # Get comprehensive application context
        context = await graph_rag.get_job_application_context(job_description)
        
        # Extract job requirements for form filling guidance
        job_analysis = context.get("job_analysis", {})
        
        # Generate agent instructions based on Graph RAG insights
        agent_instructions = await _generate_agent_instructions(job_analysis, context, user)
        
        return {
            "agent_instructions": agent_instructions,
            "job_analysis": job_analysis,
            "user_strengths": context.get("relevant_experience", [])[:3],
            "confidence_score": context.get("confidence_score", 0.5),
            "form_filling_hints": {
                "skills_to_highlight": job_analysis.get("required_skills", [])[:5],
                "experience_level": job_analysis.get("experience_level", "mid"),
                "key_achievements": _extract_achievements_from_context(context)
            },
            "graph_rag_enabled": True
        }
        
    except Exception as e:
        logger.error(f"Agent context generation failed: {e}")
        return {
            "error": f"Context generation failed: {str(e)}",
            "fallback_context": f"User: {user.name}, Job URL: {job_url}"
        }

async def _generate_agent_instructions(job_analysis: dict, context: dict, user: User) -> str:
    """Generate intelligent agent instructions based on Graph RAG analysis"""
    
    job_title = job_analysis.get("job_title", "Position")
    required_skills = job_analysis.get("required_skills", [])
    confidence = context.get("confidence_score", 0.5)
    
    instructions = f"""
    INTELLIGENT AGENT INSTRUCTIONS (Graph RAG Enhanced):
    
    Job Target: {job_title}
    User: {user.name}
    Confidence Score: {confidence:.2f}
    
    KEY STRATEGIES:
    1. Highlight these relevant skills when found in forms: {', '.join(required_skills[:5])}
    2. Confidence level: {'HIGH' if confidence > 0.7 else 'MODERATE' if confidence > 0.4 else 'REQUIRES_ATTENTION'}
    3. Experience level match: {job_analysis.get('experience_level', 'mid')}
    
    FORM FILLING PRIORITIES:
    - Emphasize technical skills that match job requirements
    - Use specific examples from relevant experience sections
    - Align responses with {job_analysis.get('industry', 'technology')} industry expectations
    
    If confidence is low, be extra careful with form responses and consider asking for human assistance.
    """
    
    return instructions.strip()

def _extract_achievements_from_context(context: dict) -> List[str]:
    """Extract key achievements from Graph RAG context"""
    
    achievements = []
    relevant_exp = context.get("relevant_experience", [])
    
    for exp in relevant_exp[:3]:
        # Simple achievement extraction
        if any(keyword in exp.lower() for keyword in ["achieved", "improved", "increased", "reduced", "built", "developed"]):
            # Extract first sentence containing achievement keywords
            sentences = exp.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in ["achieved", "improved", "increased", "reduced"]):
                    achievements.append(sentence.strip())
                    break
    
    return achievements[:3]