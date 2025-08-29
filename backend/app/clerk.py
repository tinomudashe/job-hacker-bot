import os
import httpx
import logging
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

# Use the correct 'jose' library for all JWT operations
from jose import jwt, jwk
from jose.utils import base64url_decode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
CLERK_ISSUER_URL = os.getenv("CLERK_ISSUER_URL")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY") 
CLERK_API_URL = os.getenv("CLERK_API_URL")
ALGORITHMS = ["RS256"]

# Cache for JWKS
_jwks_cache: List[Dict[str, Any]] = []

class ClerkUser(BaseModel):
    sub: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None
    public_metadata: Dict[str, Any] = {}


async def get_jwks() -> List[Dict[str, Any]]:
    """
    Retrieves and caches the JSON Web Key Set (JWKS) from Clerk.
    """
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    if not CLERK_ISSUER_URL:
        logger.error("CLERK_ISSUER_URL not set")
        raise HTTPException(status_code=500, detail="Clerk issuer URL not configured")

    url = f"{CLERK_ISSUER_URL}/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            _jwks_cache = response.json()["keys"]
            return _jwks_cache
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch JWKS from Clerk")


async def verify_token(token: str) -> ClerkUser:
    """
    Verifies a Clerk JWT token using the python-jose library.
    """
    # Validate token format first
    if not token or not isinstance(token, str):
        logger.error("Token validation failed: Token is None or not a string")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if token has the correct number of segments (header.payload.signature)
    if token.count('.') != 2:
        logger.error(f"Invalid token format - wrong number of segments: {token[:20]}... (segments: {token.count('.')})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        
        rsa_key = {}
        for key in jwks:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = key
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Correctly construct the public key from the JWK dictionary
        public_key = jwk.construct(rsa_key, algorithm=ALGORITHMS[0])

        payload = jwt.decode(
            token,
            public_key,
            algorithms=ALGORITHMS,
            issuer=CLERK_ISSUER_URL,
            options={"verify_aud": False},
        )
        return ClerkUser(**payload)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error decoding token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_clerk_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a full user object from the Clerk API.
    """
    if not CLERK_SECRET_KEY or not CLERK_API_URL:
        logger.error("Clerk Secret Key or API URL is not configured. Cannot fetch user.")
        return None

    headers = {"Authorization": f"Bearer {CLERK_SECRET_KEY}"}
    url = f"{CLERK_API_URL}/v1/users/{user_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch user data from Clerk API for user {user_id}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching user data for {user_id}: {e}", exc_info=True)
        return None


async def verify_session_token(session_id: str) -> Optional[ClerkUser]:
    """
    Verifies a Clerk session ID and returns the user information.
    Used when the extension passes a session ID from the main app.
    """
    if not CLERK_SECRET_KEY or not CLERK_API_URL:
        logger.error("Clerk Secret Key or API URL is not configured.")
        return None
    
    headers = {"Authorization": f"Bearer {CLERK_SECRET_KEY}"}
    url = f"{CLERK_API_URL}/v1/sessions/{session_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            # Get session details
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            session_data = response.json()
            
            # Check if session is active
            if session_data.get("status") != "active":
                logger.warning(f"Session {session_id} is not active")
                return None
            
            # Get the user ID from session
            user_id = session_data.get("user_id")
            if not user_id:
                logger.error(f"No user_id found in session {session_id}")
                return None
            
            # Get user details
            user_data = await get_clerk_user(user_id)
            if not user_data:
                return None
            
            # Extract primary email
            email = None
            if user_data.get("email_addresses"):
                for email_addr in user_data["email_addresses"]:
                    if email_addr.get("id") == user_data.get("primary_email_address_id"):
                        email = email_addr.get("email_address")
                        break
            
            # Create ClerkUser object
            return ClerkUser(
                sub=user_id,
                email=email,
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                picture=user_data.get("profile_image_url"),
                public_metadata=user_data.get("public_metadata", {})
            )
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to verify session {session_id}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Error verifying session {session_id}: {e}", exc_info=True)
        return None


async def get_primary_email_address(user_id: str) -> Optional[str]:
    """
    Fetches a user's primary email address directly from the Clerk API.
    """
    if not CLERK_SECRET_KEY or not CLERK_API_URL:
        logger.error("Clerk Secret Key or API URL is not configured. Cannot fetch primary email.")
        return None
        
    headers = {"Authorization": f"Bearer {CLERK_SECRET_KEY}"}
    url = f"{CLERK_API_URL}/v1/users/{user_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            
            for email_info in user_data.get("email_addresses", []):
                if email_info.get("id") == user_data.get("primary_email_address_id"):
                    return email_info.get("email_address")
            
            return None
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch user data from Clerk API: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching user email: {e}", exc_info=True)
        return None


async def get_user_info(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Gets a user's information from Clerk.
    
    Args:
        user_id: The Clerk user ID
        
    Returns:
        User info dict if successful, None otherwise
    """
    if not CLERK_SECRET_KEY or not CLERK_API_URL:
        logger.error("Clerk Secret Key or API URL is not configured. Cannot get user info.")
        return None
        
    headers = {
        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{CLERK_API_URL}/v1/users/{user_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to get user info for {user_id}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting user info: {e}", exc_info=True)
        return None


async def update_user_metadata(user_id: str, public_metadata: Dict[str, Any]) -> bool:
    """
    Updates a user's public metadata in Clerk.
    
    Args:
        user_id: The Clerk user ID
        public_metadata: Dictionary of metadata to update
        
    Returns:
        True if successful, False otherwise
    """
    if not CLERK_SECRET_KEY or not CLERK_API_URL:
        logger.error("Clerk Secret Key or API URL is not configured. Cannot update metadata.")
        return False
        
    headers = {
        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{CLERK_API_URL}/v1/users/{user_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url, 
                headers=headers,
                json={"public_metadata": public_metadata}
            )
            response.raise_for_status()
            logger.info(f"Successfully updated metadata for user {user_id}")
            return True
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to update user metadata in Clerk: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while updating user metadata: {e}", exc_info=True)
        return False 