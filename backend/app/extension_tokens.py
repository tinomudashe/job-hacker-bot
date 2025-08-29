"""
Extension Access Token Management
Handles creation, validation, and revocation of personal access tokens for Chrome extension
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import hashlib
from sqlalchemy import Column, String, DateTime, Boolean, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.dependencies import get_current_user
from app.models_db import Base
import uuid

router = APIRouter(prefix="/api/extension-tokens", tags=["extension-tokens"])

# Pydantic models
class TokenCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = None  # None means no expiration

class TokenResponse(BaseModel):
    id: str
    name: str
    token: Optional[str] = None  # Only returned when creating
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool

class TokenListResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool

# Database model
class ExtensionToken(Base):
    __tablename__ = "extension_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

def generate_token():
    """Generate a secure random token"""
    # Generate 32 bytes of random data and convert to hex
    return f"jhb_{secrets.token_hex(32)}"

def hash_token(token: str) -> str:
    """Hash a token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()

@router.post("/", response_model=TokenResponse)
async def create_token(
    token_data: TokenCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new personal access token for the Chrome extension"""
    try:
        # Generate the token
        plain_token = generate_token()
        token_hash = hash_token(plain_token)
        
        # Calculate expiration if specified
        expires_at = None
        if token_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=token_data.expires_in_days)
        
        # Create token record
        token = ExtensionToken(
            user_id=current_user.external_id,  # Use external_id from User object
            name=token_data.name,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        db.add(token)
        await db.commit()
        await db.refresh(token)
        
        # Return the token (only time the plain token is shown)
        return TokenResponse(
            id=token.id,
            name=token.name,
            token=plain_token,  # Return plain token only on creation
            created_at=token.created_at,
            last_used=token.last_used,
            expires_at=token.expires_at,
            is_active=token.is_active
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create token: {str(e)}"
        )

@router.get("/", response_model=List[TokenListResponse])
async def list_tokens(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all tokens for the current user"""
    try:
        result = await db.execute(
            select(ExtensionToken)
            .filter(ExtensionToken.user_id == current_user.external_id)
            .order_by(ExtensionToken.created_at.desc())
        )
        tokens = result.scalars().all()
        
        return [
            TokenListResponse(
                id=token.id,
                name=token.name,
                created_at=token.created_at,
                last_used=token.last_used,
                expires_at=token.expires_at,
                is_active=token.is_active
            )
            for token in tokens
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tokens: {str(e)}"
        )

@router.delete("/{token_id}")
async def revoke_token(
    token_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke a personal access token"""
    try:
        result = await db.execute(
            select(ExtensionToken)
            .filter(
                ExtensionToken.id == token_id,
                ExtensionToken.user_id == current_user.external_id
            )
        )
        token = result.scalar_one_or_none()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        # Soft delete - mark as inactive
        token.is_active = False
        await db.commit()
        
        return {"message": "Token revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke token: {str(e)}"
        )

@router.post("/verify")
async def verify_token(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Verify if a token is valid (used by extension)"""
    try:
        # Extract token from Bearer header
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
        
        plain_token = authorization.replace("Bearer ", "")
        token_hash = hash_token(plain_token)
        
        # Find the token
        result = await db.execute(
            select(ExtensionToken)
            .filter(
                ExtensionToken.token_hash == token_hash,
                ExtensionToken.is_active == True
            )
        )
        token = result.scalar_one_or_none()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Check expiration
        if token.expires_at and token.expires_at < datetime.utcnow():
            token.is_active = False
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Update last used
        token.last_used = datetime.utcnow()
        await db.commit()
        
        return {
            "valid": True,
            "user_id": token.user_id,
            "token_name": token.name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify token: {str(e)}"
        )

# Middleware to authenticate extension requests
async def verify_extension_token(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Middleware to verify extension tokens in API calls"""
    authorization = request.headers.get("Authorization", "")
    if not authorization or not authorization.startswith("Bearer jhb_"):
        # Not an extension token, let other auth methods handle it
        return None
    
    try:
        plain_token = authorization.replace("Bearer ", "")
        token_hash = hash_token(plain_token)
        
        result = await db.execute(
            select(ExtensionToken)
            .filter(
                ExtensionToken.token_hash == token_hash,
                ExtensionToken.is_active == True
            )
        )
        token = result.scalar_one_or_none()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid extension token"
            )
        
        # Check expiration
        if token.expires_at and token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Extension token has expired"
            )
        
        # Update last used
        token.last_used = datetime.utcnow()
        await db.commit()
        
        return {"id": token.user_id, "token_id": token.id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid extension token"
        )