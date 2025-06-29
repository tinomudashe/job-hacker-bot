import logging
import re
import asyncio
from typing import Dict, Optional
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Comment
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from readability import Document

logger = logging.getLogger(__name__)

@dataclass
class JobDetails:
    """Structured job information extracted from a URL."""
    title: str
    company: str
    location: str
    description: str
    requirements: str
    url: str
    raw_text: str

class URLScraper:
    """Web scraper optimized for job posting URLs."""
    
    def __init__(self):
        self.session = None
        self.driver = None
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
        if self.driver:
            self.driver.quit()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver for JavaScript-heavy sites."""
        if self.driver:
            return self.driver
            
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            self.driver = webdriver.Chrome(
                ChromeDriverManager().install(),
                options=chrome_options
            )
            return self.driver
        except Exception as e:
            logger.warning(f"Failed to setup Selenium: {e}")
            return None
    
    async def scrape_url(self, url: str) -> JobDetails:
        """Extract job details from a given URL."""
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            
            # First try simple HTTP request
            content = await self._fetch_with_httpx(url)
            
            # If that fails or content is minimal, try Selenium
            if not content or len(content.strip()) < 500:
                content = await self._fetch_with_selenium(url)
            
            if not content:
                raise ValueError("Could not extract content from URL")
            
            # Parse and extract job details
            job_details = self._extract_job_details(content, url)
            return job_details
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            raise ValueError(f"Failed to scrape job posting: {str(e)}")
    
    async def _fetch_with_httpx(self, url: str) -> Optional[str]:
        """Fetch content using HTTP client."""
        try:
            response = await self.session.get(url, follow_redirects=True)
            response.raise_for_status()
            
            # Use readability to extract main content
            doc = Document(response.text)
            return doc.content()
            
        except Exception as e:
            logger.warning(f"HTTP fetch failed for {url}: {e}")
            return None
    
    async def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """Fetch content using Selenium for JavaScript-heavy sites."""
        try:
            driver = self._setup_selenium()
            if not driver:
                return None
            
            # Run Selenium in thread pool to avoid blocking
            def _selenium_fetch():
                driver.get(url)
                
                # Wait for content to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Additional wait for dynamic content
                driver.implicitly_wait(3)
                
                return driver.page_source
            
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, _selenium_fetch)
            
            # Use readability to extract main content
            doc = Document(content)
            return doc.content()
            
        except Exception as e:
            logger.warning(f"Selenium fetch failed for {url}: {e}")
            return None
    
    def _extract_job_details(self, html_content: str, url: str) -> JobDetails:
        """Extract structured job information from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        text = soup.get_text()
        clean_text = re.sub(r'\s+', ' ', text).strip()
        
        # Extract specific job information
        title = self._extract_job_title(soup, clean_text)
        company = self._extract_company_name(soup, clean_text)
        location = self._extract_location(soup, clean_text)
        description = self._extract_description(soup, clean_text)
        requirements = self._extract_requirements(soup, clean_text)
        
        return JobDetails(
            title=title,
            company=company,
            location=location,
            description=description,
            requirements=requirements,
            url=url,
            raw_text=clean_text
        )
    
    def _extract_job_title(self, soup: BeautifulSoup, text: str) -> str:
        """Extract job title from the page."""
        # Try various selectors for job title
        selectors = [
            'h1[data-automation="job-detail-title"]',  # Seek
            'h1.jobsearch-JobInfoHeader-title',         # Indeed  
            '[data-testid="job-title"]',                # LinkedIn
            '.job-title',
            '.job-header-title',
            'h1.title',
            'h1',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        # Fallback: extract from page title or first heading
        page_title = soup.find('title')
        if page_title:
            title_text = page_title.get_text(strip=True)
            # Remove common job board suffixes
            title_text = re.sub(r'\s*-\s*(Indeed|LinkedIn|Glassdoor|Monster).*$', '', title_text)
            if title_text and len(title_text) < 100:
                return title_text
        
        return "Job Position"
    
    def _extract_company_name(self, soup: BeautifulSoup, text: str) -> str:
        """Extract company name from the page."""
        selectors = [
            '[data-testid="job-details-company-name"]',  # LinkedIn
            '.jobsearch-InlineCompanyRating a',          # Indeed
            '.employer-name',
            '.company-name',
            '[data-automation="job-detail-company"]',    # Seek
            '.company',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        # Fallback: search for company patterns in text
        company_patterns = [
            r'Company:?\s*([A-Z][A-Za-z\s&,.-]+?)(?:\n|$)',
            r'at\s+([A-Z][A-Za-z\s&,.-]{2,30}?)(?:\s|$)',
            r'Job at\s+([A-Z][A-Za-z\s&,.-]{2,30}?)(?:\s|$)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return "Company"
    
    def _extract_location(self, soup: BeautifulSoup, text: str) -> str:
        """Extract job location from the page."""
        selectors = [
            '[data-testid="job-location"]',              # LinkedIn
            '.jobsearch-JobInfoHeader-subtitle',         # Indeed
            '[data-automation="job-detail-location"]',   # Seek
            '.location',
            '.job-location',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                location_text = element.get_text(strip=True)
                # Clean up location text
                location_text = re.sub(r'\s*•.*$', '', location_text)  # Remove bullet points and following text
                return location_text
        
        # Fallback: search for location patterns
        location_patterns = [
            r'Location:?\s*([A-Za-z\s,.-]+?)(?:\n|$)',
            r'((?:[A-Z][a-z]+,?\s*){1,3}(?:USA?|United States|Canada|UK|Australia|Remote))',
            r'Remote|Work from home',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.groups() else match.group(0).strip()
        
        return "Not specified"
    
    def _extract_description(self, soup: BeautifulSoup, text: str) -> str:
        """Extract job description from the page."""
        # Try to find description sections
        description_selectors = [
            '[data-testid="job-description"]',           # LinkedIn
            '#jobDescriptionText',                       # Indeed
            '.job-description',
            '.description',
            '.job-details',
            '.content',
        ]
        
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                desc_text = element.get_text(separator=' ', strip=True)
                if len(desc_text) > 100:  # Ensure we have substantial content
                    return self._clean_description_text(desc_text)
        
        # Fallback: try to extract main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|job|description'))
        if main_content:
            desc_text = main_content.get_text(separator=' ', strip=True)
            return self._clean_description_text(desc_text)
        
        # Last resort: use full text but try to find job-related content
        lines = text.split('\n')
        description_lines = []
        start_capturing = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Start capturing after we find job-related keywords
            if not start_capturing and re.search(r'(description|responsibilities|duties|about|role|position)', line.lower()):
                start_capturing = True
            
            if start_capturing:
                description_lines.append(line)
                
            # Stop if we hit navigation or footer content
            if re.search(r'(apply now|contact|privacy|terms|copyright)', line.lower()):
                break
        
        return self._clean_description_text(' '.join(description_lines[:20]))  # Limit to first 20 relevant lines
    
    def _extract_requirements(self, soup: BeautifulSoup, text: str) -> str:
        """Extract job requirements/qualifications from the page."""
        # Look for requirements sections
        requirements_keywords = r'(requirements?|qualifications?|skills?|experience|must have|preferred|ideal candidate)'
        
        # Try to find specific requirements sections
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b']):
            if re.search(requirements_keywords, heading.get_text(), re.IGNORECASE):
                # Get the following content
                requirements_text = ""
                next_element = heading.next_sibling
                while next_element and len(requirements_text) < 1000:
                    if hasattr(next_element, 'get_text'):
                        text_content = next_element.get_text(strip=True)
                        if text_content:
                            requirements_text += text_content + " "
                            # Stop if we hit another major heading
                            if next_element.name in ['h1', 'h2', 'h3'] and len(requirements_text) > 100:
                                break
                    next_element = next_element.next_sibling
                
                if requirements_text.strip():
                    return self._clean_description_text(requirements_text)
        
        # Fallback: extract requirements from full text
        text_lower = text.lower()
        requirements_start = -1
        
        for keyword in ['requirements', 'qualifications', 'must have', 'ideal candidate']:
            pos = text_lower.find(keyword)
            if pos != -1:
                requirements_start = pos
                break
        
        if requirements_start != -1:
            # Extract text starting from requirements section
            requirements_text = text[requirements_start:requirements_start + 1500]
            return self._clean_description_text(requirements_text)
        
        return "Requirements not clearly specified"
    
    def _clean_description_text(self, text: str) -> str:
        """Clean and format description text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common job board artifacts
        text = re.sub(r'(Apply now|Apply for this job|Save job|Share|Print).*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Job ID:?\s*\w+', '', text)
        text = re.sub(r'Posted:?\s*\d+.*?(ago|day|week)', '', text)
        
        # Limit length to reasonable size
        if len(text) > 2000:
            sentences = text.split('. ')
            text = '. '.join(sentences[:15]) + '.'
        
        return text.strip()

# Convenience function for direct usage
async def scrape_job_url(url: str) -> JobDetails:
    """Scrape job details from a URL."""
    async with URLScraper() as scraper:
        return await scraper.scrape_url(url) 