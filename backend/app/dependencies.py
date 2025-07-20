from fastapi import Depends, HTTPException, Query, status, WebSocket, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
import re
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from app.db import get_db
from app.models_db import User
from app.clerk import verify_token, ClerkUser
from typing import Optional

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def create_valid_email(user_id: str) -> str:
    """
    Create a valid email from an Auth0 user ID.
    
    Args:
        user_id: The Auth0 user ID (e.g., 'auth0|1234567890' or 'hmcRCt3f35DJC2NF0iVipwgrub1jlgTS@clients')
    
    Returns:
        A valid email address.
    """
    if '@clients' in user_id:
        clean_id = user_id.split('@')[0]
        return f"client_{clean_id}@auth0-client.com"
        
    # For regular users, extract the part after the last '|' or use the whole id
    clean_id = user_id.split('|')[-1]
    
    # Remove any non-alphanumeric characters
    clean_id = re.sub(r'[^a-zA-Z0-9]', '', clean_id)
    
    # Take first 20 characters to keep it reasonable length
    clean_id = clean_id[:20]
    
    return f"user_{clean_id}@example.com"


def extract_token_from_request(request: Request, token_from_header: Optional[str] = None) -> Optional[str]:
    """
    Extract Clerk token from either Authorization header or cookies.
    
    Args:
        request: FastAPI request object
        token_from_header: Token from OAuth2 scheme (Authorization header)
    
    Returns:
        Token string or None if not found
    """
    # First try the Authorization header
    if token_from_header:
        return token_from_header
    
    # Then try cookies (common Clerk cookie names)
    clerk_cookie_names = [
        '__session',  # Common Clerk session cookie
        '__clerk_session',
        'clerk-session',
        '__clerk_token',
    ]
    
    for cookie_name in clerk_cookie_names:
        token = request.cookies.get(cookie_name)
        if token:
            logger.info(f"Found token in cookie: {cookie_name}")
            return token
    
    # Try to extract from custom Authorization header formats
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix
    
    logger.warning("No authentication token found in request")
    return None


async def get_user_from_token_data(token_data: ClerkUser, db: AsyncSession) -> User:
    """
    Given validated token data from Clerk, find or create the corresponding user in our database.
    """
    user_result = await db.execute(select(User).where(User.external_id == token_data.sub))
    user = user_result.scalar_one_or_none()
    
    if user is None:
        logger.info(f"User with external_id {token_data.sub} not found. Creating new user.")
        
        email = token_data.email
        first_name = token_data.first_name
        last_name = token_data.last_name
        picture = token_data.picture
        name = " ".join(filter(None, [first_name, last_name])) or "New User"

        user = User(
            external_id=token_data.sub, 
            email=email,
            name=name,
            picture=picture,
            first_name=first_name,
            last_name=last_name,
            phone=None,
            address=None,
            linkedin=None,
            preferred_language=None,
            date_of_birth=None,
            profile_headline=None,
            skills=None,
            profile_picture_url=picture
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify the auth token and get the current user.
    This is used for regular HTTP endpoints.
    Now supports both Authorization header and cookie-based authentication.
    """
    try:
        # Extract token from various sources
        auth_token = extract_token_from_request(request, token)
        
        if not auth_token:
            logger.warning("No authentication token found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        clerk_user: ClerkUser = await verify_token(auth_token)
        if not clerk_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = await db.execute(select(User).where(User.external_id == clerk_user.sub))
        user = result.scalar_one_or_none()
        
        # This block ensures the user profile is always synchronized with Clerk.
        # It handles both new user creation and updates for existing users.
        if user is None:
            # If the user does not exist in the local database, create a new record.
            # This ensures that a user's profile is populated on their first login.
            logger.info(f"User with external_id {clerk_user.sub} not found. Creating new user.")
            user = User(
                external_id=clerk_user.sub,
                email=clerk_user.email,
                name=f"{clerk_user.first_name or ''} {clerk_user.last_name or ''}".strip() or "New User",
                first_name=clerk_user.first_name,
                last_name=clerk_user.last_name,
                picture=clerk_user.picture,
                active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # If the user already exists, check for null or empty fields in the local
            # database and populate them with data from Clerk's token. This ensures
            # that we enrich the user's profile without overwriting existing data.
            update_needed = False
            if not user.email and clerk_user.email:
                user.email = clerk_user.email
                update_needed = True
            
            # Populate name only if it's empty or the default "New User"
            new_name = f"{clerk_user.first_name or ''} {clerk_user.last_name or ''}".strip()
            if not user.name or user.name == "New User":
                if new_name:
                    user.name = new_name
                    update_needed = True

            if not user.first_name and clerk_user.first_name:
                user.first_name = clerk_user.first_name
                update_needed = True

            if not user.last_name and clerk_user.last_name:
                user.last_name = clerk_user.last_name
                update_needed = True

            if not user.picture and clerk_user.picture:
                user.picture = clerk_user.picture
                update_needed = True
            
            # If any fields were updated, commit the changes to the database.
            if update_needed:
                logger.info(f"User profile for {user.external_id} enriched from Clerk.")
                await db.commit()
                await db.refresh(user)
            
        logger.info(f"Successfully authenticated user: {user.external_id}")
        return user
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    This is used for regular HTTP endpoints.
    """
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_user_ws(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency for WebSocket endpoints.
    Verifies Clerk token from query parameters and returns the active user.
    """
    token_data = await verify_token(token)
    user = await get_user_from_token_data(token_data, db)
    if not user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_user_from_ws(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Verify the auth token and get the current user.
    This is used for WebSocket connections.
    """
    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        clerk_user: ClerkUser = await verify_token(token)
        if not clerk_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        result = await db.execute(select(User).where(User.external_id == clerk_user.sub))
        user = result.scalar_one_or_none()

        if not user:
            # Create new user if they don't exist
            user = User(
                external_id=clerk_user.sub,
                email=clerk_user.email,
                name=f"{clerk_user.first_name or ''} {clerk_user.last_name or ''}".strip(),
                first_name=clerk_user.first_name,
                last_name=clerk_user.last_name,
                picture=clerk_user.picture,
                active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user
    except Exception as e:
        logger.error(f"Error in get_current_user_from_ws: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None 