#!/usr/bin/env python3
"""
Script to process uploaded CV documents and extract structured data to populate Resume fields.
This extracts experience, education, skills, etc. from CV text and saves them properly.

Usage:
    python process_cv_to_resume.py --user-id USER_ID      # Process for specific user
    python process_cv_to_resume.py --document-id DOC_ID   # Process specific document
"""

import asyncio
import argparse
import sys
from pathlib import Path
import logging
import json

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import attributes
from app.db import get_db_context
from app.models_db import Document, User, Resume
from app.cv_processor import cv_processor
from app.resume import fix_resume_data_structure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_document_to_resume(db: AsyncSession, document: Document, user: User):
    """Process a CV document to extract structured data and save to Resume."""
    logger.info(f"Processing CV document: {document.name} (ID: {document.id})")
    
    # Check if document has content
    if not document.content or document.content.strip() == "":
        logger.warning(f"Document {document.name} has no content")
        return False
    
    # Determine file path
    file_path = None
    if document.vector_store_path:
        # Try to find the actual file
        possible_paths = [
            Path(document.vector_store_path.replace('/faiss_', '/').replace('_faiss', '')),
            Path("uploads") / user.id / f"{document.id}_{document.name}",
            Path("uploads") / document.name,
        ]
        for path in possible_paths:
            if path.exists() and path.is_file():
                file_path = path
                break
    
    if not file_path:
        # Create temporary file from content
        temp_path = Path("uploads") / f"temp_{document.id}.txt"
        temp_path.write_text(document.content)
        file_path = temp_path
        logger.info(f"Created temporary file for processing: {temp_path}")
    
    try:
        # Extract CV information using the cv_processor
        logger.info("Extracting structured CV information...")
        cv_data = await cv_processor.extract_cv_information(file_path)
        
        # Clean up temp file if created
        if 'temp_' in str(file_path):
            file_path.unlink()
        
        # Get or create Resume record
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        if not db_resume:
            db_resume = Resume(user_id=user.id, data={})
            db.add(db_resume)
            logger.info("Created new Resume record")
        
        # Build resume data structure from extracted CV data
        resume_data = db_resume.data or {}
        
        # Update personal info
        if not resume_data.get('personalInfo'):
            resume_data['personalInfo'] = {}
        
        if cv_data.personal_info:
            personal_info = resume_data['personalInfo']
            if cv_data.personal_info.full_name:
                personal_info['name'] = cv_data.personal_info.full_name
            if cv_data.personal_info.email:
                personal_info['email'] = cv_data.personal_info.email
            if cv_data.personal_info.phone:
                personal_info['phone'] = cv_data.personal_info.phone
            if cv_data.personal_info.linkedin:
                personal_info['linkedin'] = cv_data.personal_info.linkedin
            if cv_data.personal_info.address:
                personal_info['location'] = cv_data.personal_info.address
            if cv_data.personal_info.profile_summary:
                personal_info['summary'] = cv_data.personal_info.profile_summary
        
        # Update experience (always update with new data)
        if cv_data.experience:
            resume_data['experience'] = []
            for exp in cv_data.experience:
                exp_dict = {
                    'id': str(hash(f"{exp.company}_{exp.job_title}"))[:8],
                    'jobTitle': exp.job_title,
                    'company': exp.company,
                    'dates': exp.duration,
                    'description': exp.description
                }
                resume_data['experience'].append(exp_dict)
            logger.info(f"Added {len(cv_data.experience)} experience entries")
        
        # Update education (always update with new data)
        if cv_data.education:
            resume_data['education'] = []
            for edu in cv_data.education:
                edu_dict = {
                    'id': str(hash(f"{edu.institution}_{edu.degree}"))[:8],
                    'degree': edu.degree,
                    'institution': edu.institution,
                    'dates': edu.graduation_year,
                    'description': edu.gpa if edu.gpa else ""
                }
                resume_data['education'].append(edu_dict)
            logger.info(f"Added {len(cv_data.education)} education entries")
        
        # Update skills
        if cv_data.skills:
            all_skills = []
            if cv_data.skills.technical_skills:
                all_skills.extend(cv_data.skills.technical_skills)
            if cv_data.skills.soft_skills:
                all_skills.extend(cv_data.skills.soft_skills)
            
            if all_skills:
                resume_data['skills'] = all_skills
                # Also update user skills field
                user.skills = ", ".join(all_skills[:10])  # Limit to first 10 skills
                logger.info(f"Added {len(all_skills)} skills")
        
        # Update projects (always update with new data)
        if hasattr(cv_data, 'projects') and cv_data.projects:
            resume_data['projects'] = []
            for proj in cv_data.projects:
                proj_dict = {
                    'id': str(hash(f"{proj.title}_{proj.description}"))[:8] if proj.title else str(hash(str(proj)))[:8],
                    'title': proj.title or "",
                    'description': proj.description or "",
                    'technologies': proj.technologies or "",
                    'url': proj.url or "",
                    'github': proj.github or "",
                    'dates': proj.duration or ""
                }
                resume_data['projects'].append(proj_dict)
            logger.info(f"Added {len(cv_data.projects)} projects")
        elif 'projects' not in resume_data:
            resume_data['projects'] = []
        
        # Update certifications (always update with new data)
        if cv_data.skills and cv_data.skills.certifications:
            resume_data['certifications'] = []
            for cert in cv_data.skills.certifications:
                # Handle both string and dict certifications
                if isinstance(cert, str):
                    cert_dict = {
                        'id': str(hash(cert))[:8],
                        'name': cert,
                        'issuer': "",
                        'date': "",
                        'description': "",
                        'url': "",
                        'credentialId': ""
                    }
                elif isinstance(cert, dict):
                    cert_dict = {
                        'id': str(hash(cert.get('name', str(cert))))[:8],
                        'name': cert.get('name', ''),
                        'issuer': cert.get('issuer', ''),
                        'date': cert.get('date', ''),
                        'description': cert.get('description', ''),
                        'url': cert.get('url', ''),
                        'credentialId': cert.get('credentialId', '')
                    }
                else:
                    continue
                resume_data['certifications'].append(cert_dict)
            logger.info(f"Added {len(cv_data.skills.certifications)} certifications")
        elif 'certifications' not in resume_data:
            resume_data['certifications'] = []
        
        # Update languages (always update with new data)
        if cv_data.skills and cv_data.skills.languages:
            resume_data['languages'] = []
            for lang in cv_data.skills.languages:
                # Handle both string and dict languages
                if isinstance(lang, str):
                    lang_dict = {
                        'id': str(hash(lang))[:8],
                        'language': lang,
                        'proficiency': ""
                    }
                elif isinstance(lang, dict):
                    lang_dict = {
                        'id': str(hash(lang.get('language', str(lang))))[:8],
                        'language': lang.get('language', ''),
                        'proficiency': lang.get('proficiency', '')
                    }
                else:
                    continue
                resume_data['languages'].append(lang_dict)
            logger.info(f"Added {len(cv_data.skills.languages)} languages")
        elif 'languages' not in resume_data:
            resume_data['languages'] = []
        
        # Initialize interests if not present
        if 'interests' not in resume_data:
            resume_data['interests'] = []
        
        # Fix and validate the resume data structure
        resume_data = fix_resume_data_structure(resume_data)
        
        # Save the updated resume data
        db_resume.data = resume_data
        attributes.flag_modified(db_resume, "data")
        
        # Update user profile fields if needed
        if cv_data.personal_info:
            if cv_data.personal_info.full_name and not user.name:
                user.name = cv_data.personal_info.full_name
            if cv_data.personal_info.email and not user.email:
                user.email = cv_data.personal_info.email
            if cv_data.personal_info.phone and not user.phone:
                user.phone = cv_data.personal_info.phone
            if cv_data.personal_info.linkedin and not user.linkedin:
                user.linkedin = cv_data.personal_info.linkedin
            if cv_data.personal_info.profile_summary and not user.profile_headline:
                user.profile_headline = cv_data.personal_info.profile_summary
        
        await db.commit()
        
        logger.info(f"Successfully processed CV and updated Resume for user {user.id}")
        logger.info(f"Resume now contains: {len(resume_data.get('experience', []))} experiences, "
                   f"{len(resume_data.get('education', []))} education entries, "
                   f"{len(resume_data.get('skills', []))} skills, "
                   f"{len(resume_data.get('projects', []))} projects, "
                   f"{len(resume_data.get('certifications', []))} certifications, "
                   f"{len(resume_data.get('languages', []))} languages")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing CV document {document.id}: {e}")
        await db.rollback()
        return False


