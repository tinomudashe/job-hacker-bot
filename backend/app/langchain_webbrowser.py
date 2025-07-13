#!/usr/bin/env python3
"""
Official LangChain Playwright browser toolkit implementation.
"""

import logging
from typing import Optional
from playwright.sync_api import sync_playwright
from langchain.tools import Tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class BrowserInput(BaseModel):
    """Input schema for the browser tool."""
    url: str = Field(..., description="The URL to navigate to and extract content from")

def _sync_browser_navigate(url: str) -> str:
    """Synchronous browser navigation and content extraction."""
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            try:
                # Create page with reasonable timeout
                page = browser.new_page()
                page.set_default_timeout(30000)  # 30 seconds
                
                # Navigate to URL
                logger.info(f"Navigating to: {url}")
                response = page.goto(url, wait_until='domcontentloaded')
                
                if response and response.status != 200:
                    logger.warning(f"Page returned status {response.status}")
                
                # Wait for content to load
                page.wait_for_load_state('networkidle', timeout=10000)
                
                # Extract content
                # Try to get the main content
                content_selectors = [
                    'main',
                    'article',
                    '[role="main"]',
                    '#content',
                    '.content',
                    'body'
                ]
                
                text_content = ""
                for selector in content_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        if elements:
                            for element in elements:
                                text = element.inner_text()
                                if text and len(text) > len(text_content):
                                    text_content = text
                    except Exception:
                        continue
                
                # Get page title
                title = page.title()
                
                # Get meta description if available
                meta_description = ""
                try:
                    meta_desc = page.query_selector('meta[name="description"]')
                    if meta_desc:
                        meta_description = meta_desc.get_attribute('content') or ""
                except Exception:
                    pass
                
                # Compile result
                result_parts = []
                if title:
                    result_parts.append(f"Title: {title}")
                if meta_description:
                    result_parts.append(f"Description: {meta_description}")
                if text_content:
                    # Limit content length
                    if len(text_content) > 5000:
                        text_content = text_content[:5000] + "..."
                    result_parts.append(f"Content:\n{text_content}")
                
                result = "\n\n".join(result_parts)
                
                if not result.strip():
                    result = f"Successfully navigated to {url} but no content could be extracted. The page might be using JavaScript rendering or require authentication."
                
                logger.info(f"Successfully extracted {len(result)} characters from {url}")
                return result
                
            finally:
                browser.close()
                
    except Exception as e:
        logger.error(f"Browser navigation error: {e}")
        return f"Error accessing {url}: {str(e)}. The page might be protected or require special handling."

def create_webbrowser_tool():
    """Create a web browser tool using synchronous Playwright."""
    return Tool(
        name="web_browser",
        description="Navigate to a URL and extract content from web pages. Useful for scraping job postings, company information, and other web content.",
        func=_sync_browser_navigate,
        args_schema=BrowserInput
    )

# Keep this for compatibility
async def get_playwright_browser_toolkit():
    """Compatibility function - returns None since we're using sync approach."""
    return None 