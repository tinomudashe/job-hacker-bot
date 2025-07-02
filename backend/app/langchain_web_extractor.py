import logging
import re
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.tools import Tool
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

@dataclass
class LightweightJobExtraction:
    """Lightweight job information extracted using LangChain WebBrowser approach."""
    url: str
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary: Optional[str] = None
    job_type: Optional[str] = None
    raw_content: str = ""

class LangChainWebExtractor:
    """Lightweight web extraction using LangChain WebBrowser approach."""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-04-17", temperature=0.1)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by adding protocol if missing."""
        if not url:
            return url
        
        # If URL doesn't start with http:// or https://, add https://
        if not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        
        return url
    
    async def extract_job_from_url(self, url: str, query: str = "") -> Optional[LightweightJobExtraction]:
        """
        Extract job information from URL using LangChain WebBrowser approach.
        
        Args:
            url: Job posting URL
            query: Optional specific query for what to extract
            
        Returns:
            LightweightJobExtraction object or None if failed
        """
        try:
            # Normalize URL - add protocol if missing
            normalized_url = self._normalize_url(url)
            logger.info(f"Starting lightweight extraction for: {normalized_url}")
            
            # Step 1: Fetch and clean content
            raw_content = await self._fetch_content(normalized_url)
            if not raw_content:
                logger.warning(f"Failed to fetch content from {normalized_url}")
                return None
            
            # Step 2: If query is provided, use vector search approach
            if query:
                relevant_content = await self._vector_search_content(raw_content, query)
            else:
                # Use full content for general extraction
                relevant_content = raw_content[:4000]  # Limit for LLM context
            
            # Step 3: Extract structured job information
            job_extraction = await self._extract_job_details(normalized_url, relevant_content)
            
            if job_extraction:
                job_extraction.raw_content = raw_content[:1000]  # Store sample for debugging
                logger.info(f"Successfully extracted: {job_extraction.title} at {job_extraction.company}")
                return job_extraction
            else:
                logger.warning(f"Failed to extract job details from {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error in lightweight extraction for {url}: {e}")
            return None
    
    async def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch and clean web content."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                # Parse and clean HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    element.decompose()
                
                # Extract main content
                main_content = soup.find('main') or soup.find('article') or soup.find('body')
                if main_content:
                    text = main_content.get_text(separator=' ', strip=True)
                else:
                    text = soup.get_text(separator=' ', strip=True)
                
                # Clean up text
                text = re.sub(r'\s+', ' ', text).strip()
                
                return text
                
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None
    
    async def _vector_search_content(self, content: str, query: str) -> str:
        """Use vector search to find relevant content sections."""
        try:
            # Split content into chunks
            chunks = self.text_splitter.split_text(content)
            
            if not chunks:
                return content[:4000]
            
            # Create documents
            documents = [Document(page_content=chunk) for chunk in chunks]
            
            # Create vector store using async method
            vectorstore = await FAISS.afrom_documents(documents, self.embeddings)
            
            # Search for relevant chunks
            relevant_docs = vectorstore.similarity_search(query, k=3)
            
            # Combine relevant content
            relevant_content = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            return relevant_content
            
        except Exception as e:
            logger.warning(f"Vector search failed, using truncated content: {e}")
            return content[:4000]
    
    async def _extract_job_details(self, url: str, content: str) -> Optional[LightweightJobExtraction]:
        """Extract structured job information using LLM."""
        try:
            extraction_prompt = f"""
            You are an expert at extracting job information from web content. 
            
            Extract the following information from this job posting content:
            
            URL: {url}
            Content: {content}
            
            Please extract and return ONLY the following information in this exact format:
            
            TITLE: [Job title]
            COMPANY: [Company name]
            LOCATION: [Job location]
            DESCRIPTION: [Job description and responsibilities - keep concise but comprehensive]
            REQUIREMENTS: [Skills, qualifications, and requirements]
            SALARY: [Salary information if available, otherwise "Not specified"]
            JOB_TYPE: [Full-time, Part-time, Contract, Internship, etc. - if available, otherwise "Not specified"]
            
            Important:
            - Extract actual information from the content, don't make up details
            - If information is not available, use "Not specified"
            - Keep descriptions concise but informative
            - Focus on the most relevant job details
            """
            
            response = await self.llm.ainvoke(extraction_prompt)
            content_text = response.content
            
            # Parse the structured response
            job_info = self._parse_extraction_response(content_text)
            
            if job_info and job_info.get('title') and job_info.get('company'):
                return LightweightJobExtraction(
                    url=url,
                    title=job_info.get('title', 'Not specified'),
                    company=job_info.get('company', 'Not specified'),
                    location=job_info.get('location', 'Not specified'),
                    description=job_info.get('description', 'Not specified'),
                    requirements=job_info.get('requirements', 'Not specified'),
                    salary=job_info.get('salary'),
                    job_type=job_info.get('job_type')
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error extracting job details: {e}")
            return None
    
    def _parse_extraction_response(self, response_text: str) -> Dict[str, str]:
        """Parse the structured LLM response."""
        job_info = {}
        
        patterns = {
            'title': r'TITLE:\s*(.+?)(?=\n[A-Z]+:|$)',
            'company': r'COMPANY:\s*(.+?)(?=\n[A-Z]+:|$)',
            'location': r'LOCATION:\s*(.+?)(?=\n[A-Z]+:|$)',
            'description': r'DESCRIPTION:\s*(.+?)(?=\n[A-Z]+:|$)',
            'requirements': r'REQUIREMENTS:\s*(.+?)(?=\n[A-Z]+:|$)',
            'salary': r'SALARY:\s*(.+?)(?=\n[A-Z]+:|$)',
            'job_type': r'JOB_TYPE:\s*(.+?)(?=\n[A-Z]+:|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and value.lower() not in ['not specified', 'not available', 'n/a']:
                    job_info[key] = value
                else:
                    job_info[key] = None if key in ['salary', 'job_type'] else 'Not specified'
        
        return job_info

# Tool creation for LangChain integration
def create_langchain_web_tool() -> Tool:
    """Create a LangChain tool for lightweight web extraction."""
    extractor = LangChainWebExtractor()
    
    async def web_extract(input_str: str) -> str:
        """
        Extract job information from a URL.
        Input should be: "URL,optional_query" or just "URL"
        """
        try:
            parts = input_str.split(',', 1)
            url = parts[0].strip()
            query = parts[1].strip() if len(parts) > 1 else ""
            
            result = await extractor.extract_job_from_url(url, query)
            
            if result:
                return f"""
Job Title: {result.title}
Company: {result.company}
Location: {result.location}
Description: {result.description}
Requirements: {result.requirements}
Salary: {result.salary or 'Not specified'}
Job Type: {result.job_type or 'Not specified'}
URL: {result.url}
"""
            else:
                return f"Failed to extract job information from {url}"
                
        except Exception as e:
            return f"Error extracting job information: {str(e)}"
    
    return Tool(
        name="lightweight_web_extractor",
        description="Useful for extracting job information from URLs. Input should be a URL, optionally followed by a comma and specific query about what to find.",
        func=web_extract
    )

# Convenience function
async def extract_job_lightweight(url: str, query: str = "") -> Optional[LightweightJobExtraction]:
    """Extract job information using lightweight approach."""
    extractor = LangChainWebExtractor()
    return await extractor.extract_job_from_url(url, query) 