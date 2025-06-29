"use client"

import * as React from "react"
import { useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Download, FileText, Sparkles, Palette } from "lucide-react"

// Enhanced style options with better colors
const PDF_STYLES = [
  {
    key: "modern",
    name: "Modern",
    description: "Clean design with blue accents",
    colors: {
      primary: "#2563eb",
      secondary: "#1e40af", 
      accent: "#3b82f6",
      background: "#ffffff",
      text: "#1f2937"
    }
  },
  {
    key: "professional",
    name: "Professional", 
    description: "Traditional business layout",
    colors: {
      primary: "#374151",
      secondary: "#1f2937",
      accent: "#6b7280",
      background: "#ffffff",
      text: "#111827"
    }
  },
  {
    key: "creative",
    name: "Creative",
    description: "Modern layout with purple accents",
    colors: {
      primary: "#7c3aed",
      secondary: "#5b21b6",
      accent: "#a855f7",
      background: "#ffffff",
      text: "#1f2937"
    }
  }
]

interface PreviewData {
  content: string
  style: string
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    text: string
  }
  company_name: string
  job_title: string
  content_type: "cover_letter" | "resume"
  personal_info?: {
    fullName: string
    email: string
    phone: string
    address: string
    linkedin: string
    website: string
  }
  work_experience?: Array<{
    title: string
    company: string
    startYear: string
    endYear: string
    description: string
  }>
  education?: Array<{
    degree: string
    school: string
    year: string
    description: string
  }>
  skills?: string
  additional_sections?: string
}

