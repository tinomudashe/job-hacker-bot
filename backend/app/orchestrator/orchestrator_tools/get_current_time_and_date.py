from langchain_core.tools import tool
import logging
from datetime import datetime

@tool
async def get_current_time_and_date() -> str:
    """Gets the current date and time for temporal context."""
    now = datetime.now()
    return f"Current date and time is: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"
