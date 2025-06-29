import faiss
import asyncio
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from app.models_db import Document, User
from app.enhanced_memory import AsyncSafeEnhancedMemoryManager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_user_vector_store(user_id: str, db: AsyncSession):
    """
    Enhanced vector store management with user learning context
    """
    try:
        # Initialize enhanced memory manager
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        memory_manager = AsyncSafeEnhancedMemoryManager(db, user)
        
        # Get user learning profile for personalized document prioritization
        user_profile = await memory_manager._get_user_learning_profile_safe()
        
        # Get user documents with enhanced prioritization
        doc_result = await db.execute(
            select(Document).where(Document.user_id == user_id)
        )
        documents = doc_result.scalars().all()
        
        # Prioritize documents based on user learning profile
        prioritized_docs = await _prioritize_documents_by_relevance(
            documents, user_profile, memory_manager
        )
        
        texts = []
        
        # Add enhanced user context based on learning profile
        enhanced_user_info = await _generate_enhanced_user_context(user, user_profile)
        texts.append(enhanced_user_info)
        
        # Add document contents with personalized weighting
        for doc in prioritized_docs:
            if doc.content:
                # Add document type context for better retrieval
                doc_context = f"[{doc.type.upper()} DOCUMENT - {doc.name}]\n{doc.content}"
                texts.append(doc_context)
        
        if not texts:
            return None
        
        # Enhanced text splitting based on document types and user preferences
        text_splitter = CharacterTextSplitter(
            chunk_size=_get_optimal_chunk_size_for_user(user_profile),
            chunk_overlap=100
        )
        docs = text_splitter.create_documents(texts)
        
        # Track vector store usage
        try:
            await memory_manager.save_user_behavior_safe(
                action_type="vector_store_access",
                context={
                    "documents_count": len(documents),
                    "prioritized_count": len(prioritized_docs),
                    "chunks_created": len(docs),
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=True
            )
        except Exception as e:
            logger.warning(f"Failed to track vector store usage: {e}")
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = await FAISS.afrom_documents(docs, embeddings)
        
        return vector_store
        
    except Exception as e:
        logger.error(f"Error creating enhanced vector store for user {user_id}: {e}")
        # Fallback to basic vector store
        return await _create_basic_vector_store(user_id, db)

async def _prioritize_documents_by_relevance(
    documents: List[Document], 
    user_profile, 
    memory_manager: AsyncSafeEnhancedMemoryManager
) -> List[Document]:
    """Prioritize documents based on user learning profile and recent interactions"""
    
    try:
        # Score documents based on relevance to user profile
        scored_docs = []
        
        for doc in documents:
            score = 0.0
            
            # Base score by document type preferences
            if user_profile and user_profile.preferences:
                preferred_doc_type = user_profile.preferences.get("preferred_document_type")
                if preferred_doc_type == doc.type:
                    score += 2.0
            
            # Score by job search patterns alignment
            if user_profile and user_profile.job_search_patterns and doc.content:
                common_keywords = user_profile.job_search_patterns.get("common_keywords", [])
                keyword_matches = sum(1 for keyword in common_keywords 
                                    if keyword.lower() in doc.content.lower())
                score += keyword_matches * 0.5
            
            # Recent document bonus
            try:
                # Handle timezone-aware vs naive datetime comparison
                now = datetime.utcnow()
                if doc.date_created.tzinfo is not None:
                    # Convert to naive datetime for comparison
                    doc_created = doc.date_created.replace(tzinfo=None)
                else:
                    doc_created = doc.date_created
                
                days_old = (now - doc_created).days
                if days_old < 30:  # Recent documents get priority
                    score += max(0, (30 - days_old) / 30)
            except Exception:
                # If datetime comparison fails, just skip the recent bonus
                pass
            
            # Document type relevance
            if doc.type == "resume":
                score += 1.5  # Resumes are generally high priority
            elif doc.type == "cover_letter":
                score += 1.0
            
            scored_docs.append((doc, score))
        
        # Sort by score (descending) and return documents
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs]
        
    except Exception as e:
        logger.warning(f"Document prioritization failed: {e}")
        return documents

async def _generate_enhanced_user_context(user: User, user_profile) -> str:
    """Generate enhanced user context information for vector store"""
    
    context_parts = [
        f"Name: {user.name or 'Not specified'}",
        f"Email: {user.email or 'Not specified'}",
        f"Phone: {user.phone or 'Not specified'}",
        f"Location: {user.address or 'Not specified'}",
        f"LinkedIn: {user.linkedin or 'Not specified'}"
    ]
    
    # Add learning profile insights
    if user_profile and user_profile.job_search_patterns:
        job_patterns = user_profile.job_search_patterns
        
        if job_patterns.get("common_job_titles"):
            context_parts.append(f"Career Interest: {', '.join(job_patterns['common_job_titles'][:3])}")
        
        if job_patterns.get("common_search_locations"):
            context_parts.append(f"Preferred Locations: {', '.join(job_patterns['common_search_locations'][:3])}")
        
        if job_patterns.get("preferred_job_boards"):
            context_parts.append(f"Preferred Job Boards: {', '.join(job_patterns['preferred_job_boards'][:3])}")
    
    # Add skill preferences from CV learning
    if user_profile and user_profile.preferences:
        cv_skills = [key.replace("cv_skill_", "").title() 
                    for key in user_profile.preferences.keys() 
                    if key.startswith("cv_skill_") and user_profile.preferences[key] == "true"]
        if cv_skills:
            context_parts.append(f"Key Skills: {', '.join(cv_skills[:10])}")
        
        # Add industry preference
        industry = user_profile.preferences.get("preferred_industry")
        if industry:
            context_parts.append(f"Industry Focus: {industry.title()}")
        
        # Add experience level
        experience_years = user_profile.preferences.get("experience_years")
        if experience_years:
            context_parts.append(f"Experience Level: {experience_years} years")
    
    # Add interaction patterns for context
    if user_profile and user_profile.interaction_patterns:
        patterns = user_profile.interaction_patterns
        
        detail_level = patterns.get("preferred_detail_level", "moderate")
        context_parts.append(f"Communication Preference: {detail_level} detail level")
        
        common_actions = patterns.get("most_common_actions", {})
        if common_actions:
            top_action = max(common_actions, key=common_actions.get)
            context_parts.append(f"Most Common Activity: {top_action}")
    
    return "[USER PROFILE]\n" + "\n".join(context_parts) + "\n"

