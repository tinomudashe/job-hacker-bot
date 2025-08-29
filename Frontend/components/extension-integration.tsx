'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { PDFGenerationDialog } from './chat/pdf-generation-dialog'
import { toast } from 'sonner'

/**
 * Extension Integration Component
 * Handles incoming requests from the Chrome extension to open the PDF dialog
 * with generated content
 */
export function ExtensionIntegration() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogContent, setDialogContent] = useState<{
    type: 'cover_letter' | 'resume';
    content: string;
    companyName: string;
    jobTitle: string;
  } | null>(null)

  useEffect(() => {
    // Check if this is a request from the extension
    const action = searchParams.get('action')
    const type = searchParams.get('type')
    const company = searchParams.get('company')
    const title = searchParams.get('title')
    const generated = searchParams.get('generated')
    const encodedData = searchParams.get('data')

    if (action === 'open_pdf_dialog' && type && generated === 'true') {
      // Decode the content from URL parameters
      let data: any = null;
      
      if (encodedData) {
        try {
          // Decode from base64 and parse JSON
          const decodedString = decodeURIComponent(atob(encodedData));
          data = JSON.parse(decodedString);
        } catch (error) {
          console.error('Error decoding content data:', error);
          toast.error('Failed to decode generated content');
          return;
        }
      }
      
      if (data) {
        try {
          // Prepare content for the dialog
          let content = ''
          
          if (type === 'cover_letter' && data.content) {
            content = data.content
          } else if (type === 'resume' && data.content) {
            // For resume, we might have the full resume data
            // Convert it to a string format if needed
            if (typeof data.content === 'object') {
              content = JSON.stringify(data.content, null, 2)
            } else {
              content = data.content
            }
          }

          // Set dialog content
          setDialogContent({
            type: type as 'cover_letter' | 'resume',
            content,
            companyName: company || data.companyName || '',
            jobTitle: title || data.jobTitle || ''
          })

          // Open the dialog
          setDialogOpen(true)

          // Clean up URL parameters
          const newUrl = new URL(window.location.href)
          newUrl.searchParams.delete('action')
          newUrl.searchParams.delete('type')
          newUrl.searchParams.delete('company')
          newUrl.searchParams.delete('title')
          newUrl.searchParams.delete('generated')
          newUrl.searchParams.delete('data')
          router.replace(newUrl.pathname + newUrl.search)

          // Show success message
          toast.success(`${type === 'cover_letter' ? 'Cover letter' : 'Resume'} generated successfully!`)
        } catch (error) {
          console.error('Failed to parse extension content:', error)
          toast.error('Failed to load generated content')
        }
      } else {
        toast.error('No generated content found. Please try again.')
      }
    }
  }, [searchParams, router])

  // Also listen for postMessage events from the extension (alternative method)
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Validate origin if needed
      if (event.data?.source === 'job-hacker-extension' && event.data?.action === 'open_dialog') {
        const { type, content, companyName, jobTitle } = event.data

        setDialogContent({
          type: type as 'cover_letter' | 'resume',
          content: content || '',
          companyName: companyName || '',
          jobTitle: jobTitle || ''
        })

        setDialogOpen(true)
        toast.success('Content received from extension')
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [])

  if (!dialogContent) {
    return null
  }

  return (
    <PDFGenerationDialog
      open={dialogOpen}
      onOpenChange={setDialogOpen}
      contentType={dialogContent.type}
      initialContent={dialogContent.content}
      companyName={dialogContent.companyName}
      jobTitle={dialogContent.jobTitle}
    />
  )
}

export default ExtensionIntegration