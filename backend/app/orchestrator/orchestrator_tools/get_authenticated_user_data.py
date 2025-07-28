import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, constr
from langchain_core.tools import Tool

from app.models_db import User
from app.internal_api import make_internal_api_call

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class GetUserDataInput(BaseModel):
    # FIX: The keyword argument for the regex is 'pattern', not 'regex'.
    endpoint: constr(pattern=r"^\/api\/(users\/me|resume|users\/me\/documents)$") = Field(
        description="The API endpoint to access. Allowed values: '/api/users/me', '/api/resume', '/api/users/me/documents'."
    )

# Step 2: Define the core logic as a plain async function.
async def _get_authenticated_user_data(endpoint: str, user: User, db: AsyncSession) -> str:
    """The underlying implementation for accessing protected user data endpoints."""
    try:
        data = await make_internal_api_call(endpoint, user, db)
        
        if not data:
            return f"⚠️ No data returned from endpoint: {endpoint}"

        # Use a simple, clean JSON representation for the agent.
        # The agent can then decide how to present this to the user.
        pretty_json = json.dumps(data, indent=2)
        return f"**Data from {endpoint}:**\n```json\n{pretty_json}\n```"
            
    except Exception as e:
        log.error(f"Error in _get_authenticated_user_data for endpoint {endpoint}, user {user.id}: {e}", exc_info=True)
        return f"❌ Error accessing {endpoint}: {str(e)}"

# Step 3: Manually construct the Tool object with the explicit schema.
get_authenticated_user_data = Tool(
    name="get_authenticated_user_data",
    description="Accesses protected user endpoints to get user profile, resume, or document data. Use this to get the user's current information.",
    func=_get_authenticated_user_data,
    args_schema=GetUserDataInput
)