def _get_optimal_chunk_size_for_user(user_profile) -> int:
    """Determine optimal chunk size based on user interaction patterns"""
    
    default_size = 1000
    
    try:
        if user_profile and user_profile.interaction_patterns:
            detail_preference = user_profile.interaction_patterns.get("preferred_detail_level", "moderate")
            
            if detail_preference == "detailed":
                return 1500  # Larger chunks for users who prefer detail
            elif detail_preference == "brief":
                return 800   # Smaller chunks for users who prefer concise info
        
        return default_size
        
    except Exception:
        return default_size

async def _create_basic_vector_store(user_id: str, db: AsyncSession):
    """Fallback to basic vector store creation if enhanced version fails"""
    
    try:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()

        doc_result = await db.execute(
            select(Document).where(Document.user_id == user_id)
        )
        documents = doc_result.scalars().all()
        
        texts = [doc.content for doc in documents if doc.content]
        
        user_info = f"""
        Name: {user.name}
        Email: {user.email}
        Phone: {user.phone}
        Location: {user.address}
        LinkedIn: {user.linkedin}
        """
        texts.append(user_info)

        if not texts:
            return None
            
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.create_documents(texts)
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = await FAISS.afrom_documents(docs, embeddings)
        
        return vector_store
        
    except Exception as e:
        logger.error(f"Basic vector store creation failed for user {user_id}: {e}")
        return None

async def add_document_to_vector_store(document: Document, db: AsyncSession):
    """
    Enhanced document addition to vector store with user learning integration
    """
    try:
        # Initialize enhanced memory manager
        user_result = await db.execute(select(User).where(User.id == document.user_id))
        user = user_result.scalar_one()
        memory_manager = AsyncSafeEnhancedMemoryManager(db, user)
        
        # Track document addition behavior
        await memory_manager.save_user_behavior_safe(
            action_type="document_vectorization",
            context={
                "document_type": document.type,
                "document_name": document.name,
                "content_length": len(document.content) if document.content else 0,
                "timestamp": datetime.utcnow().isoformat()
            },
            success=True
        )
        
        # Recreate enhanced vector store with new document
        vector_store = await get_user_vector_store(document.user_id, db)
        
        return vector_store
        
    except Exception as e:
        logger.error(f"Enhanced document addition failed: {e}")
        # Fallback to basic addition
        return await _add_document_basic(document, db)

async def _add_document_basic(document: Document, db: AsyncSession):
    """Fallback basic document addition"""
    
    try:
        vector_store = await _create_basic_vector_store(document.user_id, db)
        
        if vector_store and document.content:
            texts = [document.content]
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            docs = text_splitter.create_documents(texts)
            vector_store.add_documents(docs)
        
        return vector_store
        
    except Exception as e:
        logger.error(f"Basic document addition failed: {e}")
        return None

async def search_documents_with_context(
    user_id: str, 
    query: str, 
    db: AsyncSession,
    k: int = 5
) -> List[str]:
    """
    Enhanced document search with user learning context
    """
    try:
        # Get enhanced vector store
        vector_store = await get_user_vector_store(user_id, db)
        
        if not vector_store:
            return []
        
        # Initialize memory manager for search tracking
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        memory_manager = AsyncSafeEnhancedMemoryManager(db, user)
        
        # Enhanced search with user profile context
        user_profile = await memory_manager._get_user_learning_profile_safe()
        
        # Modify query based on user interests
        enhanced_query = await _enhance_query_with_profile(query, user_profile)
        
        # Perform similarity search
        docs = vector_store.similarity_search(enhanced_query, k=k)
        
        # Track search behavior
        await memory_manager.save_user_behavior_safe(
            action_type="document_search",
            context={
                "query": query,
                "enhanced_query": enhanced_query,
                "results_count": len(docs),
                "timestamp": datetime.utcnow().isoformat()
            },
            success=len(docs) > 0
        )
        
        return [doc.page_content for doc in docs]
        
    except Exception as e:
        logger.error(f"Enhanced document search failed: {e}")
        return []

async def _enhance_query_with_profile(query: str, user_profile) -> str:
    """Enhance search query with user profile context"""
    
    try:
        enhanced_parts = [query]
        
        # Add relevant skills if query is job-related
        if any(term in query.lower() for term in ["job", "position", "role", "career"]):
            if user_profile and user_profile.preferences:
                skills = [key.replace("cv_skill_", "") 
                         for key in user_profile.preferences.keys() 
                         if key.startswith("cv_skill_")]
                if skills:
                    enhanced_parts.append(f"skills: {' '.join(skills[:3])}")
        
        # Add industry context
        if user_profile and user_profile.preferences:
            industry = user_profile.preferences.get("preferred_industry")
            if industry and industry.lower() not in query.lower():
                enhanced_parts.append(f"industry: {industry}")
        
        return " ".join(enhanced_parts)
        
    except Exception:
        return query 