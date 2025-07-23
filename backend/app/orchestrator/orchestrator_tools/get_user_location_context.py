from langchain_core.tools import tool
import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import User

log = logging.getLogger(__name__)

@tool
async def get_user_location_context(user: User, db: AsyncSession) -> str:
    """Gets user's location based on their IP address for local job market context."""
    try:
        # FIX: Use an asynchronous HTTP client to prevent blocking the event loop.
        async with httpx.AsyncClient() as client:
            response = await client.get("https://ipinfo.io/json", timeout=10.0)
            response.raise_for_status()
            data = response.json()

        city = data.get("city", "Unknown")
        region = data.get("region", "Unknown")
        country = data.get("country", "Unknown")
        
        location_str = f"Location: {city}, {region}, {country}"
        
        # Update user's profile with this location if it's missing
        if not user.address and city and city != "Unknown":
            user.address = f"{city}, {country}"
            db.add(user)
            await db.commit()
            await db.refresh(user)
            log.info(f"Updated user {user.id} location to {user.address}")
            return f"✅ Location identified as {location_str} and saved to profile."
        
        return f"✅ User location identified as: {location_str}"
        
    except Exception as e:
        log.error(f"Unable to retrieve location information: {e}", exc_info=True)
        return f"❌ Unable to retrieve location information: {str(e)}"