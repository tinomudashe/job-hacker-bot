import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from langchain_core.tools import Tool

from app.models_db import User

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema (even if empty).
class GetLocationInput(BaseModel):
    pass

# Step 2: Define the core logic as a plain async function.
async def _get_user_location_context(user: User, db: AsyncSession) -> str:
    """The underlying implementation for getting user's location based on their IP address."""
    try:
        if user.address:
            return f"User's location is already known: {user.address}."

        async with httpx.AsyncClient() as client:
            response = await client.get("https://ipinfo.io/json", timeout=5.0)
            response.raise_for_status()
            data = response.json()

        city = data.get("city")
        country = data.get("country")
        
        if not city or not country:
            return "Could not determine a specific city and country from the IP address."

        location_str = f"{city}, {country}"
        
        # Update user's profile with this location
        user.address = location_str
        await db.commit()
        log.info(f"Updated user {user.id} location to {user.address}")
        return f"✅ Location identified as {location_str} and saved to your profile."
        
    except httpx.RequestError as e:
        log.error(f"Network error while retrieving location info for user {user.id}: {e}", exc_info=True)
        return "❌ Network error: Unable to retrieve location information at this time."
    except Exception as e:
        log.error(f"Error in _get_user_location_context for user {user.id}: {e}", exc_info=True)
        return "❌ An unexpected error occurred while determining your location."

# Step 3: Manually construct the Tool object with the explicit schema.
get_user_location_context = Tool(
    name="get_user_location_context",
    description="Gets the user's current location based on their IP address to provide local job market context. Only use if the user's location is not already known.",
    func=_get_user_location_context,
    args_schema=GetLocationInput
)