from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import shutil
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from pypdf import PdfReader
import io

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
        # Read the file content into memory
        content_bytes = await file.read()
        
        # Reset file pointer for saving
        await file.seek(0)

        # Save the file to disk
        file_path = Path("uploads") / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text content based on file type
        text_content = ""
        if file.content_type == "application/pdf" or file.filename.lower().endswith('.pdf'):
            try:
                # Extract text from PDF
                pdf_reader = PdfReader(io.BytesIO(content_bytes))
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
            except Exception as e:
                print(f"Error extracting PDF text: {e}")
                # Fallback to raw decode
                text_content = content_bytes.decode("utf-8", errors="ignore")
        else:
            # For non-PDF files, try to decode as text
            text_content = content_bytes.decode("utf-8", errors="ignore")
        
        db_document = Document(
            user_id=current_user.id,
            name=file.filename,
            type=file.content_type,
            content=text_content.strip(),  # Store extracted text
            vector_store_path=str(file_path)
        )
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)

        await add_document_to_vector_store(db_document, db)

        return {"filename": file.filename, "path": str(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {e}") 