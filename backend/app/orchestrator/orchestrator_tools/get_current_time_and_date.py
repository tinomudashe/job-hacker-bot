import logging
from datetime import datetime
from pydantic import BaseModel
from langchain_core.tools import Tool

# Step 1: Define the explicit Pydantic input schema (even if empty).
class GetTimeInput(BaseModel):
    pass

# Step 2: Define the core logic as a plain async function.
async def _get_current_time_and_date() -> str:
    """The underlying implementation for getting the current date and time."""
    now = datetime.now()
    return f"Current date and time is: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"

# Step 3: Manually construct the Tool object with the explicit schema.
get_current_time_and_date = Tool(
    name="get_current_time_and_date",
    description="Gets the current date and time for temporal context.",
    func=_get_current_time_and_date,
    args_schema=GetTimeInput
)
