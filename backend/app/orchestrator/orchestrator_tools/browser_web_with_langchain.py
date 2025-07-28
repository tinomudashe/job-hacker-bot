import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from app.langchain_webbrowser import create_webbrowser_tool

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class BrowseWebInput(BaseModel):
    url: str = Field(description="The URL to browse.")
    query: Optional[str] = Field(default="", description="Specific query about what to find on the page.")

# Step 2: Define the core logic as a plain async function.
async def _browse_web_with_langchain(
        url: str,
        query: str = ""
    ) -> str:
    """The underlying implementation for browsing a web page and extracting information."""
    try:
        log.info(f"Browsing URL: {url} with query: '{query}'")
        
        webbrowser_tool = create_webbrowser_tool()
        
        browser_input = f"{url},{query}" if query else url
        
        result = await webbrowser_tool.arun(browser_input)
        
        if result:
            return f"🌐 **Web Content from {url}:**\n\n{result}"
        else:
            log.warning(f"WebBrowser tool returned empty result for {url}")
            return f"❌ Could not extract content from {url}. The page might be inaccessible."
            
    except Exception as e:
        log.error(f"Error in _browse_web_with_langchain for {url}: {e}", exc_info=True)
        return f"❌ Error browsing {url}: {str(e)}."

# Step 3: Manually construct the Tool object with the explicit schema.
browse_web_with_langchain = Tool(
    name="browse_web_with_langchain",
    description="Browse a web page to extract and summarize information. Useful for getting details from job posting URLs.",
    func=_browse_web_with_langchain,
    args_schema=BrowseWebInput
)