async def main():
    parser = argparse.ArgumentParser(description='Process CV documents to extract and save structured Resume data')
    parser.add_argument('--document-id', type=str, help='Process specific document by ID')
    parser.add_argument('--user-id', type=str, help='Process all CV documents for specific user')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without making changes')
    
    args = parser.parse_args()
    
    if not args.document_id and not args.user_id:
        parser.error("Please specify either --document-id or --user-id")
    
    async with get_db_context() as db:
        if args.document_id:
            # Process specific document
            result = await db.execute(
                select(Document).where(
                    Document.id == args.document_id,
                    Document.type == "resume"
                )
            )
            document = result.scalars().first()
            
            if not document:
                logger.error(f"Resume document with ID {args.document_id} not found")
                return
            
            # Get the user
            user_result = await db.execute(select(User).where(User.id == document.user_id))
            user = user_result.scalars().first()
            
            if not user:
                logger.error(f"User {document.user_id} not found")
                return
            
            if args.dry_run:
                logger.info(f"DRY RUN: Would process document {document.name} for user {user.email}")
            else:
                success = await process_document_to_resume(db, document, user)
                if success:
                    logger.info("Processing completed successfully")
                else:
                    logger.error("Processing failed")
        
        elif args.user_id:
            # Process all CV documents for user
            user_result = await db.execute(select(User).where(User.id == args.user_id))
            user = user_result.scalars().first()
            
            if not user:
                logger.error(f"User with ID {args.user_id} not found")
                return
            
            # Get all resume documents for the user
            docs_result = await db.execute(
                select(Document).where(
                    Document.user_id == args.user_id,
                    Document.type == "resume"
                )
            )
            documents = docs_result.scalars().all()
            
            if not documents:
                logger.info(f"No resume documents found for user {user.email}")
                return
            
            logger.info(f"Found {len(documents)} resume document(s) for user {user.email}")
            
            if args.dry_run:
                logger.info("DRY RUN MODE - No changes will be made")
                for doc in documents:
                    logger.info(f"Would process: {doc.name}")
            else:
                processed = 0
                failed = 0
                
                for doc in documents:
                    success = await process_document_to_resume(db, doc, user)
                    if success:
                        processed += 1
                    else:
                        failed += 1
                
                logger.info(f"\nProcessing complete:")
                logger.info(f"  Successfully processed: {processed}")
                logger.info(f"  Failed: {failed}")


if __name__ == "__main__":
    asyncio.run(main())