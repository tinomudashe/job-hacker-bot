// Background service worker
// Handles communication between extension and app

interface MessageData {
  action: string;
  data?: any;
}

// Track app tabs for communication
const appTabs = new Set<number>();

// Persistent connections to content scripts
const contentConnections = new Map<number, chrome.runtime.Port>();


// Listen for persistent connections
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === 'content-script') {
    const tabId = port.sender?.tab?.id;
    if (tabId) {
      contentConnections.set(tabId, port);
      
      // Handle disconnection
      port.onDisconnect.addListener(() => {
        contentConnections.delete(tabId);
      });
      
      // Handle messages from content script
      port.onMessage.addListener((msg) => {
        if (msg.action === 'jobDataUpdate') {
          // Forward to app if connected
          sendMessageToApp({
            action: 'liveUpdate',
            data: msg.data,
            tabId: tabId
          });
        }
      });
    }
  }
});

// Job extraction state
const extractionState = new Map<number, {
  status: 'idle' | 'extracting' | 'complete' | 'error';
  data?: any;
  error?: string;
}>();

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Job Hacker Bot extension installed');
  
  // Set default settings
  chrome.storage.local.set({
    appUrl: 'http://localhost:3000',
    autoExtract: false,
    enableContextMenu: true
  });
  
  // Configure side panel to open on action click (Chrome 116+)
  // This allows the extension icon to open the side panel
  if ((chrome as any).sidePanel && (chrome as any).sidePanel.setPanelBehavior) {
    (chrome as any).sidePanel.setPanelBehavior({ 
      openPanelOnActionClick: true 
    }).then(() => {
      console.log('Side panel configured to open on action click');
    }).catch((error: any) => {
      console.log('Could not set panel behavior:', error);
    });
  }
  
  // Create generic context menu for all pages
  chrome.contextMenus.create({
    id: 'extract-job',
    title: 'Extract Job Details',
    contexts: ['page', 'frame']
  });
  
  chrome.contextMenus.create({
    id: 'save-selection',
    title: 'Save to Job Hacker Bot',
    contexts: ['selection']
  });
});

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request: MessageData, sender, sendResponse) => {
  if (request.action === 'openApp') {
    handleOpenApp(request.data);
  } else if (request.action === 'checkConnection') {
    checkAppConnection().then(sendResponse);
    return true; // Keep message channel open for async response
  } else if (request.action === 'sendToApp') {
    sendMessageToApp(request.data).then(sendResponse);
    return true; // Keep message channel open for async response
  } else if (request.action === 'registerAppTab') {
    // Register tab as app instance
    if (sender.tab?.id) {
      appTabs.add(sender.tab.id);
      sendResponse({ success: true });
    }
  } else if (request.action === 'extractJob') {
    // Handle job extraction request
    if (sender.tab?.id) {
      handleJobExtraction(sender.tab.id, request.data).then(sendResponse);
      return true;
    }
  } else if (request.action === 'getExtractionState') {
    // Get current extraction state for a tab
    if (sender.tab?.id) {
      const state = extractionState.get(sender.tab.id) || { status: 'idle' };
      sendResponse(state);
    }
  } else if (request.action === 'openSidePanel') {
    // Open extension in side panel
    openSidePanel().then(sendResponse);
    return true;
  }
});

// Handle opening the app with data
async function handleOpenApp(data: any) {
  const { appUrl } = await chrome.storage.local.get(['appUrl']);
  const url = appUrl || 'http://localhost:3000';
  
  // Create URL with params
  const params = new URLSearchParams({
    source: 'extension',
    action: data.action || 'open',
    ...data
  });
  
  const targetUrl = `${url}?${params.toString()}`;
  
  // Check if app is already open in a tab
  const existingTabs = await chrome.tabs.query({ 
    url: `${url}/*` 
  });
  
  if (existingTabs.length > 0) {
    // Focus existing tab and update URL
    const tab = existingTabs[0];
    await chrome.tabs.update(tab.id!, { 
      active: true,
      url: targetUrl 
    });
    
    // Focus the window containing the tab
    if (tab.windowId) {
      await chrome.windows.update(tab.windowId, { focused: true });
    }
    
    // Track this tab
    if (tab.id) {
      appTabs.add(tab.id);
    }
  } else {
    // Open in new tab
    const newTab = await chrome.tabs.create({
      url: targetUrl
    });
    
    // Track new tab
    if (newTab.id) {
      appTabs.add(newTab.id);
    }
  }
}

// Check if app is running with retry logic
async function checkAppConnection(retries = 3): Promise<boolean> {
  const { appUrl } = await chrome.storage.local.get(['appUrl']);
  const url = appUrl || 'http://localhost:3000';
  
  for (let i = 0; i < retries; i++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch(`${url}/api/health`, {
        method: 'GET',
        mode: 'cors',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        return true;
      }
    } catch (error: any) {
      if (i === retries - 1) {
        console.error('Failed to connect to app after retries:', error);
      } else {
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
      }
    }
  }
  
  return false;
}

// Handle tab updates (optional: auto-extract on job pages)
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    const { autoExtract } = await chrome.storage.local.get(['autoExtract']);
    
    if (autoExtract) {
      const jobSites = [
        'linkedin.com/jobs',
        'indeed.com',
        'glassdoor.com',
        'greenhouse.io',
        'lever.co'
      ];
      
      const isJobSite = jobSites.some(site => tab.url!.includes(site));
      
      if (isJobSite) {
        // Show notification badge
        chrome.action.setBadgeText({ text: '!', tabId });
        chrome.action.setBadgeBackgroundColor({ color: '#3B82F6' });
        
        // Clear badge after 5 seconds
        setTimeout(() => {
          chrome.action.setBadgeText({ text: '', tabId });
        }, 5000);
      }
    }
  }
});

