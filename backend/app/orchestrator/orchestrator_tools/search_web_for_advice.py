import logging
from typing import Optional
from datetime import datetime
import httpx
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class WebSearchInput(BaseModel):
    query: str = Field(description="The search query for current information.")
    context: Optional[str] = Field(default=None, description="Optional context about why this search is needed.")

# Step 2: Define the core logic as a plain async function.
async def _search_web_for_advice(query: str, context: Optional[str] = None) -> str:
    """The underlying implementation for searching the web for up-to-date information."""
    try:
        search_query = f"{query} {context or ''} {datetime.now().year}".strip()
        log.info(f"🔍 Searching web for: '{search_query}'")
        
        encoded_query = quote_plus(search_query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.get(search_url, follow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for link in soup.find_all('a', class_='result__a', limit=3):
                title = link.get_text(strip=True)
                snippet_elem = link.find_next_sibling('a', class_='result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                if title and snippet:
                    results.append(f"**{title}**\n{snippet}")
            
            if not results:
                return "❌ No relevant information found from the web search."
            
            return f"🌐 **Latest Information on: {query}**\n\n" + "\n\n".join(results)
        
    except httpx.HTTPStatusError as e:
        log.error(f"HTTP error during web search for '{query}': {e}", exc_info=True)
        return f"❌ Web search failed with status code: {e.response.status_code}. The service may be temporarily unavailable."
    except Exception as e:
        log.error(f"Error in _search_web_for_advice for query '{query}': {e}", exc_info=True)
        return "❌ An unexpected error occurred while searching the web."

# Step 3: Manually construct the Tool object with the explicit schema.
search_web_for_advice = Tool(
    name="search_web_for_advice",
    description="Searches the web for up-to-date information, advice, and guidance on career-related topics.",
    func=_search_web_for_advice,
    args_schema=WebSearchInput
)