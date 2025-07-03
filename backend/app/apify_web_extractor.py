#!/usr/bin/env python3
"""
Official Apify tool implementation for job application system.
This uses the Apify RAG Web Browser Actor for web scraping.
"""

import logging
from typing import Optional, List
from dataclasses import dataclass
import re

from langchain_apify import ApifyWrapper

logger = logging.getLogger(__name__)

@dataclass
class ApifyJobExtraction:
    """Job information extracted using the Apify RAG Web Browser Actor."""
    url: str
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary: Optional[str] = None
    job_type: Optional[str] = None
    raw_content: str = ""

class ApifyWebExtractor:
    """Apify tool for job extraction."""
    
    def __init__(self):
        """Initialize with the Apify RAG Web Browser Actor."""
        self.apify = ApifyWrapper()
        logger.info("Initialized Apify RAG Web Browser Actor")
    
    async def extract_job_from_url(self, url: str) -> Optional[ApifyJobExtraction]:
        """
        Extract job information from a URL using the Apify RAG Web Browser Actor.
        
        Args:
            url: Job posting URL
            
        Returns:
            ApifyJobExtraction object or None if failed
        """
        try:
            logger.info(f"Starting Apify extraction for: {url}")
            
            # Run the Apify RAG Web Browser Actor
            loader = self.apify.call_actor(
                actor_id="apify/rag-web-browser",
                run_input={"urls": [url], "outputFormat": "markdown"},
                dataset_mapping_function=lambda item: Document(
                    page_content=item["markdown"], metadata={"source": item["url"]}
                ),
            )
            
            documents = loader.load()
            
            if not documents:
                logger.warning(f"Apify returned no documents for {url}")
                return None
            
            # Use the first document's content for extraction
            raw_content = documents[0].page_content
            
            # Parse the result and extract structured job information
            job_extraction = await self._parse_apify_result(url, raw_content)
            
            if job_extraction:
                logger.info(f"Successfully extracted job: {job_extraction.title} at {job_extraction.company}")
                return job_extraction
            else:
                logger.warning(f"Failed to parse job details from Apify result for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error in Apify extraction for {url}: {e}")
            return None
    
    async def _parse_apify_result(self, url: str, apify_result: str) -> Optional[ApifyJobExtraction]:
        """Parse the Apify tool result into structured job information."""
        # This part will be similar to the previous implementation, using an LLM to parse the text
        # For now, we'll just return a simplified version
        # You can add the LLM parsing logic here for more detailed extraction
        
        # Simple parsing for demonstration
        title_match = re.search(r'#\s*(.*)', apify_result)
        title = title_match.group(1).strip() if title_match else "Not specified"
        
        return ApifyJobExtraction(
            url=url,
            title=title,
            company="Not specified",
            location="Not specified",
            description=apify_result,
            requirements="Not specified",
            raw_content=apify_result[:1000]
        )

# Convenience function
async def extract_job_with_apify(url: str) -> Optional[ApifyJobExtraction]:
    """Extract job information using Apify RAG Web Browser Actor."""
    extractor = ApifyWebExtractor()
    return await extractor.extract_job_from_url(url) 