from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models_db import Document, User
from app.dependencies import get_current_active_user
from datetime import datetime
import os
import uuid
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
    # Save file
    doc_id = str(uuid.uuid4())
    user_dir = UPLOAD_DIR / db_user.id
    user_dir.mkdir(exist_ok=True)
    file_path = user_dir / f"{doc_id}_{file.filename}"
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
    # Build FAISS index
    embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    docs = [LCDocument(page_content=chunk) for chunk in chunks]
    faiss_dir = user_dir / f"faiss_{doc_id}"
    faiss_dir.mkdir(exist_ok=True)
    vectorstore = FAISS.from_documents(docs, embedding)
    vectorstore.save_local(str(faiss_dir))
    # Store document metadata
    now = datetime.utcnow()
    doc = Document(
        id=doc_id,
        user_id=db_user.id,
        type=doc_type,
        name=name,
        content=None,  # Optionally store text
        vector_store_path=str(faiss_dir),
        date_created=now,
        date_updated=now
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

@router.get("/documents", response_model=List[DocumentOut])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    List all documents for the authenticated user.
    """
    result = await db.execute(
        select(Document).where(Document.user_id == db_user.id)
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