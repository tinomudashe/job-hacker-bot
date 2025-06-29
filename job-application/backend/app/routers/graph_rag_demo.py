from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User
from app.graph_rag import EnhancedGraphRAG
from typing import Optional, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class GraphRAGDemoRequest(BaseModel):
    query: str
    job_description: Optional[str] = None
    context: Optional[dict] = None

class GraphRAGDemoResponse(BaseModel):
    query: str
    enhanced_query: str
    results: List[dict]
    job_analysis: Optional[dict] = None
    confidence_score: Optional[float] = None
    graph_rag_enabled: bool
    demo_explanation: str

@router.post("/demo/graph-rag-search", response_model=GraphRAGDemoResponse)
async def demo_graph_rag_search(
    request: GraphRAGDemoRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Demo endpoint to showcase Graph RAG intelligent search capabilities
    """
    try:
        # Initialize Graph RAG
        graph_rag = EnhancedGraphRAG(user.id, db)
        initialized = await graph_rag.initialize()
        
        if not initialized:
            return GraphRAGDemoResponse(
                query=request.query,
                enhanced_query=request.query,
                results=[],
                graph_rag_enabled=False,
                demo_explanation="Graph RAG not available - no documents uploaded yet. Please upload your resume or documents first."
            )
        
        # Analyze job description if provided
        job_analysis = None
        if request.job_description:
            job_analysis = await graph_rag._analyze_job_description(request.job_description)
        
        # Perform intelligent search
        search_context = request.context or job_analysis
        results = await graph_rag.intelligent_search(request.query, search_context)
        
        # Format results for demo
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                "metadata": doc.metadata,
                "document_type": doc.metadata.get("document_type", "unknown"),
                "skills": doc.metadata.get("skills", []),
                "relevance_indicators": doc.metadata.get("section_type", "general")
            })
        
        # Generate enhanced query explanation
        enhanced_query = graph_rag._enhance_search_query(request.query, search_context)
        
        # Calculate confidence score
        confidence = 0.0
        if results and job_analysis:
            confidence = graph_rag._calculate_confidence_score(job_analysis, results)
        
        demo_explanation = f"""
        🧠 Graph RAG Intelligence Demo:
        
        Original Query: "{request.query}"
        Enhanced Query: "{enhanced_query}"
        
        Graph Connections Found: {len(results)} related documents
        Job Match Confidence: {confidence:.2f} (0.0 = poor match, 1.0 = excellent match)
        
        How Graph RAG Works:
        1. Creates intelligent connections between your documents based on skills, experience, and industry
        2. Traverses these connections to find the most relevant information
        3. Provides context-aware results that understand job requirements
        4. Generates personalized responses based on your background and the job
        
        Traditional search would only find text similarity, but Graph RAG understands:
        - Skill relationships (Python → Backend Development → Software Engineering)
        - Experience connections (Previous roles → Relevant projects → Achievements)
        - Industry context (Technology sector → Required competencies → Career progression)
        """
        
        return GraphRAGDemoResponse(
            query=request.query,
            enhanced_query=enhanced_query,
            results=formatted_results,
            job_analysis=job_analysis,
            confidence_score=confidence,
            graph_rag_enabled=True,
            demo_explanation=demo_explanation.strip()
        )
        
    except Exception as e:
        logger.error(f"Graph RAG demo failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

@router.post("/demo/intelligent-application-context")
async def demo_intelligent_application_context(
    job_description: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Demo endpoint showing how Graph RAG enhances job application context
    """
    try:
        # Initialize Graph RAG
        graph_rag = EnhancedGraphRAG(user.id, db)
        initialized = await graph_rag.initialize()
        
        if not initialized:
            return {
                "error": "Graph RAG not available - please upload documents first",
                "graph_rag_enabled": False
            }
        
        # Get comprehensive application context
        context = await graph_rag.get_job_application_context(job_description)
        
        # Format for demo
        demo_response = {
            "graph_rag_enabled": True,
            "job_analysis": context.get("job_analysis", {}),
            "confidence_score": context.get("confidence_score", 0.0),
            "relevant_experience": context.get("relevant_experience", [])[:2],  # Limit for demo
            "cover_letter_preview": context.get("cover_letter", "")[:400] + "..." if context.get("cover_letter") else "",
            "intelligence_features": {
                "skill_matching": "Automatically identifies which of your skills match the job requirements",
                "experience_relevance": "Finds the most relevant work experience and projects from your background",
                "contextual_responses": "Generates job-specific answers for application forms",
                "confidence_scoring": "Provides a confidence score for application success likelihood",
                "smart_cover_letters": "Creates personalized cover letters highlighting relevant experience"
            },
            "demo_explanation": f"""
            🎯 Intelligent Job Application Context Demo:
            
            Job Analysis Results:
            - Position: {context.get("job_analysis", {}).get("job_title", "N/A")}
            - Required Skills: {', '.join(context.get("job_analysis", {}).get("required_skills", [])[:5])}
            - Match Confidence: {context.get("confidence_score", 0.0):.2f}
            
            What makes this intelligent:
            1. CONTEXT AWARENESS: Understands the specific job requirements and tailors responses
            2. RELATIONSHIP MAPPING: Connects your skills to job needs through graph relationships
            3. SMART PRIORITIZATION: Highlights your most relevant experience for this specific role
            4. ADAPTIVE RESPONSES: Adjusts communication style based on industry and role level
            
            Traditional systems just keyword match - Graph RAG understands context and relationships!
            """
        }
        
        return demo_response
        
    except Exception as e:
        logger.error(f"Intelligent application context demo failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

@router.get("/demo/graph-rag-status")
async def demo_graph_rag_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Check Graph RAG status and capabilities for the current user
    """
    try:
        # Initialize Graph RAG
        graph_rag = EnhancedGraphRAG(user.id, db)
        initialized = await graph_rag.initialize()
        
        if not initialized:
            return {
                "graph_rag_enabled": False,
                "status": "Not Available",
                "reason": "No documents uploaded or initialization failed",
                "recommendations": [
                    "Upload your resume or CV",
                    "Add work experience documents",
                    "Upload project portfolios",
                    "Ensure documents have sufficient content"
                ]
            }
        
        # Get basic stats
        vector_store_size = len(graph_rag.vector_store._docs) if graph_rag.vector_store else 0
        
        return {
            "graph_rag_enabled": True,
            "status": "Active",
            "user_name": user.name,
            "documents_processed": vector_store_size,
            "capabilities": {
                "intelligent_search": True,
                "job_analysis": True,
                "context_aware_responses": True,
                "skill_mapping": True,
                "experience_matching": True,
                "cover_letter_generation": True,
                "confidence_scoring": True
            },
            "graph_features": {
                "edge_types": ["skills", "industries", "job_titles", "experience_level", "document_type"],
                "search_strategy": "Eager traversal with k=8, depth=3",
                "embedding_model": "Google Text Embedding 004"
            },
            "demo_available": True,
            "message": "🧠 Graph RAG is ready! Your agent is now significantly smarter with contextual understanding and relationship-based reasoning."
        }
        
    except Exception as e:
        logger.error(f"Graph RAG status check failed: {e}")
        return {
            "graph_rag_enabled": False,
            "status": "Error",
            "error": str(e)
        }

@router.post("/demo/personalized-advice")
async def demo_personalized_advice(
    job_description: str,
    advice_type: str = "cv_improvement",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Demo endpoint showing deeply personalized advice that proves the agent knows the user
    """
    try:
        # Initialize Graph RAG
        graph_rag = EnhancedGraphRAG(user.id, db)
        initialized = await graph_rag.initialize()
        
        if not initialized:
            return {
                "error": "Graph RAG not available - please upload documents first",
                "graph_rag_enabled": False,
                "generic_fallback": "To strengthen your CV for AI Engineering roles, consider adding: Programming Languages: Python, R, Java, C++..."
            }
        
        # Generate personalized advice
        personalized_advice = await graph_rag.generate_personalized_advice(job_description, advice_type)
        
        # Also show what a generic response would look like for comparison
        generic_response = """
        To strengthen your CV for AI Engineering roles, consider adding the following, if applicable:
        
        Technical Skills: List specific AI/ML technologies you're proficient in:
        - Programming Languages: Python, R, Java, C++
        - ML Libraries/Frameworks: TensorFlow, PyTorch, scikit-learn, Keras
        - Cloud Computing: AWS (SageMaker), Azure (ML Studio), GCP (Vertex AI)
        
        Projects/Experience:
        - Quantifiable achievements: Instead of just listing tasks, quantify your contributions
        - AI-related projects: Showcase personal projects, hackathons, or relevant coursework
        """
        
        return {
            "graph_rag_enabled": True,
            "user_name": user.name,
            "advice_type": advice_type,
            "personalized_advice": personalized_advice,
            "generic_comparison": generic_response.strip(),
            "demo_explanation": f"""
            🎯 Personalization Demo - This shows the difference:
            
            ❌ GENERIC RESPONSE: Cold, templated advice that could apply to anyone
            ✅ PERSONALIZED RESPONSE: Shows intimate knowledge of {user.name}'s specific background
            
            The Graph RAG system:
            1. Analyzes your actual work experience and companies
            2. Identifies your current technical skills
            3. Finds your real achievements and quantifiable results
            4. Maps your background to the target role requirements
            5. Provides advice that feels like it comes from someone who knows you
            
            This eliminates those frustrating "one-size-fits-all" responses!
            """,
            "personalization_indicators": [
                "References your specific companies and roles",
                "Mentions your actual technical skills",
                "Connects your real achievements to target role",
                "Provides next steps based on your current level",
                "Feels like advice from a friend who knows your background"
            ]
        }
        
    except Exception as e:
        logger.error(f"Personalized advice demo failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}") 