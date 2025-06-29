import os
import httpx
import logging
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import jwt  # PyJWT library
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLERK_ISSUER_URL = os.getenv("CLERK_ISSUER_URL")
ALGORITHMS = ["RS256"]

# Asynchronous cache for JWKS
_jwks_cache: List[Dict[str, Any]] = []

class ClerkUser(BaseModel):
    sub: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None

async def get_jwks() -> List[Dict[str, Any]]:
    """Asynchronously fetches and caches the JWKS from Clerk."""
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    if not CLERK_ISSUER_URL:
        raise HTTPException(status_code=500, detail="CLERK_ISSUER_URL not configured.")
    
    jwks_url = f"{CLERK_ISSUER_URL.rstrip('/')}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks_data = response.json()
            _jwks_cache = jwks_data.get("keys", [])
            return _jwks_cache
        except (httpx.RequestError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch or parse JWKS: {e}")
            raise HTTPException(status_code=500, detail="Could not retrieve signing keys from Clerk.")

async def verify_token(token: str) -> ClerkUser:
    """Asynchronously verifies a Clerk JWT."""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.exceptions.DecodeError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token header: {e}")

    jwks = await get_jwks()
    
    # Find the key that matches the token's 'kid'
    for key in jwks:
        if key.get("kid") == unverified_header.get("kid"):
            try:
                # Reconstruct the key in a format PyJWT understands
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=ALGORITHMS,
                    issuer=CLERK_ISSUER_URL,
                    leeway=60,
                )
                
                return ClerkUser(
                    sub=payload.get("sub"),
                    email=payload.get("email"),
                    first_name=payload.get("first_name"),
                    last_name=payload.get("last_name"),
                    picture=payload.get("picture"),
                )
            except jwt.exceptions.PyJWTError as e:
                # If this specific key fails, log it and continue.
                # It might be an old key, and another one in the JWKS might work.
                logger.warning(f"JWT validation failed with key {key.get('kid')}: {e}")
                # Invalidate cache in case of signature errors with a new key
                if isinstance(e, jwt.exceptions.InvalidSignatureError):
                    global _jwks_cache
                    _jwks_cache = []
                continue

    # If the loop completes without returning, no valid key was found
    raise HTTPException(status_code=401, detail="Unable to find a valid signing key for this token.") 