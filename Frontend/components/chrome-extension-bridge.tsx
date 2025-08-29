'use client'

import { useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'

// Declare chrome types for TypeScript
declare global {
  interface Window {
    chrome?: any
  }
}

/**
 * Chrome Extension Bridge Component
 * This component runs on the Job Hacker Bot website and communicates with the Chrome extension
 * to share the Clerk authentication session
 */
export function ChromeExtensionBridge() {
  const { isSignedIn, getToken, userId, sessionId } = useAuth()

  useEffect(() => {
    // Function to send session to extension
    const sendSessionToExtension = async () => {
      if (!isSignedIn || typeof window === 'undefined' || !window.chrome?.runtime) {
        return
      }

      try {
        // Get the auth token
        const token = await getToken()
        
        if (!token) {
          console.log('No auth token available')
          return
        }

        // Get the extension ID from environment variable or use a default
        const extensionId = process.env.NEXT_PUBLIC_CHROME_EXTENSION_ID || ''
        
        if (!extensionId) {
          console.log('Chrome extension ID not configured')
          return
        }

        // Calculate token expiration (Clerk tokens typically expire in 1 hour)
        const expiresAt = Date.now() + (60 * 60 * 1000)

        // Send the session data to the extension
        window.chrome.runtime.sendMessage(
          extensionId,
          {
            action: 'setClerkSession',
            token: token,
            userId: userId,
            sessionId: sessionId,
            expiresAt: expiresAt
          },
          (response: any) => {
            if (window.chrome.runtime.lastError) {
              console.log('Extension not installed or not responding:', window.chrome.runtime.lastError.message)
            } else if (response?.success) {
              console.log('Session shared with extension successfully')
            }
          }
        )
      } catch (error) {
        console.error('Failed to share session with extension:', error)
      }
    }

    // Send session immediately if signed in
    if (isSignedIn) {
      sendSessionToExtension()
    }

    // Also send when session changes
    const interval = setInterval(() => {
      if (isSignedIn) {
        sendSessionToExtension()
      }
    }, 30000) // Refresh every 30 seconds

    // Clear session in extension when signing out
    return () => {
      clearInterval(interval)
      if (!isSignedIn && typeof window !== 'undefined' && window.chrome?.runtime) {
        const extensionId = process.env.NEXT_PUBLIC_CHROME_EXTENSION_ID || ''
        if (extensionId) {
          window.chrome.runtime.sendMessage(
            extensionId,
            { action: 'clearClerkSession' },
            () => {
              // Ignore errors when extension is not installed
              if (window.chrome.runtime.lastError) {
                console.log('Extension not responding')
              }
            }
          )
        }
      }
    }
  }, [isSignedIn, getToken, userId, sessionId])

  // This component doesn't render anything
  return null
}

export default ChromeExtensionBridge