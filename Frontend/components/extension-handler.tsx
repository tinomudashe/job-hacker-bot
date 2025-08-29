'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { toast } from 'sonner'

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

interface ExtensionHandlerProps {
  onJobDataReceived?: (data: JobData, action: 'resume' | 'cover_letter') => void;
}

/**
 * Extension Handler Component
 * Handles incoming data from the Chrome extension
 */
export function ExtensionHandler({ onJobDataReceived }: ExtensionHandlerProps) {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Check if we have data from the extension
    const source = searchParams.get('source')
    const action = searchParams.get('action')
    const dataParam = searchParams.get('data')

    if (source === 'extension' && action && dataParam) {
      try {
        const jobData = JSON.parse(decodeURIComponent(dataParam)) as JobData

        if (action === 'create_document') {
          const docType = searchParams.get('type') as 'resume' | 'cover_letter'
          
          if (docType && onJobDataReceived) {
            // Pass data to parent component
            onJobDataReceived(jobData, docType)
            
            // Show success toast
            toast.success(`Creating ${docType === 'cover_letter' ? 'cover letter' : 'tailored resume'} for ${jobData.title} at ${jobData.company}`)
            
            // Clean up URL
            const newUrl = new URL(window.location.href)
            newUrl.searchParams.delete('source')
            newUrl.searchParams.delete('action')
            newUrl.searchParams.delete('data')
            newUrl.searchParams.delete('type')
            router.replace(newUrl.pathname + newUrl.search)
          }
        }
      } catch (error) {
        console.error('Failed to parse extension data:', error)
        toast.error('Failed to process job data from extension')
      }
    }
  }, [searchParams, router, onJobDataReceived])

  // Listen for postMessage from extension (alternative communication method)
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Verify origin if needed
      if (event.data?.source === 'job-hacker-extension') {
        const { action, jobData, type } = event.data
        
        if (action === 'create_document' && jobData && onJobDataReceived) {
          onJobDataReceived(jobData, type)
          toast.success(`Processing job data from ${jobData.company}`)
        }
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [onJobDataReceived])

  return null
}

export default ExtensionHandler