from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import shutil
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models_db import Document, User
from app.dependencies import get_current_active_user
from app.vector_store import add_document_to_vector_store

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file for the authenticated user.
    """
    try:
        # EDIT: Read the file content into memory. This is crucial for storing it
        # in the database, which allows the agent to access it later for context.
        content = await file.read()
        
        # FIX: The file pointer needs to be reset after the initial read, otherwise
        # the subsequent copy operation will fail because the pointer is at the end.
        await file.seek(0)

        file_path = Path("uploads") / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        db_document = Document(
            user_id=current_user.id,
            name=file.filename,
            type=file.content_type,
            # EDIT: Store the actual file content in the 'content' field.
            # This makes the document's text available for the agent's tools.
            content=content.decode("utf-8", errors="ignore"),
            vector_store_path=str(file_path)
        )
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)

        await add_document_to_vector_store(db_document, db)

        return {"filename": file.filename, "path": str(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {e}") 