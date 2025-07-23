from langchain_core.tools import tool
import logging
from typing import Optional
import httpx
from urllib.parse import quote_plus
from datetime import datetime
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

@tool
async def search_web_for_advice(
        query: str,
        context: Optional[str] = None
    ) -> str:
    """
    Search the web for up-to-date information, advice, and guidance.
    
    Use this tool when providing career advice, industry insights, latest trends,
    or any information that requires current, real-time data from the internet.
    
    Args:
        query: The search query for current information (e.g., "latest software engineering trends", 
                "how to negotiate salary in tech", "remote work best practices")
        context: Optional context about why this search is needed (e.g., "user asking for interview tips")
    
    Returns:
        Current information and insights from web search results
    """
    try:
        # Format search query for better results with current year
        current_year = datetime.now().year
        
        if context:
            search_query = f"{query} {context} {current_year}"
        else:
            search_query = f"{query} {current_year}"
        
        log.info(f"🔍 Web search for advice: '{search_query}'")
        
        # Use DuckDuckGo search (no API key needed)
        encoded_query = quote_plus(search_query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            response = await client.get(search_url, follow_redirects=True)
            
            if response.status_code != 200:
                return f"❌ Unable to fetch current information for '{query}' at the moment. I'll provide guidance based on established best practices instead."
            
            # Parse search results (basic HTML parsing)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search result snippets
            results = []
            result_links = soup.find_all('a', class_='result__a')[:5]  # Get first 5 results
            
            for link in result_links:
                title = link.get_text(strip=True)
                if title and len(title) > 10:  # Valid title
                    # Find the snippet for this result
                    result_container = link.find_parent('div', class_='result__body') or link.find_parent('div')
                    if result_container:
                        snippet_elem = result_container.find('a', class_='result__snippet')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        if snippet and len(snippet) > 20:
                            results.append(f"**{title}**\n{snippet}")
            
            if not results:
                return f"❌ No current information found for '{query}'. I'll provide general guidance based on my knowledge instead."
            
            search_results = "\n\n".join(results[:3])  # Use top 3 results
            
            # Format the results for career/advice context
            formatted_response = f"""🌐 **Latest Information on: {query}**

Based on current web search results:

{search_results}

💡 **How this applies to your situation:**
This up-to-date information can help inform your career decisions and strategies. Consider how these current trends and insights align with your professional goals and background."""
            
            log.info(f"✅ Web search completed for advice query: '{query}' - found {len(results)} results")
            return formatted_response
        
    except Exception as e:
        log.error(f"Error in web search for advice: {e}", exc_info=True)
        return f"❌ Unable to fetch current information for '{query}' at the moment. Let me provide guidance based on established best practices instead."