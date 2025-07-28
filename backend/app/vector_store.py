import asyncio
from datetime import datetime
import logging
from typing import List, Optional

from langchain_community.vectorstores.pgvector import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models_db import Document, User
import os

logger = logging.getLogger(__name__)

# --- Reusable Components ---
# Use the DATABASE_URL constructed from individual components
# Note: For PGVector's connection_string, we don't need the +asyncpg driver part.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

if all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    from urllib.parse import quote_plus
    encoded_password = quote_plus(DB_PASSWORD)
    CONNECTION_STRING = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
else:
    CONNECTION_STRING = None
    logger.warning("Database connection details for PGVector are not fully configured.")

EMBEDDINGS = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
# The dimension for the embedding model
VECTOR_DIMENSION = 768


async def get_user_vector_store(user_id: str, db: AsyncSession) -> Optional[PGVector]:
    """
    Gets a PGVector store for a user, ensuring it is synchronized with their documents.
    This function will clear any old entries for the user and re-populate the store
    with their current documents from the database.
    """
    if not CONNECTION_STRING:
        logger.error("Cannot create vector store: DATABASE_URL is not configured.")
        return None
        
    try:
        # Get all of the user's current documents from the main database
        doc_result = await db.execute(
            select(Document).where(Document.user_id == user_id)
        )
        documents = doc_result.scalars().all()

        if not documents:
            logger.warning(f"No documents found for user {user_id}. Vector store will be empty.")
            # Still return a store object so it can be added to later.
            return PGVector(
                connection_string=CONNECTION_STRING,
                embedding_function=EMBEDDINGS,
                collection_name=f"user_{user_id.replace('-', '_')}",
            )

        # Process documents into a format LangChain can use
        texts_for_embedding = []
        for doc in documents:
            if doc.content:
                # Add context to the document content for better retrieval
                doc_context = f"[{doc.type.upper()} DOCUMENT - {doc.name}]\n{doc.content}"
                texts_for_embedding.append(doc_context)
        
        if not texts_for_embedding:
            logger.info(f"No content found in documents for user {user_id}.")
            return None

        # Split documents into chunks for embedding
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs_for_vector_store = text_splitter.create_documents(texts_for_embedding)
        
        collection_name = f"user_{user_id.replace('-', '_')}"

        # Create the vector store.
        # This will use our Alembic-managed tables.
        # pre_delete_collection=True ensures that all old entries for this user are cleared
        # before adding the new ones, keeping the store perfectly in sync.
        # DEFINITIVE FIX: Use the ASYNCHRONOUS version of the method (`afrom_documents`) and AWAIT it.
        vector_store = await PGVector.afrom_documents(
            embedding=EMBEDDINGS,
            documents=docs_for_vector_store,
            collection_name=collection_name,
            connection_string=CONNECTION_STRING,
            pre_delete_collection=True,
        )
        
        logger.info(f"Successfully synchronized vector store for user {user_id} with {len(docs_for_vector_store)} chunks.")
        return vector_store
        
    except Exception as e:
        logger.error(f"Error synchronizing vector store for user {user_id}: {e}")
        return None

async def add_document_to_vector_store(document: Document, db: AsyncSession) -> Optional[PGVector]:
    """
    Adds a single document to the user's existing vector store.
    """
    if not CONNECTION_STRING:
        logger.error("Cannot add to vector store: DATABASE_URL is not configured.")
        return None

    try:
        # Initialize a vector store object pointed at the user's collection
        vector_store = PGVector(
            connection_string=CONNECTION_STRING,
            embedding_function=EMBEDDINGS,
            collection_name=f"user_{document.user_id.replace('-', '_')}",
        )

        # Process and chunk the single new document
        if document.content:
            doc_context = f"[{document.type.upper()} DOCUMENT - {document.name}]\n{document.content}"
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs_for_vector_store = text_splitter.create_documents([doc_context])

            # Add the new chunks to the existing collection in the database
            await vector_store.aadd_documents(docs_for_vector_store)
            logger.info(f"Successfully added document {document.id} to vector store for user {document.user_id}.")
        
        return vector_store

    except Exception as e:
        logger.error(f"Failed to add document {document.id} to vector store: {e}")
        return None

async def search_documents_with_context(
    user_id: str, 
    query: str, 
    db: AsyncSession,
    k: int = 5
) -> List[str]:
    """
    Performs a similarity search on a user's vector store.
    """
    if not CONNECTION_STRING:
        logger.error("Cannot search vector store: DATABASE_URL is not configured.")
        return []

    try:
        # Initialize a vector store object pointed at the user's collection
        vector_store = PGVector(
            connection_string=CONNECTION_STRING,
            embedding_function=EMBEDDINGS,
            collection_name=f"user_{user_id.replace('-', '_')}",
        )
        
        # Perform the similarity search
        results = await vector_store.asimilarity_search(query, k=k)
        
        logger.info(f"Found {len(results)} results for query in vector store for user {user_id}.")
        return [doc.page_content for doc in results]
        
    except Exception as e:
        # This can happen if the collection doesn't exist yet for a new user
        if "does not exist" in str(e):
             logger.warning(f"Collection for user {user_id} not found. Returning empty search results.")
        else:
            logger.error(f"Failed to search documents for user {user_id}: {e}")
        return [] 