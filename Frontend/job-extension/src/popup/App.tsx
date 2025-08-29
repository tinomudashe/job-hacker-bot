import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  Loader2, 
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  RefreshCw,
  Settings as SettingsIcon,
  Key,
  PanelRightOpen
} from 'lucide-react';
import Settings from './Settings';

interface JobData {
  title?: string;
  company?: string;
  location?: string;
  description?: string;
  requirements?: string[];
  salary?: string;
  type?: string;
  url?: string;
  skills?: string[];
}

interface ExtensionState {
  isExtracting: boolean;
  jobData: JobData | null;
  error: string | null;
  isConnected: boolean;
  extractedText: string | null;
  extractionProgress: string | null;
  isGenerating: boolean;
}

const App: React.FC = () => {
  const [state, setState] = useState<ExtensionState>({
    isExtracting: false,
    jobData: null,
    error: null,
    isConnected: false,
    extractedText: null,
    extractionProgress: null,
    isGenerating: false
  });

  const [appUrl, setAppUrl] = useState<string>('https://jobhackerbot.com');
  const [showSettings, setShowSettings] = useState(false);
  const [generatingType, setGeneratingType] = useState<'cover_letter' | 'resume' | null>(null);
  const [generationProgress, setGenerationProgress] = useState<string>('');
  const [hasToken, setHasToken] = useState(false);
  const [showFullDescription, setShowFullDescription] = useState(false);
  const [userProfile, setUserProfile] = useState<{
    firstName?: string;
    lastName?: string;
    email?: string;
    profileImage?: string;
  } | null>(null);

  useEffect(() => {
    // Load saved data first, then check connection
    chrome.storage.local.get(['jobData', 'extensionToken', 'sessionToken', 'appUrl', 'userProfile'], async (result) => {
      if (result.jobData) {
        setState(prev => ({ ...prev, jobData: result.jobData }));
      }
      if (result.extensionToken || result.sessionToken) {
        setHasToken(true);
      } else {
        // Check if user is signed in to the app
        await checkUserAuth();
        // Check again after auth check
        const newData = await chrome.storage.local.get(['sessionToken']);
        if (newData.sessionToken) {
          setHasToken(true);
        }
      }
      if (result.appUrl) {
        setAppUrl(result.appUrl);
      }
      if (result.userProfile) {
        setUserProfile(result.userProfile);
      }
      
      // Check connection after loading appUrl
      const urlToCheck = result.appUrl || 'https://jobhackerbot.com';
      try {
        const response = await fetch(`${urlToCheck}/api/health`);
        setState(prev => ({ ...prev, isConnected: response.ok }));
      } catch {
        setState(prev => ({ ...prev, isConnected: false }));
      }
    });
  }, []);

  const checkConnection = async () => {
    try {
      const response = await fetch(`${appUrl}/api/health`);
      setState(prev => ({ ...prev, isConnected: response.ok }));
    } catch {
      setState(prev => ({ ...prev, isConnected: false }));
    }
  };

  const openSidePanel = async () => {
    try {
      // Check if sidePanel API is available (Chrome 116+)
      if ((chrome as any).sidePanel && (chrome as any).sidePanel.open) {
        // Get current tab info for proper API call
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (tab && tab.id !== undefined) {
          // Correct API signature: open(options) where options can have windowId or tabId
          (chrome as any).sidePanel.open({ 
            tabId: tab.id 
          }).then(() => {
            console.log('Side panel opened successfully');
            // Close the popup after opening side panel
            window.close();
          }).catch((error: any) => {
            console.error('Failed to open side panel:', error);
            // If it fails, try without options (global panel)
            (chrome as any).sidePanel.open({}).then(() => {
              window.close();
            }).catch((err: any) => {
              console.error('Failed to open global side panel:', err);
              // Final fallback: inform user
              alert('To use the side panel:\n1. Right-click the extension icon\n2. Select "Open side panel"');
            });
          });
        } else {
          // Try opening without tab context
          (chrome as any).sidePanel.open({}).then(() => {
            window.close();
          }).catch((error: any) => {
            console.error('Failed to open side panel:', error);
          });
        }
      } else {
        // Browser doesn't support sidePanel API
        alert('Your browser doesn\'t support the side panel feature. Please update Chrome to version 116 or later.');
      }
    } catch (error) {
      console.error('Error opening side panel:', error);
    }
  };

  const checkUserAuth = async () => {
    try {
      // Try to get a session token from the app
      const tokenUrl = `${appUrl}/api/extension/get-token`;
      
      // Open the URL in a hidden iframe to maintain session
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = tokenUrl;
      document.body.appendChild(iframe);
      
      // Wait a moment for iframe to load
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Try to fetch with credentials
      const response = await fetch(tokenUrl, {
        method: 'GET',
        credentials: 'include',
        mode: 'cors'
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.token) {
          // Store the session token temporarily
          chrome.storage.local.set({ 
            sessionToken: data.token,
            userProfile: data.user 
          });
          setUserProfile(data.user);
          console.log('Got session token from logged-in user');
        }
      }
      
      // Clean up iframe
      document.body.removeChild(iframe);
    } catch (error) {
      console.log('Could not get session token:', error);
    }
  };

  const extractJobData = async () => {
    setState(prev => ({ ...prev, isExtracting: true, error: null, extractionProgress: null }));
    setShowFullDescription(false); // Reset when extracting new job

    try {
      // Get current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab.id) {
        throw new Error('No active tab found');
      }

      // Extract all text content from the page
      setState(prev => ({ ...prev, error: 'Extracting page content...' }));
      
      // Inject content script to get page text
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: extractPageText,
      });

      const pageText = result.result as string;
      
      if (!pageText || pageText.length < 100) {
        throw new Error('Could not extract sufficient text content from the page. Make sure you are on a job details page.');
      }
      
      console.log('Page text extracted successfully, length:', pageText.length);
      
      // Store the extracted text for fallback display
      setState(prev => ({ ...prev, extractedText: pageText }));
      
      // Send text to backend via WebSocket for AI extraction
      setState(prev => ({ ...prev, error: 'Connecting to AI service...' }));
      
      // Get saved tokens and app URL (same pattern as openInApp)
      const storageData = await chrome.storage.local.get(['extensionToken', 'sessionToken', 'appUrl']);
      console.log('Storage data retrieved:', { 
        hasExtensionToken: !!storageData.extensionToken,
        hasSessionToken: !!storageData.sessionToken
      });
      
      const { extensionToken, sessionToken, appUrl: savedAppUrl } = storageData;
      const currentAppUrl = savedAppUrl || appUrl;
      
      // Check for authentication - try multiple methods
      let authHeader = '';
      
      // 1. First try extension token (most reliable)
      if (extensionToken) {
        console.log('Using extension token');
        authHeader = `Bearer ${extensionToken}`;
      } 
      // 2. Then try stored session token
      else if (sessionToken) {
        console.log('Using session token from logged-in user');
        authHeader = `Bearer ${sessionToken}`;
      }
      // 3. Try to get a fresh session token
      else {
        console.log('No tokens found, checking if user is logged in...');
        
        // Try to get a session token
        await checkUserAuth();
        
        // Check again after attempting to get session
        const newData = await chrome.storage.local.get(['sessionToken']);
        if (newData.sessionToken) {
          console.log('Got new session token');
          authHeader = `Bearer ${newData.sessionToken}`;
        }
      }

      // If still no auth, prompt user
      if (!authHeader) {
        setState(prev => ({ ...prev, isExtracting: false }));
        
        // Show authentication options
        const message = 'Authentication required.\n\n' +
                       'Please choose an option:\n\n' +
                       '1. Sign in to Job Hacker Bot (OK)\n' +
                       '2. Generate an access token (Cancel)';
        
        if (confirm(message)) {
          // Open sign-in page in browser
          window.open(`${currentAppUrl}/sign-in?from=extension`, '_blank');
          setState(prev => ({ 
            ...prev, 
            error: 'Please sign in to Job Hacker Bot in the browser tab that opened, then try again.' 
          }));
          // After sign in, try to get session token
          setTimeout(async () => {
            await checkUserAuth();
            const data = await chrome.storage.local.get(['sessionToken']);
            if (data.sessionToken) {
              setHasToken(true);
              setState(prev => ({ ...prev, error: null }));
            }
          }, 5000);
        } else {
          // Show settings for token generation  
          setShowSettings(true);
          setState(prev => ({ 
            ...prev, 
            error: 'Generate an access token in the settings panel for persistent authentication.' 
          }));
        }
        return;
      }

      // Create WebSocket connection for extraction
      const backendUrl = 'https://jobhacker-202691328264.europe-west1.run.app';
      const wsUrl = backendUrl.replace(/^http/, 'ws');
      const ws = new WebSocket(`${wsUrl}/api/ws/orchestrator?token=${authHeader.replace('Bearer ', '')}`);
      
      let extractionCompleted = false;
      
      ws.onopen = () => {
        console.log('WebSocket connected for job text extraction');
        setState(prev => ({ ...prev, error: 'Analyzing page content with AI...' }));
        
        // Send the page text extraction request through WebSocket
        
        ws.send(JSON.stringify({
          type: 'message',
          content: `I'm providing you with text content from a job posting. Please read and analyze this text directly - do not use any tools, do not search documents, do not browse websites. Just read the text below and extract job information from it.

TEXT TO ANALYZE:
================
${pageText.substring(0, 8000)} ${pageText.length > 8000 ? '... (content truncated for brevity)' : ''}
================

Please read the text above and extract the following information directly from it:
- **Job Title:** [what position is being advertised]
- **Company:** [what company/employer is hiring]  
- **Location:** [where is the job located]
- **Job Description:** [what does the job involve - responsibilities, duties, what you'll do]
- **Salary:** [how much does it pay - salary, rate, compensation]
- **Employment Type:** [what type of work - full-time, contract, remote, etc.]
- **Key Requirements:** [what skills/experience do they want]
- **Skills:** [list up to 10 most important technical skills, programming languages, tools, technologies mentioned - separate with commas]

Read the text I provided above and extract the job details directly. Do not use any tools or search functions.`,
          page_id: 'extension_temp_request'
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          console.log('Message content:', data.message);
          
          // Handle progress updates (use progress field instead of error)
          if (data.message && !extractionCompleted) {
            // Check if this looks like actual job data rather than progress
            if (data.message.includes('Job Title') || data.message.includes('Company') || data.message.includes('**')) {
              // This looks like extracted job data, process it immediately
              console.log('Detected job data in response, processing...');
            } else {
              // This is a progress message, show it in progress field
              setState(prev => ({ ...prev, extractionProgress: data.message, error: null }));
            }
          }
          
          // Check if the AI is trying to use the tool but failing
          if (data.message && (data.message.includes('extract_job_from_screenshot') || data.message.includes('screenshot'))) {
            console.log('Tool-related message detected:', data.message);
          }
          
          // Look for job information in the AI response
          if (data.message && (
            data.message.includes('Job Title') || 
            data.message.includes('Company') || 
            data.message.includes('Position') ||
            data.message.toLowerCase().includes('title:') ||
            data.message.toLowerCase().includes('company:')
          )) {
            extractionCompleted = true;
            
            // Try to parse job data from the message
            try {
              // Extract the structured data from the AI response
              const message = data.message;
              
              // Create a job data object from the AI response with flexible field extraction
              const jobData: JobData = {
                title: extractField(message, 'Job Title') || extractField(message, 'Title') || extractField(message, 'Position') || extractField(message, 'Role'),
                company: extractField(message, 'Company') || extractField(message, 'Employer') || extractField(message, 'Organization') || extractField(message, 'Client'),
                location: extractField(message, 'Location') || extractField(message, 'Where') || extractField(message, 'Based') || extractField(message, 'Remote'),
                description: extractField(message, 'Job Description') || extractField(message, 'Description') || extractField(message, 'Role Description') || extractField(message, 'About') || extractField(message, 'Responsibilities') || extractField(message, 'Summary') || extractLongField(message, 'Description'),
                salary: extractField(message, 'Salary') || extractField(message, 'Pay') || extractField(message, 'Compensation') || extractField(message, 'Rate') || extractField(message, 'Wage'),
                type: extractField(message, 'Employment Type') || extractField(message, 'Type') || extractField(message, 'Employment') || extractField(message, 'Schedule') || extractField(message, 'Contract'),
                skills: extractSkills(message),
                url: tab.url
              };
              
              // Validate we have at least a title
              if (!jobData.title) {
                throw new Error('No job title found in extraction result');
              }
              
              // Save to storage
              chrome.storage.local.set({ jobData });
              
              setState(prev => ({ 
                ...prev, 
                jobData,
                isExtracting: false,
                error: null,
                extractionProgress: null
              }));
              
              // Ensure WebSocket is fully closed before proceeding
              if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close();
              }
              
              // Wait a moment to ensure connection is fully closed
              setTimeout(() => {
                console.log('Job extraction WebSocket closed, ready for document generation');
              }, 100);
              
            } catch (parseError) {
              console.error('Error parsing job data from WebSocket response:', parseError);
              setState(prev => ({ 
                ...prev, 
                error: 'Extraction completed but failed to parse job data',
                isExtracting: false,
                extractionProgress: null
              }));
            }
          }
          
          // Handle errors
          if (data.type === 'error') {
            setState(prev => ({ 
              ...prev, 
              error: data.message || 'An error occurred during extraction', 
              isExtracting: false,
              extractionProgress: null
            }));
            ws.close();
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          setState(prev => ({ 
            ...prev, 
            error: 'Failed to process extraction response', 
            isExtracting: false,
            extractionProgress: null
          }));
        }
      };
      
      // Helper function to extract fields from the AI response
      const extractField = (message: string, fieldName: string): string => {
        // Try different patterns for field extraction
        const patterns = [
          new RegExp(`\\*\\*${fieldName}[:\\s]*\\*\\*\\s*([^\\n]+)`, 'i'), // **Field:** value
          new RegExp(`${fieldName}[:\\s]*([^\\n]+)`, 'i'), // Field: value
          new RegExp(`\\*${fieldName}[:\\s]*\\*\\s*([^\\n]+)`, 'i'), // *Field:* value
          new RegExp(`${fieldName}[:\\s]*([^\\n\\*]+)`, 'i') // Field: value (without formatting)
        ];
        
        for (const regex of patterns) {
          const match = message.match(regex);
          if (match && match[1]) {
            return match[1].trim().replace(/^\*+|\*+$/g, ''); // Remove surrounding asterisks
          }
        }
        return '';
      };

      // Helper function to extract longer text fields like descriptions
      const extractLongField = (message: string, fieldName: string): string => {
        const patterns = [
          new RegExp(`\\*\\*${fieldName}[:\\s]*\\*\\*\\s*([\\s\\S]*?)(?=\\*\\*|$)`, 'i'), // **Field:** content until next **
          new RegExp(`${fieldName}[:\\s]*([\\s\\S]*?)(?=\\n\\n|\\n[A-Z]|$)`, 'i') // Field: content until double newline or capitalized line
        ];
        
        for (const regex of patterns) {
          const match = message.match(regex);
          if (match && match[1]) {
            return match[1].trim().replace(/^\*+|\*+$/g, '').substring(0, 500); // Limit to 500 chars
          }
        }
        return '';
      };

      // Helper function to extract skills from the AI response
      const extractSkills = (message: string): string[] => {
        const skillsText = extractField(message, 'Skills') || extractField(message, 'Technologies') || extractField(message, 'Technical Skills');
        
        if (!skillsText) return [];
        
        // Split by common separators and clean up
        return skillsText
          .split(/[,;•\n]/) // Split by comma, semicolon, bullet, or newline
          .map(skill => skill.trim())
          .filter(skill => skill.length > 0 && skill.length < 50) // Filter out empty or very long items
          .slice(0, 15); // Limit to 15 skills max
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ 
          ...prev, 
          error: 'Connection error occurred during extraction',
          isExtracting: false,
          extractionProgress: null
        }));
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        if (!extractionCompleted) {
          setState(prev => ({ 
            ...prev, 
            error: 'Connection closed before extraction completed',
            isExtracting: false,
            extractionProgress: null
          }));
        }
      };
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to extract job data',
        isExtracting: false,
        extractionProgress: null
      }));
    }
  };

  const openInApp = async (type: 'resume' | 'cover_letter') => {
    if (!state.jobData) return;

    setState(prev => ({ ...prev, isGenerating: true, error: null }));
    setGeneratingType(type);
    setGenerationProgress(`Initializing ${type === 'cover_letter' ? 'cover letter' : 'resume tailoring'}...`);
    
    let ws: WebSocket | null = null;

    try {
      // Get saved tokens and app URL
      const storageData = await chrome.storage.local.get(['extensionToken', 'sessionToken', 'appUrl']);
      const { extensionToken, sessionToken, appUrl: savedAppUrl } = storageData;
      const currentAppUrl = savedAppUrl || appUrl;
      
      // Check for authentication
      let authHeader = '';
      
      if (extensionToken) {
        authHeader = `Bearer ${extensionToken}`;
      } else if (sessionToken) {
        authHeader = `Bearer ${sessionToken}`;
      } else {
        await checkUserAuth();
        const newData = await chrome.storage.local.get(['sessionToken']);
        if (newData.sessionToken) {
          authHeader = `Bearer ${newData.sessionToken}`;
        }
      }

      if (!authHeader) {
        setState(prev => ({ ...prev, isGenerating: false }));
        setGeneratingType(null);
        throw new Error('Authentication required. Please sign in or set up an access token.');
      }

      // Create WebSocket connection for document generation
      const backendUrl = 'https://jobhacker-202691328264.europe-west1.run.app';
      const wsUrl = backendUrl.replace(/^http/, 'ws');
      ws = new WebSocket(`${wsUrl}/api/ws/orchestrator?token=${authHeader.replace('Bearer ', '')}`);
      
      ws.onopen = () => {
        setGenerationProgress('Initializing AI processing...');
        
        // Send document generation request
        const documentTypeText = type === 'cover_letter' ? 'cover letter' : 'resume';
        const jobDataText = `Job Title: ${state.jobData?.title}\nCompany: ${state.jobData?.company}\nLocation: ${state.jobData?.location}\nDescription: ${state.jobData?.description}`;
        
        ws!.send(JSON.stringify({
          type: 'message',
          content: `Please generate a ${documentTypeText} for the following job posting:\n\n${jobDataText}`,
          jobData: state.jobData,
          documentType: type,
          page_id: 'extension_temp_request'
        }));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Handle progress updates
        if (data.type === 'progress_update' && data.message) {
          setGenerationProgress(data.message);
        }
        
        // Handle downloadable document completion (cover letter or resume)
        if (data.type === 'message' && data.message && (data.message.includes('[DOWNLOADABLE_COVER_LETTER]') || data.message.includes('[DOWNLOADABLE_RESUME]'))) {
          const jsonMatch = data.message.match(/\[DOWNLOADABLE_(?:COVER_LETTER|RESUME)\]\s*({.*})/);
          
          let result: any = {};
          if (jsonMatch) {
            // Cover letter with JSON data
            result = JSON.parse(jsonMatch[1]);
          } else {
            // Resume with plain text response - create minimal result object
            result = {
              body: data.message.replace(/\[DOWNLOADABLE_(?:COVER_LETTER|RESUME)\]/g, '').trim(),
              company_name: state.jobData?.company || '',
              job_title: state.jobData?.title || ''
            };
          }
          
          ws!.close();

          // Encode content for PDF dialog
          const contentData = {
            content: result.body || result.content,
            coverLetterId: data.page_id,
            fullData: result
          };
          
          const encodedContent = btoa(encodeURIComponent(JSON.stringify(contentData)));

          // Open PDF dialog
          const params = new URLSearchParams({
            action: 'open_pdf_dialog',
            type: type,
            company: result.company_name || state.jobData?.company || '',
            title: result.job_title || state.jobData?.title || '',
            generated: 'true',
            data: encodedContent
          });

          const targetUrl = `${currentAppUrl}?${params.toString()}`;
          chrome.tabs.create({ url: targetUrl });
          
          // Clear generation state
          setGeneratingType(null);
          setGenerationProgress('');
          setState(prev => ({ ...prev, isGenerating: false }));
        }
      };
      
      ws.onerror = () => {
        setState(prev => ({ ...prev, error: 'Connection error', isGenerating: false }));
        setGeneratingType(null);
      };
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to generate document',
        isGenerating: false 
      }));
      setGeneratingType(null);
    }
  };

  // Show settings if requested
  if (showSettings) {
    return (
      <Settings 
        onClose={() => setShowSettings(false)}
        onTokenSaved={async () => {
          // Wait for storage to be updated
          await new Promise(resolve => setTimeout(resolve, 100));
          // Reload token status
          const result = await chrome.storage.local.get(['extensionToken']);
          setHasToken(!!result.extensionToken);
          setShowSettings(false);
        }}
      />
    );
  }

  return (
    <div className="min-h-screen h-screen flex flex-col relative overflow-hidden bg-white">
      
      {/* Debug: Show generating state */}
      {generatingType && (
        <div className="fixed top-0 left-0 bg-red-500 text-white p-2 z-50">
          DEBUG: Generating {generatingType}
        </div>
      )}
      
      {/* Loading Overlay with Backend Progress */}
      {generatingType && (
        <div className="absolute inset-0 bg-black/40 backdrop-blur-xl z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-8 max-w-sm w-full shadow-2xl shadow-gray-900/30 border border-gray-200">
            <div className="flex flex-col items-center space-y-6">
              {/* Simple clean spinner */}
              <div className="relative w-20 h-20">
                <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-600 border-r-blue-600 animate-spin"></div>
              </div>
              
              {/* Progress text */}
              <div className="text-center space-y-3">
                <h3 className="text-lg font-bold text-gray-900">
                  {generatingType === 'cover_letter' ? 'Creating Your Cover Letter' : 'Tailoring Your Resume'}
                </h3>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 font-medium min-h-[40px] flex items-center justify-center">
                    {generationProgress || 'Initializing...'}
                  </p>
                </div>
                <div className="pt-3 space-y-2">
                  <div className="flex items-center justify-center gap-1">
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-pulse"></div>
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-pulse" style={{animationDelay: '200ms'}}></div>
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-pulse" style={{animationDelay: '400ms'}}></div>
                  </div>
                  <div className="flex items-center justify-center gap-2 text-xs text-blue-600">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Optimizing for ATS & recruiters</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Header - Floating Design */}
      <div className="sticky top-0 z-20 header-glass px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-white flex items-center justify-center shadow-lg shadow-gray-900/25">
              <img 
                src="jobhackerbot-logo (1).png" 
                alt="Job Hacker Bot" 
                className="w-5 h-5 object-contain"
              />
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900">Job Hacker Bot</h1>
              <p className="text-[9px] text-gray-500">Chrome Extension</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* User Profile Image */}
            {userProfile && userProfile.profileImage && (
              <div className="flex items-center gap-1.5">
                <img 
                  src={userProfile.profileImage}
                  alt={`${userProfile.firstName || 'User'} ${userProfile.lastName || ''}`}
                  className="w-7 h-7 rounded-full border-2 border-white shadow-md shadow-gray-900/20 object-cover"
                  onError={(e) => {
                    // Fallback to initials if image fails to load
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const initialsDiv = document.createElement('div');
                    initialsDiv.className = 'w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-[10px] shadow-md shadow-gray-900/20';
                    initialsDiv.textContent = `${userProfile.firstName?.[0] || ''}${userProfile.lastName?.[0] || ''}`.toUpperCase();
                    target.parentElement?.appendChild(initialsDiv);
                  }}
                />
              </div>
            )}
            
            {/* Token indicator - only show if using token auth */}
            {hasToken && !userProfile && (
              <div className="flex items-center justify-center w-7 h-7 rounded-full bg-green-50 border border-green-500/50" title="Authenticated with token">
                <Key className="w-3.5 h-3.5 text-green-600" />
              </div>
            )}
            
            {/* Connection status - Blinking dot */}
            <div className="relative">
              <div className={`w-2.5 h-2.5 rounded-full ${
                state.isConnected 
                  ? 'bg-emerald-500' 
                  : 'bg-red-500'
              }`}>
                {state.isConnected && (
                  <div className="absolute inset-0 rounded-full bg-emerald-500 animate-ping"></div>
                )}
              </div>
              <span className="sr-only">{state.isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
            
            <div className="flex items-center gap-1.5">
              <button
                onClick={openSidePanel}
                className="p-2 rounded-lg bg-white/60 backdrop-blur-xl border border-white/50 hover:bg-white/80 hover:scale-105 transition-all duration-300 shadow-md shadow-gray-900/15 hover:shadow-lg hover:shadow-gray-900/20"
                type="button"
                aria-label="Open in side panel"
                title="Keep open in side panel"
              >
                <PanelRightOpen className="w-3.5 h-3.5 text-gray-700" />
              </button>
              
              <button
                onClick={() => setShowSettings(true)}
                className="p-2 rounded-lg bg-white/60 backdrop-blur-xl border border-white/50 hover:bg-white/80 hover:scale-105 transition-all duration-300 shadow-md shadow-gray-900/15 hover:shadow-lg hover:shadow-gray-900/20"
                type="button"
                aria-label="Settings"
              >
                <SettingsIcon className="w-3.5 h-3.5 text-gray-700" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Scrollable */}
      <div className="flex-1 overflow-y-auto px-6 pb-6 pt-2 space-y-4 relative z-10">
        {/* Extract Button */}
        {!state.jobData && (
          <button
            onClick={extractJobData}
            disabled={state.isExtracting}
            className="btn-primary w-full h-12"
            type="button"
          >
            {state.isExtracting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Extracting Job Details...</span>
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                <span>Extract Job Details</span>
              </>
            )}
          </button>
        )}

        {/* Extraction Progress Display */}
        {state.extractionProgress && state.isExtracting && (
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-start gap-3">
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-900">Extracting Job Data</p>
                <p className="text-xs text-blue-700 mt-1">{state.extractionProgress}</p>
              </div>
            </div>
          </div>
        )}

        {/* Error Display - Only for actual errors */}
        {state.error && !state.isExtracting && (
          <div className="card bg-red-50 border-red-200">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-900">Extraction Failed</p>
                <p className="text-xs text-red-700 mt-1">{state.error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Job Data Display */}
        {state.jobData && (
          <>
            <div className="card">
              <div className="space-y-3">
                <div>
                  <h2 className="text-base font-semibold text-gray-900">
                    {state.jobData.title}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {state.jobData.company} • {state.jobData.location}
                  </p>
                </div>

                {state.jobData.type && (
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                      {state.jobData.type}
                    </span>
                    {state.jobData.salary && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
                        {state.jobData.salary}
                      </span>
                    )}
                  </div>
                )}

                {state.jobData.description && (
                  <div>
                    <p className="text-xs font-medium text-gray-700 mb-1">Description</p>
                    <div className="relative">
                      <p className={`text-xs text-gray-600 ${!showFullDescription ? 'line-clamp-3' : ''}`}>
                        {state.jobData.description}
                      </p>
                      {state.jobData.description.length > 200 && (
                        <button
                          onClick={() => setShowFullDescription(!showFullDescription)}
                          className="text-xs text-blue-600 hover:text-blue-700 font-semibold mt-2 focus:outline-none hover:underline transition-all duration-200"
                          type="button"
                        >
                          {showFullDescription ? '← Show less' : 'Show more →'}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {state.jobData.skills && state.jobData.skills.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-700 mb-2">Required Skills</p>
                    <div className="flex flex-wrap gap-1.5">
                      {state.jobData.skills.map((skill, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-purple-50 text-purple-700 text-xs font-medium rounded-md border border-purple-100"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {state.jobData.url && (
                  <a 
                    href={state.jobData.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>View Original Posting</span>
                  </a>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={() => openInApp('cover_letter')}
                className="btn-primary w-full h-11"
                disabled={state.isExtracting || state.isGenerating || generatingType !== null}
                type="button"
              >
                <FileText className="w-5 h-5" />
                <span>Create Cover Letter</span>
              </button>

              <button
                onClick={() => openInApp('resume')}
                className="btn-secondary w-full h-11"
                disabled={state.isExtracting || state.isGenerating || generatingType !== null}
                type="button"
              >
                <FileText className="w-5 h-5" />
                <span>Tailor Resume</span>
              </button>

              <button
                onClick={() => {
                  setState(prev => ({ ...prev, jobData: null, error: null }));
                  setShowFullDescription(false);
                  chrome.storage.local.remove('jobData');
                }}
                className="btn-secondary w-full h-11"
                type="button"
              >
                <RefreshCw className="w-5 h-5" />
                <span>Extract New Job</span>
              </button>
            </div>
          </>
        )}

        {/* Instructions */}
        {!state.jobData && !state.error && (
          <div className="card bg-blue-50 border-blue-200">
            <div className="space-y-2">
              <p className="text-sm font-medium text-blue-900">How to use:</p>
              <ol className="text-xs text-blue-700 space-y-1 list-decimal list-inside">
                <li>Navigate to any job posting page</li>
                <li>Click "Extract Job Details" button</li>
                <li>Choose to create a cover letter or tailor your resume</li>
                <li>The app will open with pre-filled information</li>
              </ol>
              {!hasToken && (
                <div className="pt-2 border-t border-blue-200">
                  <p className="text-xs text-blue-800 font-medium">
                    💡 Tip: Add an access token in settings to skip signing in
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer - Floating Design */}
      <div className="sticky bottom-0 z-20 mt-auto p-3">
        <div className="bg-white/85 backdrop-blur-2xl backdrop-saturate-150 rounded-xl shadow-lg shadow-gray-900/10 border border-gray-200/20 px-4 py-2.5">
          <p className="text-xs text-center text-gray-500 font-medium">
            Ensure Job Hacker Bot is running at{' '}
            <span className="text-blue-600">localhost:3000</span>
          </p>
        </div>
      </div>
    </div>
  );
};

// Function that will be injected into the page to extract all text
export function extractPageText(): string {
  // Remove script and style elements
  const scripts = document.querySelectorAll('script, style, noscript');
  scripts.forEach(el => el.remove());
  
  // Get all text content
  const bodyText = document.body.innerText || document.body.textContent || '';
  
  // Clean up the text - remove extra whitespace and normalize
  const cleanedText = bodyText
    .replace(/\s+/g, ' ') // Replace multiple whitespace with single space
    .replace(/\n\s*\n/g, '\n') // Remove empty lines
    .trim();
  
  return cleanedText;
}

// Function that will be injected into the page
export function extractDataFromPage(): JobData {
  const data: JobData = {};

  // Check for error pages or browser compatibility messages
  const pageText = document.body?.innerText || '';
  if (
    pageText.includes('browser is no longer supported') ||
    pageText.includes('Internet Explorer') ||
    pageText.includes('unsupported browser') ||
    pageText.includes('please upgrade your browser')
  ) {
    // Try to find the actual job content or return error
    const mainContent = document.querySelector('main, [role="main"], .job-content, .job-details');
    if (!mainContent) {
      throw new Error('This page appears to be showing a browser compatibility message. Try refreshing the page or using a different job site.');
    }
  }

  // Extract from LinkedIn
  if (window.location.hostname.includes('linkedin.com')) {
    data.title = document.querySelector('.job-details-jobs-unified-top-card__job-title, h1.topcard__title, .jobs-unified-top-card__job-title')?.textContent?.trim();
    data.company = document.querySelector('.job-details-jobs-unified-top-card__company-name, .topcard__org-name-link, .jobs-unified-top-card__company-name a')?.textContent?.trim();
    data.location = document.querySelector('.job-details-jobs-unified-top-card__bullet, .topcard__flavor--bullet, .jobs-unified-top-card__bullet')?.textContent?.trim();
    data.description = document.querySelector('.jobs-description__content, .description__text, .jobs-box__html-content')?.textContent?.trim();
    data.type = document.querySelector('.job-details-jobs-unified-top-card__workplace-type, .jobs-unified-top-card__workplace-type')?.textContent?.trim();
  }
  
  // Extract from Indeed
  else if (window.location.hostname.includes('indeed.com')) {
    data.title = document.querySelector('[data-testid="job-title"], h1.jobsearch-JobInfoHeader-title')?.textContent?.trim();
    data.company = document.querySelector('[data-testid="company-name"], .jobsearch-CompanyInfoContainer a')?.textContent?.trim();
    data.location = document.querySelector('[data-testid="job-location"], [data-testid="inlineHeader-companyLocation"]')?.textContent?.trim();
    data.description = document.querySelector('#jobDescriptionText, .jobsearch-JobComponent-description')?.textContent?.trim();
  }
  
  // Extract from Glassdoor
  else if (window.location.hostname.includes('glassdoor.com')) {
    // Updated selectors for modern Glassdoor job pages
    data.title = document.querySelector('[data-test="job-title"], .JobDetails_jobTitle__Rw_gn, h1, .job-title')?.textContent?.trim();
    
    // Try multiple company selectors - company name often appears in various formats
    data.company = document.querySelector('[data-test="employer-name"], .JobDetails_companyName__FqHnR, .employer-name, .companyName, [class*="company"] a, .job-company')?.textContent?.trim();
    
    // Location can be in different places on Glassdoor
    data.location = document.querySelector('[data-test="location"], .JobDetails_location__MbnUM, .location, .job-location, [class*="location"]')?.textContent?.trim();
    
    // Description selectors for Glassdoor
    data.description = document.querySelector('.JobDetails_jobDescription__6VeBn, [data-test="job-description"], .job-description, .jobDescription, #jobDescription, .job-details')?.textContent?.trim();
    
    // Try to extract salary from various Glassdoor elements
    const salaryElement = document.querySelector('.salary, .pay-range, [class*="salary"], .compensation, .wage');
    if (salaryElement?.textContent?.includes('$')) {
      data.salary = salaryElement.textContent.trim();
    }
    
    // Extract job type if available
    const jobTypeElement = document.querySelector('.job-type, .employment-type, [class*="job-type"]');
    if (jobTypeElement) {
      data.type = jobTypeElement.textContent.trim();
    }
    
    // If we still don't have company, try looking in the header area
    if (!data.company) {
      const headerCompany = document.querySelector('header [class*="company"], .employer, .company-info');
      if (headerCompany) {
        data.company = headerCompany.textContent?.trim();
      }
    }
  }
  
  // Extract from SmartRecruiters
  else if (window.location.hostname.includes('smartrecruiters.com') || window.location.hostname.includes('jobs.smartrecruiters.com')) {
    // SmartRecruiters uses different structures, try multiple selectors
    data.title = document.querySelector('h1[itemprop="title"], h1.job-title, h1[class*="job"], [data-test="job-title"], h1')?.textContent?.trim();
    data.company = document.querySelector('[itemprop="hiringOrganization"], .company-name, [class*="company"], [data-test="company-name"]')?.textContent?.trim();
    data.location = document.querySelector('[itemprop="jobLocation"], .job-location, [class*="location"], [data-test="job-location"]')?.textContent?.trim();
    
    // SmartRecruiters often has the description in a section
    const descElement = document.querySelector('[itemprop="description"], section.job-description, [class*="job-description"], [data-test="job-description"], .job-sections');
    if (descElement) {
      data.description = descElement.textContent?.trim();
    }
  }
  
  // Generic extraction for other sites
  else {
    // Try common patterns
    const titleSelectors = ['h1', '[class*="job-title"]', '[class*="position"]', '[id*="job-title"]'];
    const companySelectors = ['[class*="company"]', '[class*="employer"]', '[class*="organization"]'];
    const locationSelectors = ['[class*="location"]', '[class*="place"]', '[class*="city"]'];
    const descriptionSelectors = ['[class*="description"]', '[class*="details"]', '[class*="summary"]'];

    for (const selector of titleSelectors) {
      if (!data.title) {
        data.title = document.querySelector(selector)?.textContent?.trim();
      }
    }

    for (const selector of companySelectors) {
      if (!data.company) {
        data.company = document.querySelector(selector)?.textContent?.trim();
      }
    }

    for (const selector of locationSelectors) {
      if (!data.location) {
        data.location = document.querySelector(selector)?.textContent?.trim();
      }
    }

    for (const selector of descriptionSelectors) {
      if (!data.description) {
        data.description = document.querySelector(selector)?.textContent?.trim();
      }
    }
  }

  // Clean up description if too long
  if (data.description && data.description.length > 5000) {
    data.description = data.description.substring(0, 5000) + '...';
  }

  data.url = window.location.href;

  return data;
}

export default App;
