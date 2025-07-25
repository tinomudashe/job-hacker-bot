import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import uuid

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
from app.orchestrator.certification_input import Certification
from sqlalchemy.orm.attributes import flag_modified

log = logging.getLogger(__name__)

class AddCertificationInput(BaseModel):
    """Input for adding a certification to the user's resume."""
    name: str = Field(description="The name of the certification.")
    authority: str = Field(description="The organization that issued the certification.")
    issue_date: str = Field(description="The date the certification was issued, e.g., 'YYYY-MM-DD'.")

@tool(args_schema=AddCertificationInput)
async def add_certification(
    db: AsyncSession,
    user: User,
    name: str,
    authority: str,
    issue_date: str
) -> str:
    """Adds a new certification to the user's resume."""
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
