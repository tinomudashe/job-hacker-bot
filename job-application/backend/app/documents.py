from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models_db import Document, User
from app.dependencies import get_current_active_user
from app.cv_processor import cv_processor, CVExtractionResult
from app.enhanced_memory import EnhancedMemoryManager
from datetime import datetime
import os
import uuid
import asyncio
from pathlib import Path
from PyPDF2 import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document as LCDocument
from typing import List, Optional
from pydantic import BaseModel
import shutil
import logging

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter()
logger = logging.getLogger(__name__)

class DocumentOut(BaseModel):
    id: str
    type: str
    name: str
    date_created: datetime
    date_updated: datetime

    class Config:
        from_attributes = True

class CVUploadResponse(BaseModel):
    document: DocumentOut
    extracted_info: Optional[CVExtractionResult] = None
    profile_updated: bool = False
    auto_extracted_fields: List[str] = []
    personalized_insights: Optional[str] = None

@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),  # 'resume', 'cover_letter', or 'generic'
    name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    if doc_type not in ("resume", "cover_letter", "generic"):
        raise HTTPException(status_code=400, detail="Invalid document type. Must be 'resume', 'cover_letter', or 'generic'.")
    
    logger.info(f"Starting document upload: {name} ({doc_type}) for user {db_user.id}")
    
    # Save file
    doc_id = str(uuid.uuid4())
    user_dir = UPLOAD_DIR / db_user.id
    user_dir.mkdir(exist_ok=True)
    file_path = user_dir / f"{doc_id}_{file.filename}"
    
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Extract text
        if file.filename.lower().endswith(".pdf"):
            try:
                pdf = PdfReader(str(file_path))
                text = "".join(page.extract_text() or "" for page in pdf.pages)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing PDF: {e}")
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error reading file: {e}")
        
        # Build FAISS index with enhanced embeddings
        embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        
        # Smart chunking based on document type and user preferences
        chunk_size = _get_optimal_chunk_size(doc_type, len(text))
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        docs = [LCDocument(page_content=chunk) for chunk in chunks]
        
        faiss_dir = user_dir / f"faiss_{doc_id}"
        faiss_dir.mkdir(exist_ok=True)
        
        # Use async FAISS methods to prevent greenlet errors
        vectorstore = await FAISS.afrom_documents(docs, embedding)
        
        # Run save_local in thread executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, vectorstore.save_local, str(faiss_dir)
        )
        
        # Store document metadata FIRST (avoid transaction conflicts)
        now = datetime.utcnow()
        doc = Document(
            id=doc_id,
            user_id=db_user.id,
            type=doc_type,
            name=name,
            content=text,
            vector_store_path=str(faiss_dir),
            date_created=now,
            date_updated=now
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        return doc
        
    except Exception as e:
        # Ensure transaction rollback on main error
        try:
            await db.rollback()
        except Exception:
            pass
            
        logger.error(f"Error processing document upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.post("/documents/cv-upload", response_model=CVUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv_with_extraction(
    file: UploadFile = File(...),
    name: str = Form(...),
    auto_update_profile: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Simplified CV upload without enhanced memory features to avoid greenlet errors
    """
    
    try:
        # Save file
        doc_id = str(uuid.uuid4())
        user_dir = UPLOAD_DIR / db_user.id
        user_dir.mkdir(exist_ok=True)
        file_path = user_dir / f"{doc_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Enhanced text extraction
        if file.filename and file.filename.lower().endswith(".pdf"):
            try:
                pdf = PdfReader(str(file_path))
                text = "".join(page.extract_text() or "" for page in pdf.pages)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing PDF: {e}")
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error reading file: {e}")
        
        # Store document metadata with basic FAISS processing
        now = datetime.utcnow()
        doc = Document(
            id=doc_id,
            user_id=db_user.id,
            type="resume",
            name=name,
            content=text,
            vector_store_path=None,  # Will be added after FAISS processing
            date_created=now,
            date_updated=now
        )
        db.add(doc)
        await db.commit()
        # Skip refresh to avoid greenlet issues - we have all the data we need
        
        # Basic FAISS processing (without enhanced features)
        try:
            embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
            
            # Smart chunking
            chunk_size = _get_optimal_chunk_size("resume", len(text))
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            docs = [LCDocument(page_content=chunk) for chunk in chunks]
            
            faiss_dir = user_dir / f"faiss_{doc_id}"
            faiss_dir.mkdir(exist_ok=True)
            
            # Use async FAISS methods to prevent greenlet errors
            vectorstore = await FAISS.afrom_documents(docs, embedding)
            
            # Run save_local in thread executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, vectorstore.save_local, str(faiss_dir)
            )
            
            # Update document with FAISS path using direct SQL to avoid refresh issues
            from sqlalchemy import update, text
            stmt = update(Document).where(Document.id == doc_id).values(
                vector_store_path=str(faiss_dir),
                date_updated=text('now()')
            )
            await db.execute(stmt)
            await db.commit()
            
        except Exception as e:
            logger.warning(f"FAISS processing failed but document was saved: {e}")
        
        logger.info(f"CV uploaded successfully: {name} for user {db_user.id}")
        
        return CVUploadResponse(
            document=DocumentOut(
                id=doc_id,
                type="resume",
                name=name,
                date_created=now,
                date_updated=now
            ),
            extracted_info=None,
            profile_updated=False,
            auto_extracted_fields=[],
            personalized_insights="CV uploaded successfully! Enhanced features will be available soon."
        )
        
    except Exception as e:
        # Ensure transaction rollback on main error
        try:
            await db.rollback()
        except Exception:
            pass
            
        logger.error(f"Error processing CV upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process CV: {str(e)}")

async def _analyze_document_with_context(
    content: str, 
    doc_type: str, 
    user_profile, 
    memory_manager: Optional[EnhancedMemoryManager]
) -> dict:
    """Analyze document content with user learning context"""
    
    analysis = {
        "content_type": doc_type,
        "word_count": len(content.split()),
        "key_themes": [],
        "relevance_score": 0.0
    }
    
    try:
        # Analyze based on user preferences and job search patterns
        if user_profile.job_search_patterns:
            common_keywords = user_profile.job_search_patterns.get("common_keywords", [])
            
            # Check content relevance to user's job interests
            relevance_matches = sum(1 for keyword in common_keywords if keyword.lower() in content.lower())
            analysis["relevance_score"] = min(relevance_matches / max(len(common_keywords), 1), 1.0)
            
        # Extract key themes based on document type
        if doc_type == "resume":
            analysis["key_themes"] = _extract_resume_themes(content)
        elif doc_type == "cover_letter":
            analysis["key_themes"] = _extract_cover_letter_themes(content)
        
        return analysis
        
    except Exception as e:
        logger.warning(f"Document analysis failed: {e}")
        return analysis

async def _generate_cv_insights_with_context(
    content: str,
    user_profile,
    memory_manager: Optional[EnhancedMemoryManager]
) -> Optional[str]:
    """Generate personalized CV insights based on user's job search patterns"""
    
    try:
        insights = []
        
        # Analyze based on user's job search history
        if user_profile.job_search_patterns:
            common_roles = user_profile.job_search_patterns.get("common_job_titles", [])
            preferred_locations = user_profile.job_search_patterns.get("common_search_locations", [])
            
            if common_roles:
                insights.append(f"Your CV content aligns well with your interest in {', '.join(common_roles[:3])} roles.")
            
            if preferred_locations:
                insights.append(f"Consider highlighting remote work experience since you often search for positions in {', '.join(preferred_locations[:2])}.")
        
        # Analyze based on interaction patterns
        if user_profile.interaction_patterns:
            detail_preference = user_profile.interaction_patterns.get("preferred_detail_level", "moderate")
            if detail_preference == "detailed":
                insights.append("Based on your preference for detailed information, consider expanding on specific achievements and metrics in your CV.")
        
        # Success-based recommendations
        if user_profile.success_metrics:
            success_rate = user_profile.success_metrics.get("job_search_success_rate", 0)
            if success_rate < 0.3:
                insights.append("Consider optimizing your CV with more industry-specific keywords to improve job search success.")
        
        if insights:
            return "\n".join([f"• {insight}" for insight in insights])
        
        return None
        
    except Exception as e:
        logger.warning(f"CV insights generation failed: {e}")
        return None

async def _learn_from_cv_content(content: str, memory_manager: Optional[EnhancedMemoryManager]):
    """Learn user preferences from CV content for future recommendations"""
    
    if not memory_manager:
        return  # Skip learning if memory manager is not available
    
    try:
        # Extract skills from CV
        skills = _extract_skills_from_cv(content)
        if skills:
            # Save dominant skills as preferences
            for skill in skills[:5]:  # Top 5 skills
                try:
                    await memory_manager.save_user_preference_safe(f"cv_skill_{skill.lower()}", "true")
                except Exception as e:
                    logger.warning(f"Failed to save skill preference for {skill}: {e}")
                    continue
        
        # Extract experience level
        experience_years = _estimate_experience_years(content)
        if experience_years:
            try:
                await memory_manager.save_user_preference_safe("experience_years", str(experience_years))
            except Exception as e:
                logger.warning(f"Failed to save experience years: {e}")
        
        # Extract industry keywords
        industry = _extract_industry_keywords(content)
        if industry:
            try:
                await memory_manager.save_user_preference_safe("preferred_industry", industry)
            except Exception as e:
                logger.warning(f"Failed to save industry preference: {e}")
            
    except Exception as e:
        logger.warning(f"CV learning failed: {e}")

def _get_optimal_chunk_size(doc_type: str, content_length: int) -> int:
    """Determine optimal chunk size based on document type and length"""
    
    if doc_type == "resume":
        return min(800, max(400, content_length // 10))
    elif doc_type == "cover_letter":
        return min(600, max(300, content_length // 8))
    else:
        return 500

def _extract_resume_themes(content: str) -> List[str]:
    """Extract key themes from resume content"""
    themes = []
    content_lower = content.lower()
    
    # Technical skills
    if any(term in content_lower for term in ["python", "javascript", "sql", "programming"]):
        themes.append("technical_skills")
    
    # Leadership
    if any(term in content_lower for term in ["led", "managed", "supervised", "leadership"]):
        themes.append("leadership")
    
    # Project management
    if any(term in content_lower for term in ["project", "agile", "scrum", "delivery"]):
        themes.append("project_management")
    
    return themes

def _extract_cover_letter_themes(content: str) -> List[str]:
    """Extract key themes from cover letter content"""
    themes = []
    content_lower = content.lower()
    
    if "passion" in content_lower or "enthusiastic" in content_lower:
        themes.append("enthusiasm")
    
    if "experience" in content_lower or "background" in content_lower:
        themes.append("experience_focused")
    
    if "achieve" in content_lower or "goal" in content_lower:
        themes.append("results_oriented")
    
    return themes

def _extract_skills_from_cv(content: str) -> List[str]:
    """Extract technical and professional skills from CV content"""
    skills = []
    content_lower = content.lower()
    
    # Common technical skills
    tech_skills = ["python", "javascript", "java", "sql", "aws", "docker", "kubernetes", 
                   "react", "angular", "node.js", "mongodb", "postgresql", "git"]
    
    for skill in tech_skills:
        if skill in content_lower:
            skills.append(skill)
    
    return skills

def _estimate_experience_years(content: str) -> Optional[int]:
    """Estimate years of experience from CV content"""
    import re
    
    # Look for explicit year mentions
    year_patterns = [
        r"(\d+)\+?\s*years?\s*(?:of\s*)?experience",
        r"(\d+)\+?\s*years?\s*in",
        r"over\s*(\d+)\s*years?",
    ]
    
    for pattern in year_patterns:
        matches = re.findall(pattern, content.lower())
        if matches:
            try:
                return int(matches[0])
            except ValueError:
                continue
    
    # Estimate from date ranges
    current_year = datetime.now().year
    years_mentioned = re.findall(r'\b(20\d{2})\b', content)
    
    if years_mentioned:
        years = [int(year) for year in years_mentioned if int(year) <= current_year]
        if years:
            return current_year - min(years)
    
    return None

def _extract_industry_keywords(content: str) -> Optional[str]:
    """Extract industry from CV content"""
    content_lower = content.lower()
    
    industries = {
        "technology": ["software", "programming", "developer", "engineer", "tech", "it"],
        "finance": ["finance", "banking", "investment", "accounting", "financial"],
        "healthcare": ["healthcare", "medical", "hospital", "clinical", "patient"],
        "marketing": ["marketing", "advertising", "social media", "branding", "campaign"],
        "education": ["education", "teaching", "academic", "university", "school"]
    }
    
    industry_scores = {}
    for industry, keywords in industries.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        if score > 0:
            industry_scores[industry] = score
    
    if industry_scores:
        return max(industry_scores, key=industry_scores.get)
    
    return None

@router.get("/documents", response_model=List[DocumentOut])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    List all documents for the authenticated user.
    """
    result = await db.execute(
        select(Document).where(Document.user_id == db_user.id).order_by(Document.date_created.desc())
    )
    documents = result.scalars().all()
    return documents

@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Get details for a specific document.
    """
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == db_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.post("/documents/{doc_id}/reprocess-cv")
async def reprocess_cv_extraction(
    doc_id: str,
    auto_update_profile: bool = True,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Reprocess a document with CV extraction (useful for documents uploaded before this feature)
    """
    # Get the document
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == db_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Find the original file
    user_dir = UPLOAD_DIR / db_user.id
    file_path = None
    for f in user_dir.glob(f"{doc_id}_*"):
        if f.is_file():
            file_path = f
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="Original file not found")
    
    try:
        # Extract information using CV processor
        extraction_result = await cv_processor.extract_cv_information(file_path)
        
        # Update user profile if requested
        profile_updated = False
        auto_extracted_fields = []
        
        if auto_update_profile and extraction_result.confidence_score > 0.5:
            profile_updated, auto_extracted_fields = await _update_user_profile_from_cv(
                db_user, extraction_result, db
            )
            await db.commit()
        
        return {
            "document_id": doc_id,
            "extracted_info": extraction_result,
            "profile_updated": profile_updated,
            "auto_extracted_fields": auto_extracted_fields
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing CV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reprocess CV: {str(e)}")

@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Delete a document and its associated files.
    """
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == db_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete associated files
    user_dir = UPLOAD_DIR / db_user.id
    # Find the original file (we don't store its exact name, so we have to search)
    for f in user_dir.glob(f"{doc_id}_*"):
        if f.is_file():
            f.unlink()
            break
            
    # Delete FAISS vector store directory
    if document.vector_store_path:
        faiss_dir = Path(document.vector_store_path)
        if faiss_dir.exists() and faiss_dir.is_dir():
            shutil.rmtree(faiss_dir)
            
    await db.delete(document)
    await db.commit()
    return

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None

@router.put("/documents/{doc_id}", response_model=DocumentOut)
async def update_document(
    doc_id: str,
    doc_update: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Update a document's name or type.
    """
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == db_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc_update.name:
        document.name = doc_update.name
    if doc_update.type:
        if doc_update.type not in ("resume", "cover_letter", "generic"):
            raise HTTPException(status_code=400, detail="Invalid document type. Must be 'resume', 'cover_letter', or 'generic'.")
        document.type = doc_update.type
        
    document.date_updated = datetime.utcnow()
    
    await db.commit()
    await db.refresh(document)
    return document

@router.get("/documents/insights", response_model=dict)
async def get_personalized_document_insights(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Get personalized insights about user's documents based on learning profile
    """
    try:
        # Initialize Enhanced Memory Manager
        try:
            from app.enhanced_memory import AsyncSafeEnhancedMemoryManager
            memory_manager = AsyncSafeEnhancedMemoryManager(db, db_user, skills=db_user.skills)
            user_profile = await memory_manager._get_user_learning_profile_safe()
            logger.info("Enhanced Memory Manager initialized for document insights")
        except Exception as e:
            logger.warning(f"Enhanced Memory Manager initialization failed: {e}")
            memory_manager = None
            user_profile = None
        
        # Get user documents
        doc_result = await db.execute(
            select(Document).where(Document.user_id == db_user.id)
        )
        documents = doc_result.scalars().all()
        
        if not documents:
            return {
                "insights": "No documents found. Upload your resume or cover letters to get personalized insights!",
                "recommendations": [],
                "document_analysis": {}
            }
        
        # Analyze documents with user context
        insights = await _generate_comprehensive_document_insights(
            documents, user_profile, memory_manager
        )
        
        # Track insights access
        if memory_manager:
            await memory_manager.save_user_behavior_safe(
                action_type="document_insights_access",
                context={
                    "documents_count": len(documents),
                    "insights_generated": len(insights.get("recommendations", [])),
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=True
            )
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating document insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate document insights")

@router.get("/documents/{doc_id}/analysis", response_model=dict)
async def get_document_analysis(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Get detailed analysis of a specific document with personalized insights
    """
    try:
        # Get the document
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == db_user.id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Initialize Enhanced Memory Manager
        try:
            from app.enhanced_memory import AsyncSafeEnhancedMemoryManager
            memory_manager = AsyncSafeEnhancedMemoryManager(db, db_user, skills=db_user.skills)
        except Exception as e:
            logger.warning(f"Enhanced Memory Manager initialization failed: {e}")
            memory_manager = None
        
        if memory_manager:
            user_profile = await memory_manager._get_user_learning_profile_safe()
        else:
            user_profile = None
        
        # Analyze specific document
        analysis = await _analyze_single_document(document, user_profile, memory_manager)
        
        # Track document analysis access
        if memory_manager:
            await memory_manager.save_user_behavior_safe(
                action_type="single_document_analysis",
                context={
                    "document_id": doc_id,
                    "document_type": document.type,
                    "analysis_depth": len(analysis.get("sections", [])),
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=True
            )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze document")

async def _generate_comprehensive_document_insights(
    documents: List[Document],
    user_profile,
    memory_manager: Optional[EnhancedMemoryManager]
) -> dict:
    """Generate comprehensive insights about all user documents"""
    
    insights = {
        "summary": "",
        "recommendations": [],
        "document_analysis": {},
        "career_alignment": {},
        "optimization_tips": []
    }
    
    try:
        # Document type analysis
        doc_types = {}
        total_content_length = 0
        
        for doc in documents:
            doc_types[doc.type] = doc_types.get(doc.type, 0) + 1
            if doc.content:
                total_content_length += len(doc.content)
        
        insights["document_analysis"] = {
            "total_documents": len(documents),
            "document_types": doc_types,
            "average_content_length": total_content_length // len(documents) if documents else 0,
            "latest_update": max(doc.date_updated for doc in documents).isoformat() if documents else None
        }
        
        # Generate summary based on user profile
        summary_parts = []
        summary_parts.append(f"You have {len(documents)} documents uploaded.")
        
        if doc_types.get("resume", 0) > 0:
            summary_parts.append(f"Including {doc_types['resume']} resume(s)")
        if doc_types.get("cover_letter", 0) > 0:
            summary_parts.append(f"and {doc_types['cover_letter']} cover letter(s).")
        
        # Career alignment analysis
        if user_profile.job_search_patterns:
            job_patterns = user_profile.job_search_patterns
            common_roles = job_patterns.get("common_job_titles", [])
            
            if common_roles:
                # Analyze document relevance to job search patterns
                relevance_scores = []
                for doc in documents:
                    if doc.content:
                        score = sum(1 for role in common_roles 
                                  if role.lower() in doc.content.lower())
                        relevance_scores.append(score / max(len(common_roles), 1))
                
                avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
                
                insights["career_alignment"] = {
                    "target_roles": common_roles[:3],
                    "document_relevance_score": round(avg_relevance, 2),
                    "alignment_status": "High" if avg_relevance > 0.7 else "Medium" if avg_relevance > 0.4 else "Low"
                }
                
                if avg_relevance < 0.5:
                    insights["recommendations"].append(
                        f"Consider updating your documents to better align with your target roles: {', '.join(common_roles[:3])}"
                    )
        
        # Experience-based recommendations
        if user_profile.preferences:
            experience_years = user_profile.preferences.get("experience_years")
            industry = user_profile.preferences.get("preferred_industry")
            
            if experience_years:
                try:
                    years = int(experience_years)
                    if years < 2:
                        insights["recommendations"].append(
                            "As an early-career professional, focus on highlighting education, projects, and any internship experience."
                        )
                    elif years > 5:
                        insights["recommendations"].append(
                            "With your experience level, emphasize leadership roles and major achievements with quantifiable results."
                        )
                except ValueError:
                    pass
            
            if industry:
                insights["recommendations"].append(
                    f"Ensure your documents include industry-specific keywords for {industry.title()} roles."
                )
        
        # Interaction-based recommendations
        if user_profile.interaction_patterns:
            common_actions = user_profile.interaction_patterns.get("most_common_actions", {})
            
            if "job_search" in common_actions:
                insights["recommendations"].append(
                    "Since you frequently search for jobs, consider creating multiple tailored versions of your resume for different types of positions."
                )
        
        # Optimization tips based on document analysis
        resume_docs = [doc for doc in documents if doc.type == "resume"]
        if resume_docs:
            latest_resume = max(resume_docs, key=lambda x: x.date_updated)
            if latest_resume.content:
                insights["optimization_tips"].extend(
                    _generate_resume_optimization_tips(latest_resume.content, user_profile)
                )
        
        # Generate final summary
        insights["summary"] = " ".join(summary_parts)
        
        if insights["career_alignment"]:
            alignment = insights["career_alignment"]["alignment_status"]
            insights["summary"] += f" Your documents show {alignment.lower()} alignment with your job search goals."
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating comprehensive insights: {e}")
        return {
            "summary": "Unable to generate detailed insights at this time.",
            "recommendations": ["Try uploading more documents for better analysis."],
            "document_analysis": {},
            "career_alignment": {},
            "optimization_tips": []
        }

async def _analyze_single_document(
    document: Document,
    user_profile,
    memory_manager: Optional[EnhancedMemoryManager]
) -> dict:
    """Analyze a single document with personalized context"""
    
    analysis = {
        "document_info": {
            "name": document.name,
            "type": document.type,
            "created": document.date_created.isoformat(),
            "updated": document.date_updated.isoformat()
        },
        "content_analysis": {},
        "personalized_feedback": [],
        "improvement_suggestions": [],
        "relevance_score": 0.0
    }
    
    try:
        if not document.content:
            analysis["personalized_feedback"].append("Document content is not available for analysis.")
            return analysis
        
        content = document.content
        
        # Basic content analysis
        word_count = len(content.split())
        analysis["content_analysis"] = {
            "word_count": word_count,
            "character_count": len(content),
            "estimated_reading_time": f"{max(1, word_count // 200)} minutes"
        }
        
        # Document type specific analysis
        if document.type == "resume":
            analysis.update(await _analyze_resume_content(content, user_profile))
        elif document.type == "cover_letter":
            analysis.update(await _analyze_cover_letter_content(content, user_profile))
        
        # Relevance to user's job search patterns
        if user_profile.job_search_patterns:
            common_keywords = user_profile.job_search_patterns.get("common_keywords", [])
            if common_keywords:
                matches = sum(1 for keyword in common_keywords if keyword.lower() in content.lower())
                analysis["relevance_score"] = min(matches / len(common_keywords), 1.0)
        
        # Personalized feedback based on user profile
        if user_profile.preferences:
            industry = user_profile.preferences.get("preferred_industry")
            if industry:
                industry_keywords = _get_industry_keywords(industry)
                industry_matches = sum(1 for keyword in industry_keywords if keyword.lower() in content.lower())
                
                if industry_matches < 3:
                    analysis["improvement_suggestions"].append(
                        f"Consider adding more {industry.title()}-specific keywords to better match industry standards."
                    )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing single document: {e}")
        return analysis

async def _analyze_resume_content(content: str, user_profile) -> dict:
    """Analyze resume-specific content"""
    
    resume_analysis = {
        "sections_detected": [],
        "skills_found": [],
        "experience_indicators": [],
        "resume_feedback": []
    }
    
    content_lower = content.lower()
    
    # Detect common resume sections
    sections = {
        "experience": ["experience", "work history", "employment", "professional experience"],
        "education": ["education", "academic", "degree", "university", "college"],
        "skills": ["skills", "technical skills", "competencies", "proficiencies"],
        "projects": ["projects", "project experience", "key projects"],
        "achievements": ["achievements", "accomplishments", "awards", "honors"]
    }
    
    for section, keywords in sections.items():
        if any(keyword in content_lower for keyword in keywords):
            resume_analysis["sections_detected"].append(section)
    
    # Extract technical skills
    tech_skills = ["python", "javascript", "java", "sql", "aws", "docker", "git", "react", "angular"]
    found_skills = [skill for skill in tech_skills if skill in content_lower]
    resume_analysis["skills_found"] = found_skills
    
    # Experience indicators
    experience_patterns = ["years of experience", "led", "managed", "developed", "implemented", "designed"]
    found_indicators = [pattern for pattern in experience_patterns if pattern in content_lower]
    resume_analysis["experience_indicators"] = found_indicators
    
    # Generate feedback
    if len(resume_analysis["sections_detected"]) < 3:
        resume_analysis["resume_feedback"].append(
            "Consider adding more standard resume sections (Experience, Education, Skills, etc.)"
        )
    
    if not found_skills:
        resume_analysis["resume_feedback"].append(
            "Add more specific technical skills relevant to your target roles"
        )
    
    if not found_indicators:
        resume_analysis["resume_feedback"].append(
            "Include more action verbs and quantifiable achievements"
        )
    
    return resume_analysis

async def _analyze_cover_letter_content(content: str, user_profile) -> dict:
    """Analyze cover letter specific content"""
    
    cover_letter_analysis = {
        "tone_indicators": [],
        "structure_elements": [],
        "cover_letter_feedback": []
    }
    
    content_lower = content.lower()
    
    # Detect tone
    enthusiasm_words = ["excited", "passionate", "enthusiastic", "eager", "thrilled"]
    professional_words = ["experience", "qualified", "skills", "background", "expertise"]
    
    if any(word in content_lower for word in enthusiasm_words):
        cover_letter_analysis["tone_indicators"].append("enthusiastic")
    
    if any(word in content_lower for word in professional_words):
        cover_letter_analysis["tone_indicators"].append("professional")
    
    # Check structure elements
    if "dear" in content_lower or "hello" in content_lower:
        cover_letter_analysis["structure_elements"].append("greeting")
    
    if "sincerely" in content_lower or "regards" in content_lower:
        cover_letter_analysis["structure_elements"].append("closing")
    
    # Generate feedback
    if "enthusiastic" not in cover_letter_analysis["tone_indicators"]:
        cover_letter_analysis["cover_letter_feedback"].append(
            "Consider adding more enthusiasm and passion for the role"
        )
    
    if len(cover_letter_analysis["structure_elements"]) < 2:
        cover_letter_analysis["cover_letter_feedback"].append(
            "Ensure your cover letter has proper greeting and closing"
        )
    
    return cover_letter_analysis

def _generate_resume_optimization_tips(content: str, user_profile) -> List[str]:
    """Generate specific optimization tips for resume content"""
    
    tips = []
    content_lower = content.lower()
    
    # Length optimization
    word_count = len(content.split())
    if word_count < 300:
        tips.append("Your resume might be too brief. Consider expanding on your experience and achievements.")
    elif word_count > 800:
        tips.append("Your resume might be too lengthy. Focus on the most relevant and impactful information.")
    
    # Quantification check
    if not any(char.isdigit() for char in content):
        tips.append("Add quantifiable achievements (numbers, percentages, dollar amounts) to demonstrate impact.")
    
    # Action verbs check
    action_verbs = ["achieved", "created", "developed", "improved", "led", "managed", "increased"]
    if sum(1 for verb in action_verbs if verb in content_lower) < 3:
        tips.append("Use more strong action verbs to describe your accomplishments.")
    
    return tips

def _get_industry_keywords(industry: str) -> List[str]:
    """Get relevant keywords for a specific industry"""
    
    industry_keywords = {
        "technology": ["software", "programming", "development", "coding", "technical", "engineering", "database", "system"],
        "finance": ["financial", "analysis", "investment", "banking", "accounting", "risk", "portfolio", "audit"],
        "healthcare": ["patient", "clinical", "medical", "healthcare", "treatment", "diagnosis", "nursing", "hospital"],
        "marketing": ["marketing", "digital", "social media", "campaign", "branding", "advertising", "content", "strategy"],
        "education": ["teaching", "curriculum", "student", "academic", "education", "learning", "instruction", "assessment"]
    }
    
    return industry_keywords.get(industry.lower(), []) 