from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models_db import Document, User
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.dependencies import get_current_active_user
import os
from langchain.docstore.document import Document as LCDocument
from typing import List, Optional
from pydantic import BaseModel

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
        raise HTTPException(status_code=404, detail="No resume found for user")
    # Load FAISS index
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-004")
    vectorstore = FAISS.load_local(doc.vector_store_path, embedding, allow_dangerous_deserialization=True)
    # Retrieve relevant chunks
    relevant_docs = vectorstore.similarity_search(job_description, k=5)
    context = "\n".join([d.page_content for d in relevant_docs])
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