export default function PreviewPage() {
  const searchParams = useSearchParams()
  const [previewData, setPreviewData] = React.useState<PreviewData | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [currentStyle, setCurrentStyle] = React.useState("modern")
  const [showStyleSelector, setShowStyleSelector] = React.useState(false)

  React.useEffect(() => {
    try {
      const storedData = sessionStorage.getItem('pdf_preview_data')
      if (storedData) {
        const data = JSON.parse(storedData)
        setPreviewData(data)
        setCurrentStyle(data.style || "modern")
      }
    } catch (error) {
      console.error('Failed to load preview data:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // Get current style colors
  const getCurrentColors = () => {
    const style = PDF_STYLES.find(s => s.key === currentStyle) || PDF_STYLES[0]
    return style.colors
  }

  // Close style selector when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element
      if (!target.closest('.style-selector-container')) {
        setShowStyleSelector(false)
      }
    }

    if (showStyleSelector) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showStyleSelector])

  // Simple markdown to HTML conversion
  const formatContent = (content: string) => {
    if (!content) return ""
    
    return content
      // Bold text
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
      // Italic text
      .replace(/\*(.*?)\*/g, '<em class="italic text-gray-700">$1</em>')
      // Bullet points
      .replace(/^• (.*$)/gim, '<li class="ml-6 mb-2 list-disc">$1</li>')
      // Section dividers
      .replace(/^---$/gm, '<hr class="my-6 border-gray-300">')
      // Paragraphs (double line breaks)
      .replace(/\n\n/g, '</p><p class="mb-4 leading-relaxed">')
      // Single line breaks
      .replace(/\n/g, '<br>')
      // Wrap consecutive list items in ul tags
      .replace(/(<li.*?<\/li>(\s*<li.*?<\/li>)*)/g, '<ul class="mb-4 space-y-1">$1</ul>')
  }

  const handleGoBack = () => {
    if (window.history.length > 1) {
      window.history.back()
    } else {
      window.close()
    }
  }

  const handleDownload = () => {
    // This would trigger the PDF download with the same data
    if (previewData) {
      // Store the data and send message to parent window if in popup
      if (window.opener) {
        window.opener.postMessage({
          type: 'download_pdf',
          data: previewData
        }, window.location.origin)
      }
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading preview...</p>
        </div>
      </div>
    )
  }

  if (!previewData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Preview Not Found</h1>
          <p className="text-gray-600 mb-4">
            The preview data could not be loaded. Please go back and try again.
          </p>
          <Button onClick={handleGoBack} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    )
  }

  const formattedContent = formatContent(previewData.content)

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button 
                onClick={handleGoBack}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
              
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">
                    {previewData.content_type === "cover_letter" ? "Cover Letter" : "Resume"} Preview
                  </h1>
                  <p className="text-sm text-gray-600">
                    {previewData.company_name && previewData.job_title
                      ? `${previewData.job_title} at ${previewData.company_name}`
                      : "Document Preview"
                    }
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Style Selector */}
              <div className="relative style-selector-container">
                <Button
                  onClick={() => setShowStyleSelector(!showStyleSelector)}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                  style={{ 
                    borderColor: getCurrentColors().primary,
                    color: getCurrentColors().primary
                  }}
                >
                  <Palette className="h-4 w-4" />
                  <span className="hidden sm:inline">Style</span>
                </Button>

                {showStyleSelector && (
                  <div className="absolute right-0 top-full mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20 p-3">
                    <div className="space-y-2">
                      <h3 className="text-sm font-medium text-gray-900 mb-3">Choose Style</h3>
                      {PDF_STYLES.map((style) => (
                        <button
                          key={style.key}
                          onClick={() => {
                            setCurrentStyle(style.key)
                            setShowStyleSelector(false)
                          }}
                          className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all ${
                            currentStyle === style.key
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          <div
                            className="w-4 h-4 rounded-full flex-shrink-0"
                            style={{ backgroundColor: style.colors.primary }}
                          />
                          <div className="text-left">
                            <div className="text-sm font-medium text-gray-900">
                              {style.name}
                            </div>
                            <div className="text-xs text-gray-500">
                              {style.description}
                            </div>
                          </div>
                          {currentStyle === style.key && (
                            <div className="ml-auto w-2 h-2 bg-blue-500 rounded-full" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <Badge 
                variant="outline" 
                className="capitalize"
                style={{ 
                  borderColor: getCurrentColors().primary,
                  color: getCurrentColors().primary
                }}
              >
                {PDF_STYLES.find(s => s.key === currentStyle)?.name} Style
              </Badge>
              
              <Button 
                onClick={handleDownload}
                className="flex items-center gap-2 text-white"
                style={{ 
                  backgroundColor: getCurrentColors().primary,
                  borderColor: getCurrentColors().primary
                }}
              >
                <Download className="h-4 w-4" />
                <span className="hidden sm:inline">Download PDF</span>
                <span className="sm:hidden">PDF</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden border">
          {/* Document Header */}
          <div 
            className="text-center py-8 px-6 border-b-4"
            style={{ 
              backgroundColor: getCurrentColors().background,
              borderColor: getCurrentColors().primary
            }}
          >
            {previewData.content_type === "cover_letter" ? (
              <div>
                <h1 
                  className="text-3xl font-bold mb-3"
                  style={{ color: getCurrentColors().primary }}
                >
                  Cover Letter
                </h1>
                {(previewData.job_title || previewData.company_name) && (
                  <p className="text-lg text-gray-600 mb-2">
                    {previewData.job_title} {previewData.job_title && previewData.company_name && "at"} {previewData.company_name}
                  </p>
                )}
                {previewData.personal_info?.fullName && (
                  <p className="text-base text-gray-700 font-medium">
                    {previewData.personal_info.fullName}
                  </p>
                )}
              </div>
            ) : (
              <div>
                <h1 
                  className="text-3xl font-bold mb-3"
                  style={{ color: getCurrentColors().primary }}
                >
                  {previewData.personal_info?.fullName || "Professional Resume"}
                </h1>
                {previewData.personal_info?.email && (
                  <p className="text-base text-gray-600">
                    {previewData.personal_info.email}
                  </p>
                )}
                {previewData.personal_info?.phone && (
                  <p className="text-base text-gray-600">
                    {previewData.personal_info.phone}
                  </p>
                )}
              </div>
            )}
            <p className="text-sm text-gray-500 mt-4">
              Generated on {new Date().toLocaleDateString()}
            </p>
          </div>

          {/* Document Content */}
          <div className="p-8">
            <div 
              className="border-l-4 pl-6 prose prose-lg max-w-none"
              style={{ borderColor: getCurrentColors().accent }}
            >
              <div 
                className="text-base leading-relaxed"
                style={{ color: getCurrentColors().text }}
                dangerouslySetInnerHTML={{
                  __html: `<p class="mb-4 leading-relaxed">${formattedContent}</p>`
                }}
              />
            </div>

            {/* Footer */}
            <div className="mt-12 pt-6 border-t text-center">
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                <Sparkles className="h-4 w-4" />
                <span>Generated by PDF Generator</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 