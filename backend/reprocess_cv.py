#!/usr/bin/env python3
"""
Script to reprocess uploaded CV/Resume documents to extract text content.
This is useful for documents that were uploaded before PDF text extraction was implemented.

Usage:
    python reprocess_cv.py                     # Process all PDFs for current user
    python reprocess_cv.py --document-id 123   # Process specific document
    python reprocess_cv.py --user-id abc123    # Process all PDFs for specific user
"""

import asyncio
import argparse
import sys
from pathlib import Path
from pypdf import PdfReader
import io

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db_context
from app.models_db import Document, User
from app.cv_processor import cv_processor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF file."""
    text_content = ""
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
    return text_content.strip()


async def reprocess_document(db: AsyncSession, document: Document):
    """Reprocess a single document to extract text content."""
    logger.info(f"Processing document: {document.name} (ID: {document.id})")
    
    # Handle missing or incorrect vector_store_path
    if not document.vector_store_path:
        # Try multiple path patterns
        possible_paths = [
            Path("uploads") / document.name,
            Path("uploads") / document.user_id / f"{document.id}_{document.name}",
            Path("uploads") / document.user_id / document.name,
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found file at: {path}")
                file_path = path
                # Update the database with the correct path
                document.vector_store_path = str(path)
                break
        
        if not file_path:
            logger.warning(f"File not found in any expected location for document: {document.name}")
            return False
    else:
        file_path = Path(document.vector_store_path)
    
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False
    
    # Check if it's a PDF
    if not (document.type == "application/pdf" or document.name.lower().endswith('.pdf')):
        logger.info(f"Skipping non-PDF document: {document.name}")
        return False
    
    # Extract text from the PDF
    extracted_text = await extract_pdf_text(str(file_path))
    
    if not extracted_text:
        logger.warning(f"No text extracted from {document.name}")
        return False
    
    # Update the document with extracted text
    old_content_preview = document.content[:100] if document.content else "None"
    document.content = extracted_text
    
    logger.info(f"Updated document {document.name}:")
    logger.info(f"  Old content preview: {old_content_preview}")
    logger.info(f"  New content length: {len(extracted_text)} characters")
    
    await db.commit()
    return True


async def main():
    parser = argparse.ArgumentParser(description='Reprocess uploaded CV documents to extract text')
    parser.add_argument('--document-id', type=str, help='Process specific document by ID')
    parser.add_argument('--user-id', type=str, help='Process all documents for specific user')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without making changes')
    
    args = parser.parse_args()
    
    async with get_db_context() as db:
        # Build query based on arguments
        query = select(Document)
        
        if args.document_id:
            # Process specific document
            query = query.where(Document.id == args.document_id)
            logger.info(f"Processing document with ID: {args.document_id}")
        elif args.user_id:
            # Process all documents for specific user
            query = query.where(Document.user_id == args.user_id)
            logger.info(f"Processing all documents for user: {args.user_id}")
        else:
            # Process all PDF documents in the system
            # Filter to only PDFs
            query = query.where(
                (Document.type == "application/pdf") | 
                (Document.name.ilike('%.pdf'))
            )
            logger.info("Processing all PDF documents in the system")
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        if not documents:
            logger.info("No documents found to process")
            return
        
        logger.info(f"Found {len(documents)} document(s) to process")
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            for doc in documents:
                logger.info(f"Would process: {doc.name} (User: {doc.user_id}, Type: {doc.type})")
        else:
            processed = 0
            failed = 0
            
            for doc in documents:
                try:
                    success = await reprocess_document(db, doc)
                    if success:
                        processed += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Error processing document {doc.id}: {e}")
                    failed += 1
            
            logger.info(f"\nProcessing complete:")
            logger.info(f"  Successfully processed: {processed}")
            logger.info(f"  Failed or skipped: {failed}")


if __name__ == "__main__":
    asyncio.run(main())