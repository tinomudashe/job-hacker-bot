import faiss
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from app.models_db import Document, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def get_user_vector_store(user_id: str, db: AsyncSession):
    # This is a placeholder for a more robust vector store management system
    # In a real application, you would store the vector store in a persistent location
    # and load it when needed.
    
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
    vector_store = FAISS.from_documents(docs, embeddings)
    
    return vector_store

async def add_document_to_vector_store(document: Document, db: AsyncSession):
    # This is a placeholder for a more robust vector store management system
    # In a real application, you would update the existing vector store
    # instead of recreating it every time.
    
    vector_store = await get_user_vector_store(document.user_id, db)
    
    if vector_store:
        texts = [document.content] if document.content else []
        if texts:
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            docs = text_splitter.create_documents(texts)
            vector_store.add_documents(docs)
    
    return vector_store 