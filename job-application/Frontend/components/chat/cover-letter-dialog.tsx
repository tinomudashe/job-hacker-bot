"use client"

import * as React from "react"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { 
  FileText, 
  Download, 
  Edit3, 
  Sparkles,
  Loader2,
  ExternalLink,
  Briefcase,
  User,
  X
} from "lucide-react"
import { useAuth } from "@clerk/nextjs"
import { toast } from "@/lib/toast"

interface CoverLetterDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialContent?: string
  companyName?: string
  jobTitle?: string
}

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

export function CoverLetterDialog({
  open,
  onOpenChange,
  initialContent = "",
  companyName = "",
  jobTitle = ""
}: CoverLetterDialogProps) {
  const [selectedStyle, setSelectedStyle] = React.useState("modern")
  const [editedContent, setEditedContent] = React.useState(initialContent)
  const [editedCompanyName, setEditedCompanyName] = React.useState(companyName)
  const [editedJobTitle, setEditedJobTitle] = React.useState(jobTitle)
  const [isGenerating, setIsGenerating] = React.useState(false)
  const [isMobile, setIsMobile] = React.useState(false)

  // Personal information fields
  const [personalInfo, setPersonalInfo] = React.useState({
    fullName: "",
    email: "",
    phone: "",
    address: "",
    linkedin: "",
    website: ""
  })

  // Collapsible sections state
  const [expandedSections, setExpandedSections] = React.useState({
    personalInfo: true,
    content: true
  })

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const { getToken } = useAuth()

  // Handle mobile detection
  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Improved modal scroll lock
  React.useEffect(() => {
    if (!open) return

    const originalScrollY = window.scrollY
    const originalBodyStyle = {
      overflow: document.body.style.overflow,
      position: document.body.style.position,
      top: document.body.style.top,
      width: document.body.style.width,
    }

    document.body.style.overflow = 'hidden'
    document.body.style.scrollbarGutter = 'stable'
    document.body.classList.add('modal-open')

    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
    if (isIOS) {
      document.body.style.position = 'fixed'
      document.body.style.top = `-${originalScrollY}px`
      document.body.style.width = '100%'
    }

    const preventDefault = (e: TouchEvent) => {
      const target = e.target as Element
      const isWithinModal = target.closest('[data-radix-dialog-content]')
      const isScrollableContent = target.closest('textarea, input, [role="textbox"]') || 
                                 target.closest('[data-scrollable="true"]')
      
      if (!isWithinModal && !isScrollableContent) {
        e.preventDefault()
      }
    }

    document.addEventListener('touchmove', preventDefault, { passive: false })

    return () => {
      document.body.style.overflow = originalBodyStyle.overflow
      document.body.style.position = originalBodyStyle.position
      document.body.style.top = originalBodyStyle.top
      document.body.style.width = originalBodyStyle.width
      document.body.style.scrollbarGutter = ''
      document.body.classList.remove('modal-open')
      
      if (isIOS) {
        window.scrollTo(0, originalScrollY)
      }
      
      document.removeEventListener('touchmove', preventDefault)
    }
  }, [open])

  // Initialize content
  React.useEffect(() => {
    if (initialContent && !editedContent) {
      setEditedContent(initialContent)
    }
  }, [initialContent])

  const handleDownload = async () => {
    if (isGenerating) return
    
    setIsGenerating(true)
    
    try {
      const token = await getToken()
      if (!token) {
        throw new Error("Please sign in to download PDFs")
      }
      
      const contentToUse = getCombinedContent()
      if (!contentToUse || contentToUse.trim().length === 0) {
        throw new Error("Please add some content before downloading")
      }
      
      const selectedStyleData = PDF_STYLES.find(s => s.key === selectedStyle) || PDF_STYLES[0]
      
      const requestData = {
        content_text: contentToUse.trim(),
        content_id: null,
        style: selectedStyle,
        colors: selectedStyleData.colors,
        company_name: editedCompanyName || "",
        job_title: editedJobTitle || "",
        content_type: "cover_letter"
      }

      const response = await fetch('/api/pdf/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        let errorMessage = 'Failed to generate PDF'
        try {
          const responseContentType = response.headers.get('content-type')
          if (responseContentType && responseContentType.includes('application/json')) {
            const errorData = await response.json()
            errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage
          } else {
            const errorText = await response.text()
            errorMessage = errorText || `HTTP ${response.status}: ${response.statusText}`
          }
        } catch (parseError) {
          errorMessage = `Server error (${response.status}): ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      const responseContentType = response.headers.get('content-type')
      if (!responseContentType || !responseContentType.includes('application/pdf')) {
        throw new Error("Server did not return a PDF file")
      }

      const blob = await response.blob()
      if (blob.size === 0) {
        throw new Error("Received empty PDF file")
      }
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      
      const fileName = `cover-letter-${selectedStyle}-${new Date().toISOString().split('T')[0]}.pdf`
      a.download = fileName
      
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success(`Cover letter downloaded successfully!`, {
        description: `File: ${fileName}`
      })
      
    } catch (error) {
      console.error('Download error:', error)
      
      let userMessage = 'Failed to download PDF'
      if (error instanceof Error) {
        userMessage = error.message
      }
      
      toast.error(userMessage)
    } finally {
      setIsGenerating(false)
    }
  }

  const handlePreview = () => {
    try {
      const contentToUse = getCombinedContent()
      if (!contentToUse || contentToUse.trim().length === 0) {
        throw new Error("Please add some content before previewing")
      }
      
      const selectedStyleData = PDF_STYLES.find(s => s.key === selectedStyle) || PDF_STYLES[0]
      
      const previewData = {
        content: contentToUse.trim(),
        style: selectedStyle,
        colors: selectedStyleData.colors,
        company_name: editedCompanyName || "",
        job_title: editedJobTitle || "",
        content_type: "cover_letter",
        personal_info: personalInfo
      }

      sessionStorage.setItem('pdf_preview_data', JSON.stringify(previewData))
      
      const previewUrl = `/preview?type=cover_letter&style=${selectedStyle}`
      const newWindow = window.open(previewUrl, '_blank', 'noopener,noreferrer')
      
      if (newWindow) {
        newWindow.focus()
        toast.success("Preview opened in new tab")
      } else {
        toast.error("Please allow popups to view the preview")
      }
      
    } catch (error) {
      console.error('Preview error:', error)
      
      let userMessage = 'Failed to open preview'
      if (error instanceof Error) {
        userMessage = error.message
      }
      
      toast.error(userMessage)
    }
  }

  const selectedStyleData = PDF_STYLES.find(s => s.key === selectedStyle) || PDF_STYLES[0]
  
  // Check if content is valid
  const isContentValid = React.useMemo(() => {
    return editedContent && editedContent.trim().length > 0
  }, [editedContent])

  // Combine all content for PDF generation
  const getCombinedContent = () => {
    let combined = ""

    // Personal Information
    if (Object.values(personalInfo).some(val => val.trim().length > 0)) {
      combined += "**Personal Information**\n\n"
      if (personalInfo.fullName) combined += `**Name:** ${personalInfo.fullName}\n`
      if (personalInfo.email) combined += `**Email:** ${personalInfo.email}\n`
      if (personalInfo.phone) combined += `**Phone:** ${personalInfo.phone}\n`
      if (personalInfo.address) combined += `**Address:** ${personalInfo.address}\n`
      if (personalInfo.linkedin) combined += `**LinkedIn:** ${personalInfo.linkedin}\n`
      if (personalInfo.website) combined += `**Website:** ${personalInfo.website}\n`
      combined += "\n---\n\n"
    }

    // Cover letter content
    if (editedContent.trim()) {
      combined += editedContent
    }

    return combined.trim()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] sm:max-w-5xl max-h-[92vh] sm:max-h-[95vh] w-[95vw] h-[92vh] sm:w-[90vw] sm:h-[90vh] flex flex-col bg-white/95 dark:bg-gray-950/95 backdrop-blur-xl rounded-2xl sm:rounded-2xl overflow-hidden p-0 border border-white/20 dark:border-gray-800/50 shadow-2xl">
        {/* Header */}
        <div className="flex-shrink-0 bg-white/90 dark:bg-gray-950/90 backdrop-blur-md border-b border-white/40 dark:border-gray-800/60 p-3 sm:p-5 pr-12 sm:pr-14 relative z-10">
          {/* Mobile Layout */}
          <div className="flex sm:hidden items-start justify-between gap-3">
            {/* Left: Document Type */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-300/40 shadow-lg dark:from-blue-400/20 dark:to-purple-400/20 dark:border-blue-600/40 flex items-center justify-center backdrop-blur-sm flex-shrink-0">
                <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="min-w-0 flex-1">
                <DialogTitle className="text-lg font-bold text-gray-900 dark:text-gray-100 leading-tight">
                  Cover Letter Generator
                </DialogTitle>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5 leading-tight">
                  Create your professional document
                </p>
              </div>
            </div>
            
            {/* Right: Close Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onOpenChange(false)}
              className="h-9 w-9 rounded-lg transition-all duration-300 hover:scale-105 bg-gray-100/90 border border-gray-200/70 backdrop-blur-sm hover:bg-gray-200/95 hover:border-gray-300/80 dark:bg-gray-800/90 dark:border-gray-700/70 dark:hover:bg-gray-700/95 dark:hover:border-gray-600/80 flex-shrink-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Mobile Actions Row */}
          <div className="flex sm:hidden items-center justify-center gap-2 mt-3 pt-3 border-t border-gray-200/50 dark:border-gray-700/50">
            <Button
              onClick={handlePreview}
              variant="outline"
              size="sm"
              disabled={!isContentValid}
              className="flex items-center gap-2 text-sm px-4 h-9 rounded-lg transition-all duration-300 hover:scale-105 bg-white/80 border-gray-300/60 backdrop-blur-sm hover:bg-white/95 hover:border-gray-400/70 hover:shadow-md dark:bg-gray-800/80 dark:border-gray-600/60 dark:hover:bg-gray-700/95 dark:hover:border-gray-500/70 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 font-medium flex-1"
            >
              <ExternalLink className="h-4 w-4" />
              <span>Preview</span>
            </Button>
            
            <Button
              onClick={handleDownload}
              disabled={isGenerating || !isContentValid}
              size="sm"
              className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-sm px-4 h-9 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-blue-600 disabled:hover:to-blue-700 font-semibold transition-all duration-300 hover:scale-105 hover:shadow-md disabled:hover:scale-100 shadow-blue-500/25 flex-1"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
                  <span>Wait...</span>
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" />
                  <span>PDF</span>
                </>
              )}
            </Button>
          </div>

          {/* Mobile Content Status */}
          {!isContentValid && (
            <div className="flex sm:hidden justify-center mt-2">
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center font-medium">
                Add content to enable actions
              </p>
            </div>
          )}

          {/* Desktop Layout */}
          <div className="hidden sm:flex items-center justify-between gap-4">
            {/* Left: Document Type */}
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-300/40 shadow-lg dark:from-blue-400/20 dark:to-purple-400/20 dark:border-blue-600/40 flex items-center justify-center backdrop-blur-sm">
                <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <DialogTitle className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Cover Letter Generator
                </DialogTitle>
                <p className="text-sm text-gray-600 dark:text-gray-400 -mt-0.5">
                  Create your professional cover letter
                </p>
              </div>
            </div>

            {/* Right: Actions */}
            <div className="flex flex-col items-end gap-2">
              <div className="flex items-center gap-3">
                <Button
                  onClick={handlePreview}
                  variant="outline"
                  size="sm"
                  disabled={!isContentValid}
                  className="flex items-center gap-2 text-sm px-4 h-10 rounded-xl transition-all duration-300 hover:scale-105 bg-white/80 border-gray-300/60 backdrop-blur-sm hover:bg-white/95 hover:border-gray-400/70 hover:shadow-lg dark:bg-gray-800/80 dark:border-gray-600/60 dark:hover:bg-gray-700/95 dark:hover:border-gray-500/70 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 font-medium"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>Preview</span>
                </Button>
                
                <Button
                  onClick={handleDownload}
                  disabled={isGenerating || !isContentValid}
                  size="sm"
                  className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-sm px-5 h-10 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-blue-600 disabled:hover:to-blue-700 font-semibold transition-all duration-300 hover:scale-105 hover:shadow-lg disabled:hover:scale-100 shadow-blue-500/25"
                >
                  {isGenerating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4" />
                      <span>Download PDF</span>
                    </>
                  )}
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onOpenChange(false)}
                  className="h-10 w-10 rounded-xl transition-all duration-300 hover:scale-105 bg-gray-100/90 border border-gray-200/70 backdrop-blur-sm hover:bg-gray-200/95 hover:border-gray-300/80 dark:bg-gray-800/90 dark:border-gray-700/70 dark:hover:bg-gray-700/95 dark:hover:border-gray-600/80 ml-2"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              
              {!isContentValid && (
                <p className="text-xs text-gray-500 dark:text-gray-400 text-right font-medium">
                  Add content to enable actions
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-shrink-0 border-b border-white/30 dark:border-gray-800/50 bg-gray-50/80 dark:bg-gray-900/80 backdrop-blur-md">
          <div className="px-4 sm:px-6">
            <div className="flex overflow-x-auto scrollbar-hide -mb-px">
              <button
                onClick={() => toggleSection('personalInfo')}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm whitespace-nowrap transition-colors min-w-0 ${
                  expandedSections.personalInfo
                    ? 'border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <User className="h-4 w-4 flex-shrink-0" />
                <span>Personal Info</span>
              </button>

              <button
                onClick={() => toggleSection('content')}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm whitespace-nowrap transition-colors min-w-0 ${
                  expandedSections.content
                    ? 'border-teal-500 text-teal-600 bg-teal-50 dark:bg-teal-900/20 dark:text-teal-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <Edit3 className="h-4 w-4 flex-shrink-0" />
                <span>Content</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-auto scrollbar-thin" data-scrollable="true">
          <div className="h-full flex flex-col">
            {/* Content Editor */}
            <div className="flex-1 p-3 sm:p-6 bg-gradient-to-br from-gray-50/30 via-white/20 to-gray-100/30 dark:from-gray-900/30 dark:via-gray-800/20 dark:to-gray-900/40 backdrop-blur-sm">
              <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
                
                {/* Job Details Section */}
                {expandedSections.personalInfo && (
                  <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <Briefcase className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 flex-shrink-0" />
                      <span className="truncate">Job Application Details</span>
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 mb-6">
                      <div>
                        <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                          Company Name
                        </Label>
                        <Input
                          placeholder="e.g., Google Inc."
                          value={editedCompanyName}
                          onChange={(e) => setEditedCompanyName(e.target.value)}
                          className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                        />
                      </div>
                      <div>
                        <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                          Job Title
                        </Label>
                        <Input
                          placeholder="e.g., Software Engineer"
                          value={editedJobTitle}
                          onChange={(e) => setEditedJobTitle(e.target.value)}
                          className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                        />
                      </div>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                      <User className="h-4 w-4 text-blue-600 flex-shrink-0" />
                      <span>Personal Information</span>
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                      <div className="space-y-3 sm:space-y-4">
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 sm:mb-2 block">
                            Full Name
                          </Label>
                          <Input
                            placeholder="John Doe"
                            value={personalInfo.fullName}
                            onChange={(e) => setPersonalInfo({...personalInfo, fullName: e.target.value})}
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 sm:mb-2 block">
                            Email Address
                          </Label>
                          <Input
                            placeholder="john.doe@email.com"
                            type="email"
                            value={personalInfo.email}
                            onChange={(e) => setPersonalInfo({...personalInfo, email: e.target.value})}
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 sm:mb-2 block">
                            Phone Number
                          </Label>
                          <Input
                            placeholder="+1 (555) 123-4567"
                            value={personalInfo.phone}
                            onChange={(e) => setPersonalInfo({...personalInfo, phone: e.target.value})}
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                      </div>
                      <div className="space-y-3 sm:space-y-4">
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 sm:mb-2 block">
                            Address
                          </Label>
                          <Input
                            placeholder="City, State, Country"
                            value={personalInfo.address}
                            onChange={(e) => setPersonalInfo({...personalInfo, address: e.target.value})}
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 sm:mb-2 block">
                            LinkedIn Profile
                          </Label>
                          <Input
                            placeholder="linkedin.com/in/johndoe"
                            value={personalInfo.linkedin}
                            onChange={(e) => setPersonalInfo({...personalInfo, linkedin: e.target.value})}
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 sm:mb-2 block">
                            Website/Portfolio
                          </Label>
                          <Input
                            placeholder="johndoe.com"
                            value={personalInfo.website}
                            onChange={(e) => setPersonalInfo({...personalInfo, website: e.target.value})}
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Content Editor Section */}
                {expandedSections.content && (
                  <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <Edit3 className="h-4 w-4 sm:h-5 sm:w-5 text-teal-600 flex-shrink-0" />
                      <span className="truncate">Cover Letter Content</span>
                    </h2>
                    <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                      Cover Letter Text
                    </Label>
                    <Textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      placeholder={`Dear Hiring Manager,

I am writing to express my strong interest in the ${editedJobTitle || '[Job Title]'} position at ${editedCompanyName || '[Company Name]'}. With my background in [Your Field] and [X] years of experience, I am confident that I would be a valuable addition to your team.

In my previous role at [Previous Company], I successfully [Key Achievement]. This experience has equipped me with [Relevant Skills] that directly align with the requirements of this position.

I am particularly drawn to ${editedCompanyName || '[Company Name]'} because [Reason for Interest in Company]. I am excited about the opportunity to contribute to [Specific Project/Goal] and help drive [Company Objective].

Thank you for considering my application. I look forward to discussing how my skills and experience can contribute to your team's success.

Sincerely,
${personalInfo.fullName || '[Your Name]'}`}
                      rows={18}
                      data-scrollable="true"
                      className="resize-none text-sm sm:text-base px-3 sm:px-4 py-2.5 sm:py-3 leading-relaxed min-h-[400px] sm:min-h-[500px] focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all duration-200 cursor-text scrollbar-thin backdrop-blur-sm bg-white/50 dark:bg-gray-900/50"
                      style={{ 
                        fontSize: isMobile ? '16px' : undefined,
                        lineHeight: '1.6',
                        resize: 'none',
                        overflowY: 'auto'
                      }}
                      onFocus={(e) => {
                        setTimeout(() => {
                          e.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }, 100);
                      }}
                    />
                    <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                      <div className="flex items-center gap-4">
                        <span>{editedContent.length} characters</span>
                        <span>~{Math.ceil(editedContent.split(' ').length / 250)} pages</span>
                      </div>
                      <div className="hidden sm:flex items-center gap-2 text-xs text-gray-400">
                        <span>**bold**</span>
                        <span>*italic*</span>
                        <span>• bullets</span>
                      </div>
                    </div>
                  </div>
                )}

              </div>
            </div>
          </div>
        </div>

      </DialogContent>
    </Dialog>
  )
} 