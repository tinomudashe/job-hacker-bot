from typing import Optional, List, Dict
from langchain_core.tools import tool
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from ..certification_input import Certification

log = logging.getLogger(__name__)

@tool
async def add_certification(
    db: AsyncSession,
    user: User,
    certification_name: str,
    issuing_organization: str,
    issue_date: Optional[str] = None,
    expiration_date: Optional[str] = None,
    credential_id: Optional[str] = None,
    credential_url: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Add a certification entry to resume with detailed variables.
    
    Args:
        certification_name: Name of certification (e.g., "AWS Solutions Architect", "Google Analytics Certified")
        issuing_organization: Organization that issued it (e.g., "Amazon Web Services", "Google")
        issue_date: When received (e.g., "January 2023", "2023-01")
        expiration_date: When expires (e.g., "January 2026", "Does not expire")
        credential_id: Certification ID/number
        credential_url: URL to verify certification
        description: Additional details about the certification
    
    Returns:
        Success message with certification details
    """
    if not db or not user:
        return "❌ Error: Database session and user must be provided to add certification."

    try:
        db_resume, resume_data = await get_or_create_resume(db, user)

        if not resume_data:
            return "❌ Error: Could not find or create a resume for the user."

        # Ensure certifications list exists
        if not hasattr(resume_data, 'certifications') or resume_data.certifications is None:
            resume_data.certifications = []
        
        # Build certification details
        cert_details = []
        if issue_date:
            cert_details.append(f"Issued: {issue_date}")
        if expiration_date:
            cert_details.append(f"Expires: {expiration_date}")
        if credential_id:
            cert_details.append(f"Credential ID: {credential_id}")
        if credential_url:
            cert_details.append(f"Verify: {credential_url}")
        if description:
            cert_details.append(f"Description: {description}")
        
        full_description = "\n".join(cert_details) if cert_details else ""
        
        new_cert = Certification(id=str(uuid.uuid4()), **cert_data)

        resume_data.certifications.append(new_cert)
        db_resume.data = resume_data.dict()
        flag_modified(db_resume, "data")

        # --- COMMIT AND VERIFY ---
        await db.commit()
        await db.refresh(db_resume)

        added_cert = next((cert for cert in db_resume.data['certifications'] if cert['id'] == new_cert.id), None)

        if added_cert and added_cert['name'] == new_cert.name:
            log.info(f"SUCCESSFULLY VERIFIED write for certification: {new_cert.name}")
            return f"✅ Certification '{new_cert.name}' was successfully added and verified."
        else:
            raise Exception(f"DATABASE VERIFICATION FAILED for certification: {new_cert.name}")

    except Exception as e:
        await db.rollback()
        log.error(f"Error adding certification: {e}")
        return f"❌ DATABASE ERROR: The attempt to add a certification failed. Details: {str(e)}"
