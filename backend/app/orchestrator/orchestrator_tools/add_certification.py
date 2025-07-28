import logging
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import User
from .get_or_create_resume import get_or_create_resume
# FIX: Import 'Certification' from the correct central model file.
from ..education_input import Certification

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class AddCertificationInput(BaseModel):
    name: str = Field(description="The name of the certification.")
    authority: str = Field(description="The issuing organization.")
    issue_date: str = Field(description="The issue date, e.g., 'YYYY-MM'.")
    expiration_date: Optional[str] = Field(default=None, description="The expiration date, e.g., 'YYYY-MM'.")
    credential_id: Optional[str] = Field(default=None, description="The credential ID or number.")
    credential_url: Optional[str] = Field(default=None, description="A URL to verify the credential.")

# Step 2: Define the core logic as a plain async function.
async def _add_certification(
    db: AsyncSession, user: User, **kwargs
) -> str:
    """The underlying implementation for adding a new certification to the user's resume."""
    try:
        db_resume, resume_data = await get_or_create_resume(db, user)
        if isinstance(resume_data, str):  # Error case
            return resume_data

        if not hasattr(resume_data, 'certifications') or resume_data.certifications is None:
            resume_data.certifications = []
        
        # Create a new Certification object from the provided arguments
        new_cert = Certification(id=str(uuid.uuid4()), **kwargs)
        resume_data.certifications.append(new_cert)

        db_resume.data = resume_data.model_dump(exclude_none=True)
        attributes.flag_modified(db_resume, "data")

        await db.commit()
        await db.refresh(db_resume)

        log.info(f"Successfully added certification '{new_cert.name}' for user {user.id}")
        return f"✅ Certification '{new_cert.name}' was successfully added to your resume."

    except Exception as e:
        log.error(f"Error in _add_certification for user {user.id}: {e}", exc_info=True)
        await db.rollback()
        return f"❌ An error occurred while adding the certification: {e}"

# Step 3: Manually construct the Tool object with the explicit schema.
# FIX: Replaced the lambda with a direct reference to the named function `_add_certification`.
# This resolves the `TypeError` because `_add_certification` has the required `__name__` attribute.
add_certification = Tool(
    name="add_certification",
    description="Adds a new certification to the user's resume.",
    func=_add_certification,
    args_schema=AddCertificationInput
)
