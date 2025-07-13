"""
Simple browser tool that runs Playwright in a subprocess to avoid event loop conflicts.
"""

import subprocess
import json
import tempfile
import os
import logging
from typing import Optional
from langchain.tools import Tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class BrowserInput(BaseModel):
    """Input schema for the browser tool."""
    url: str = Field(..., description="The URL to navigate to and extract content from")

def _create_playwright_script(url: str, output_file: str) -> str:
    """Create a Python script that runs Playwright and saves the result."""
    script_content = f'''
import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_url():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set a reasonable timeout
            page.set_default_timeout(30000)  # 30 seconds
            
            # Navigate to the URL
            await page.goto("{url}")
            
            # Wait for the page to load
            await page.wait_for_load_state("networkidle")
            
            # Get page content and title
            content = await page.content()
            title = await page.title()
            
            # Try to get text content as well
            text_content = await page.evaluate("document.body.innerText")
            
            result = {{
                "success": True,
                "url": "{url}",
                "title": title,
                "content": content,
                "text_content": text_content[:5000],  # Limit text content
                "content_length": len(content)
            }}
            
            await browser.close()
            return result
            
    except Exception as e:
        return {{
            "success": False,
            "url": "{url}",
            "error": str(e)
        }}

if __name__ == "__main__":
    result = asyncio.run(scrape_url())
    
    with open("{output_file}", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
'''
    return script_content

def _run_browser_subprocess(url: str) -> str:
    """Run Playwright in a subprocess to avoid event loop conflicts."""
    try:
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_output:
            output_file = temp_output.name
        
        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
            script_content = _create_playwright_script(url, output_file)
            temp_script.write(script_content)
            script_file = temp_script.name
        
        try:
            # Run the script in a subprocess
            logger.info(f"Running Playwright subprocess for URL: {url}")
            result = subprocess.run(
                ["python", script_file],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                logger.error(f"Subprocess failed with return code {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                return f"Browser subprocess failed: {result.stderr}"
            
            # Read the result from the output file
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get("success"):
                    title = data.get("title", "No title")
                    text_content = data.get("text_content", "")
                    content_length = data.get("content_length", 0)
                    
                    return f"Successfully scraped: {title}\nContent length: {content_length} characters\nText preview:\n{text_content[:1000]}..."
                else:
                    error = data.get("error", "Unknown error")
                    return f"Browser scraping failed: {error}"
            else:
                return "Browser subprocess completed but no output file found"
                
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_file)
                os.unlink(output_file)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        return "Browser operation timed out after 60 seconds"
    except Exception as e:
        logger.error(f"Error in browser subprocess: {e}")
        return f"Browser operation failed: {str(e)}"

def create_simple_browser_tool() -> Tool:
    """Create a simple browser tool that runs Playwright in a subprocess."""
    
    return Tool(
        name="web_browser",
        description="Navigate to a URL and extract content from web pages. Useful for scraping job postings, company information, and other web content. Runs in a separate process to avoid conflicts.",
        func=_run_browser_subprocess,
        args_schema=BrowserInput
    ) 