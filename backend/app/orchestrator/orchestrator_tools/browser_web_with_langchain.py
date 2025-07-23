from langchain_core.tools import tool
import logging
log = logging.getLogger(__name__)

from app.langchain_webbrowser import create_webbrowser_tool


@tool
async def browse_web_with_langchain(
        url: str,
        query: str = ""
    ) -> str:
        """
        Use the official LangChain WebBrowser tool to browse and extract information from web pages.
        
        This tool provides intelligent web browsing with AI-powered content extraction and summarization.
        It's particularly useful for extracting job information from job posting URLs.
        
        Args:
            url: The URL to browse and extract information from
            query: Optional specific query about what to find on the page (e.g., "job requirements", "salary information")
                  If empty, will provide a general summary of the page content
        
        Returns:
            Extracted and summarized information from the webpage, with relevant links if available
        """
        try:
            from app.langchain_webbrowser import create_webbrowser_tool
            
            log.info(f"Using official LangChain WebBrowser tool for URL: {url}")
            
            # Create the WebBrowser tool
            webbrowser_tool = create_webbrowser_tool()
            
            # Prepare input for WebBrowser tool
            # Format: "URL,query" or just "URL" for summary
            if query:
                browser_input = f"{url},{query}"
                log.info(f"WebBrowser query: '{query}'")
            else:
                browser_input = url
                log.info("WebBrowser mode: general summary")
            
            # Use the WebBrowser tool
            result = await webbrowser_tool.arun(browser_input)
            
            if result:
                log.info(f"WebBrowser tool successful for {url}")
                return f"🌐 **Web Content from {url}:**\n\n{result}"
            else:
                log.warning(f"WebBrowser tool returned empty result for {url}")
                return f"❌ Could not extract content from {url}. The page might be inaccessible or protected."
                
        except Exception as e:
            log.error(f"Error using LangChain WebBrowser tool for {url}: {e}")
            return f"❌ Error browsing {url}: {str(e)}. Please try again or use a different URL."