// Handle extension icon click (alternative to popup)
chrome.action.onClicked.addListener((tab) => {
  // If no popup is defined, this will be triggered
  // You can use this to inject content script directly
  if (tab.id) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        // Quick extraction function
        const indicator = document.getElementById('job-hacker-indicator');
        if (indicator) {
          indicator.style.display = 'flex';
          indicator.textContent = 'Extracting job data...';
          
          setTimeout(() => {
            indicator.style.display = 'none';
          }, 2000);
        }
      }
    });
  }
});

// Send message to app tabs
async function sendMessageToApp(data: any): Promise<any> {
  const { appUrl } = await chrome.storage.local.get(['appUrl']);
  const url = appUrl || 'http://localhost:3000';
  
  // Find all app tabs
  const appTabsArray = await chrome.tabs.query({ 
    url: `${url}/*` 
  });
  
  if (appTabsArray.length === 0) {
    return { success: false, error: 'No app tabs open' };
  }
  
  // Send to all app tabs
  const results = await Promise.allSettled(
    appTabsArray.map(tab => {
      if (tab.id) {
        return chrome.tabs.sendMessage(tab.id, {
          source: 'job-extension',
          ...data
        });
      }
      return Promise.reject('Tab has no ID');
    })
  );
  
  // Return first successful response
  const successfulResult = results.find(r => r.status === 'fulfilled');
  if (successfulResult && successfulResult.status === 'fulfilled') {
    return successfulResult.value;
  }
  
  return { success: false, error: 'Failed to send message to app' };
}

// Handle job extraction from any site with error handling
async function handleJobExtraction(tabId: number, data?: any): Promise<any> {
  try {
    // Update extraction state
    extractionState.set(tabId, { status: 'extracting' });
    
    // Show extraction badge
    chrome.action.setBadgeText({ text: '...', tabId });
    chrome.action.setBadgeBackgroundColor({ color: '#FFA500' });
    
    // Check if content script is already injected
    try {
      await chrome.tabs.sendMessage(tabId, { action: 'ping' });
    } catch {
      // Inject content script if not already present
      try {
        await chrome.scripting.executeScript({
          target: { tabId },
          files: ['content/index.js']
        });
        
        // Wait for script to initialize
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (injectError: any) {
        throw new Error(`Failed to inject content script: ${injectError.message}`);
      }
    }
    
    // Request extraction from content script with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await Promise.race([
      chrome.tabs.sendMessage(tabId, {
        action: 'extractJobData',
        options: data
      }),
      new Promise((_, reject) => {
        controller.signal.addEventListener('abort', () => 
          reject(new Error('Extraction timeout'))
        );
      })
    ]);
    
    clearTimeout(timeoutId);
    
    // Update state with results
    extractionState.set(tabId, { 
      status: 'complete', 
      data: response 
    });
    
    // Update badge
    chrome.action.setBadgeText({ text: '✓', tabId });
    chrome.action.setBadgeBackgroundColor({ color: '#00FF00' });
    
    // Clear badge after 3 seconds
    setTimeout(() => {
      chrome.action.setBadgeText({ text: '', tabId });
    }, 3000);
    
    // Auto-open app with extracted data
    if (response && (response as any).success) {
      await handleOpenApp({
        action: 'import',
        jobData: (response as any).data,
        sourceUrl: (response as any).url
      });
    }
    
    return response;
  } catch (error: any) {
    extractionState.set(tabId, { 
      status: 'error', 
      error: error.message 
    });
    
    // Show error badge
    chrome.action.setBadgeText({ text: '!', tabId });
    chrome.action.setBadgeBackgroundColor({ color: '#FF0000' });
    
    // Clear badge after 3 seconds
    setTimeout(() => {
      chrome.action.setBadgeText({ text: '', tabId });
    }, 3000);
    
    return { success: false, error: error.message };
  }
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab?.id) return;
  
  if (info.menuItemId === 'extract-job') {
    // Extract job from current page
    await handleJobExtraction(tab.id, { url: info.pageUrl });
  } else if (info.menuItemId === 'save-selection' && info.selectionText) {
    // Save selected text to app
    await handleOpenApp({
      action: 'saveText',
      text: info.selectionText,
      sourceUrl: info.pageUrl
    });
  }
});

// Clean up closed tabs
chrome.tabs.onRemoved.addListener((tabId) => {
  appTabs.delete(tabId);
  extractionState.delete(tabId);
  
  // Clean up any persistent connections
  const connection = contentConnections.get(tabId);
  if (connection) {
    connection.disconnect();
    contentConnections.delete(tabId);
  }
});

// Listen for tab URL changes
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.url) {
    const { appUrl } = await chrome.storage.local.get(['appUrl']);
    const url = appUrl || 'http://localhost:3000';
    
    // Check if tab navigated to/from app
    if (tab.url?.startsWith(url)) {
      appTabs.add(tabId);
    } else {
      appTabs.delete(tabId);
    }
  }
});

// Handle side panel request from popup
async function openSidePanel(): Promise<{ success: boolean }> {
  try {
    // Note: chrome.sidePanel.open() can only be called from user gesture in the popup
    // The background script cannot directly open the side panel
    // Return false to let the popup handle it
    return { success: false };
  } catch (error) {
    console.error('Side panel error:', error);
    return { success: false };
  }
}

export {};