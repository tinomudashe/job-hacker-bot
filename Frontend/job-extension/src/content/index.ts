// Content script for job extraction
// This runs on every page and can be triggered by the extension

interface JobData {
  title?: string;
  company?: string;
  location?: string;
  description?: string;
  requirements?: string[];
  salary?: string;
  type?: string;
  url?: string;
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractJob') {
    const jobData = extractJobData();
    sendResponse(jobData);
  }
  return true;
});

function extractJobData(): JobData {
  const data: JobData = {};
  const hostname = window.location.hostname;

  // LinkedIn extraction
  if (hostname.includes('linkedin.com')) {
    data.title = document.querySelector('.job-details-jobs-unified-top-card__job-title, h1.topcard__title, .t-24.t-bold')?.textContent?.trim();
    data.company = document.querySelector('.job-details-jobs-unified-top-card__company-name, .topcard__org-name-link, .jobs-unified-top-card__company-name a')?.textContent?.trim();
    data.location = document.querySelector('.job-details-jobs-unified-top-card__bullet, .topcard__flavor--bullet, .jobs-unified-top-card__bullet')?.textContent?.trim();
    
    // Get full description
    const descElement = document.querySelector('.jobs-description__content, .description__text, .jobs-box--fadein');
    if (descElement) {
      data.description = descElement.textContent?.trim();
    }
    
    // Extract salary if available
    const salaryElement = document.querySelector('.job-details-jobs-unified-top-card__job-insight span, .salary-main-rail-card__salary-range');
    if (salaryElement) {
      data.salary = salaryElement.textContent?.trim();
    }
    
    data.type = document.querySelector('.job-details-jobs-unified-top-card__workplace-type, .jobs-unified-top-card__workplace-type')?.textContent?.trim();
  }
  
  // Indeed extraction
  else if (hostname.includes('indeed.com')) {
    data.title = document.querySelector('[data-testid="job-title"], h1.jobsearch-JobInfoHeader-title, .jobsearch-JobInfoHeader-title-container h1')?.textContent?.trim();
    data.company = document.querySelector('[data-testid="company-name"], .jobsearch-CompanyInfoContainer a, [data-testid="inlineHeader-companyName"]')?.textContent?.trim();
    data.location = document.querySelector('[data-testid="job-location"], [data-testid="inlineHeader-companyLocation"], .jobsearch-JobInfoHeader-subtitle > div:nth-child(2)')?.textContent?.trim();
    data.description = document.querySelector('#jobDescriptionText, .jobsearch-JobComponent-description, .jobsearch-jobDescriptionText')?.textContent?.trim();
    
    // Extract salary
    const salaryElement = document.querySelector('[data-testid="job-salary"], .salary-snippet-container, .attribute_snippet');
    if (salaryElement) {
      data.salary = salaryElement.textContent?.trim();
    }
  }
  
  // Glassdoor extraction
  else if (hostname.includes('glassdoor.com')) {
    data.title = document.querySelector('[data-test="job-title"], .JobDetails_jobTitle__Rw_gn, .css-17x2pwl.e11nt52q6')?.textContent?.trim();
    data.company = document.querySelector('[data-test="employer-name"], .JobDetails_companyName__FqHnR, .css-16nw49e.e11nt52q1')?.textContent?.trim();
    data.location = document.querySelector('[data-test="location"], .JobDetails_location__MbnUM, .css-1v5elnn.e11nt52q2')?.textContent?.trim();
    data.description = document.querySelector('.JobDetails_jobDescription__6VeBn, [data-test="job-description"], .desc.css-58vpdc.ecgq1xb5')?.textContent?.trim();
    
    // Extract salary
    const salaryElement = document.querySelector('.JobDetails_salaryEstimate__zmR5J, [data-test="detailSalary"]');
    if (salaryElement) {
      data.salary = salaryElement.textContent?.trim();
    }
  }
  
  // Greenhouse.io extraction
  else if (hostname.includes('greenhouse.io') || hostname.includes('boards.greenhouse.io')) {
    data.title = document.querySelector('#header .app-title, h1.app-title, .job-title')?.textContent?.trim();
    data.company = document.querySelector('.company-name, .organization')?.textContent?.trim();
    data.location = document.querySelector('.location, .location-name')?.textContent?.trim();
    data.description = document.querySelector('#content, .content, #job-description')?.textContent?.trim();
  }
  
  // Lever.co extraction
  else if (hostname.includes('lever.co')) {
    data.title = document.querySelector('.posting-headline h2, h2[data-qa="posting-name"]')?.textContent?.trim();
    data.company = document.querySelector('.posting-headline .posting-company, [data-qa="posting-company"]')?.textContent?.trim();
    data.location = document.querySelector('.location, .posting-categories .location')?.textContent?.trim();
    data.description = document.querySelector('.section-wrapper .content, [data-qa="job-description"]')?.textContent?.trim();
  }
  
  // Workday extraction
  else if (hostname.includes('workday.com')) {
    data.title = document.querySelector('[data-automation-id="jobPostingHeader"], h2[data-automation-id="jobPostingTitle"]')?.textContent?.trim();
    data.company = document.querySelector('[data-automation-id="company"]')?.textContent?.trim();
    data.location = document.querySelector('[data-automation-id="location"], [data-automation-id="jobPostingLocation"]')?.textContent?.trim();
    data.description = document.querySelector('[data-automation-id="jobPostingDescription"], .job-description')?.textContent?.trim();
  }
  
  // AngelList extraction
  else if (hostname.includes('angel.co') || hostname.includes('wellfound.com')) {
    data.title = document.querySelector('h1.styles_title__xpQDw, h2.styles_header__14n2o')?.textContent?.trim();
    data.company = document.querySelector('.styles_component__1c6JC a, .styles_name__3JVON')?.textContent?.trim();
    data.location = document.querySelector('.styles_location__3JVON, .styles_component__2wJNZ')?.textContent?.trim();
    data.description = document.querySelector('.styles_description__1aRID, .styles_component__3kfj9')?.textContent?.trim();
  }
  
  // Generic fallback extraction
  else {
    // Look for job title
    const titleSelectors = [
      'h1', 
      'h2.job-title', 
      '[class*="job-title"]', 
      '[class*="position-title"]', 
      '[id*="job-title"]',
      '[data-testid*="title"]',
      'header h1'
    ];
    
    for (const selector of titleSelectors) {
      if (!data.title) {
        const element = document.querySelector(selector);
        if (element?.textContent) {
          data.title = element.textContent.trim();
          break;
        }
      }
    }

    // Look for company name
    const companySelectors = [
      '[class*="company-name"]',
      '[class*="employer"]',
      '[class*="organization"]',
      '[data-testid*="company"]',
      'a[href*="/company/"]'
    ];
    
    for (const selector of companySelectors) {
      if (!data.company) {
        const element = document.querySelector(selector);
        if (element?.textContent) {
          data.company = element.textContent.trim();
          break;
        }
      }
    }

    // Look for location
    const locationSelectors = [
      '[class*="location"]',
      '[class*="place"]',
      '[class*="city"]',
      '[data-testid*="location"]',
      '[aria-label*="location"]'
    ];
    
    for (const selector of locationSelectors) {
      if (!data.location) {
        const element = document.querySelector(selector);
        if (element?.textContent) {
          data.location = element.textContent.trim();
          break;
        }
      }
    }

    // Look for description
    const descriptionSelectors = [
      '[class*="description"]',
      '[class*="details"]',
      '[class*="summary"]',
      '[data-testid*="description"]',
      'main article',
      '.job-post',
      '#job-details'
    ];
    
    for (const selector of descriptionSelectors) {
      if (!data.description) {
        const element = document.querySelector(selector);
        if (element?.textContent) {
          data.description = element.textContent.trim();
          break;
        }
      }
    }
  }

  // Clean up the data
  if (data.description && data.description.length > 10000) {
    data.description = data.description.substring(0, 10000) + '...';
  }

  // Add current URL
  data.url = window.location.href;

  return data;
}

// Add visual indicator when extension is active
const indicator = document.createElement('div');
indicator.id = 'job-hacker-indicator';
indicator.style.cssText = `
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #3B82F6;
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-family: 'Inter', system-ui, sans-serif;
  z-index: 999999;
  display: none;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;
indicator.innerHTML = `
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
  </svg>
  Job Hacker Active
`;
document.body.appendChild(indicator);

// Show indicator on job sites
const jobSites = ['linkedin.com', 'indeed.com', 'glassdoor.com', 'greenhouse.io', 'lever.co', 'workday.com'];
if (jobSites.some(site => window.location.hostname.includes(site))) {
  indicator.style.display = 'flex';
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    indicator.style.display = 'none';
  }, 3000);
}

export {};