from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
import shutil
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models_db import Document, User
from app.dependencies import get_current_user
from app.vector_store import add_document_to_vector_store

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
):
    token = authorization.split(" ")[1]
    user = await get_current_user(token=token, db=db)
    
    try:
        file_path = Path("uploads") / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        db_document = Document(
            user_id=user.id,
            name=file.filename,
            type=file.content_type,
            vector_store_path=str(file_path)
        )
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)

        await add_document_to_vector_store(db_document, db)

        return {"filename": file.filename, "path": str(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {e}") 