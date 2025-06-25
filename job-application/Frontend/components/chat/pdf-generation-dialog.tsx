"use client"

import * as React from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { 
  FileText, 
  Download, 
  Eye, 
  Edit3, 
  Palette, 
  Save,
  X,
  FileImage,
  Sparkles,
  CheckCircle,
  Loader2,
  ExternalLink,
  Zap,
  Star
} from "lucide-react"
import { useAuth } from "@clerk/nextjs"
import { toast } from "@/lib/toast"

interface PDFGenerationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  contentType: "cover_letter" | "resume"
  initialContent?: string
  contentId?: string
  companyName?: string
  jobTitle?: string
}

interface StylePreview {
  name: string
  key: string
  description: string
  preview: string
  color: string
  features: string[]
  recommended?: boolean
}

const STYLE_PREVIEWS: StylePreview[] = [
  {
    name: "Modern",
    key: "modern",
    description: "Clean design with blue accents and contemporary typography",
    preview: "🎨 Blue accents • Inter font • Professional spacing",
    color: "from-blue-500 to-cyan-500",
    features: ["Blue section headers", "Modern typography", "Justified text", "Professional spacing"],
    recommended: true
  },
  {
    name: "Classic",
    key: "classic", 
    description: "Traditional format with serif fonts for formal industries",
    preview: "📜 Times New Roman • Formal layout • Conservative styling",
    color: "from-gray-600 to-gray-800",
    features: ["Serif fonts", "Centered headers", "Traditional layout", "Formal appearance"]
  },
  {
    name: "Minimal",
    key: "minimal",
    description: "Simple, clean design with plenty of white space",
    preview: "✨ Helvetica • Clean lines • Minimal styling • White space",
    color: "from-green-500 to-emerald-500", 
    features: ["Clean typography", "Minimal styling", "Left alignment", "Plenty of space"]
  }
]

export function PDFGenerationDialog({
  open,
  onOpenChange,
  contentType,
  initialContent = "",
  contentId,
  companyName = "",
  jobTitle = ""
}: PDFGenerationDialogProps) {
  const [selectedStyle, setSelectedStyle] = React.useState("modern")
  const [isEditing, setIsEditing] = React.useState(false)
  const [editedContent, setEditedContent] = React.useState(initialContent)
  const [editedCompanyName, setEditedCompanyName] = React.useState(companyName)
  const [editedJobTitle, setEditedJobTitle] = React.useState(jobTitle)
  const [isGenerating, setIsGenerating] = React.useState(false)
  const [downloadingStyle, setDownloadingStyle] = React.useState<string | null>(null)
  const [activeTab, setActiveTab] = React.useState("style")
  
  const { getToken } = useAuth()

  React.useEffect(() => {
    setEditedContent(initialContent)
    setEditedCompanyName(companyName)
    setEditedJobTitle(jobTitle)
  }, [initialContent, companyName, jobTitle])

  const handleDownload = async (style: string) => {
    setIsGenerating(true)
    setDownloadingStyle(style)
    try {
      const token = await getToken()
      if (!token) {
        toast.error("Authentication required")
        return
      }

      // Prepare the request body
      const requestBody: any = {
        content_type: contentType,
        style: style
      }

      if (contentId) {
        requestBody.content_id = contentId
      } else if (editedContent) {
        requestBody.content_text = editedContent
      }

      if (contentType === "cover_letter") {
        requestBody.company_name = editedCompanyName
        requestBody.job_title = editedJobTitle
      }

      const response = await fetch('/api/pdf/generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        // Create a blob from the response
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        
        // Create a temporary download link
        const a = document.createElement('a')
        a.href = url
        
        const filename = contentType === "cover_letter" 
          ? `cover_letter_${editedCompanyName || 'document'}_${style}.pdf`
          : `resume_${style}.pdf`
        
        a.download = filename.replace(/\s+/g, '_')
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        
        toast.success(`${style.charAt(0).toUpperCase() + style.slice(1)} PDF downloaded successfully!`, {
          description: `Saved as ${filename.replace(/\s+/g, '_')}`
        })
      } else {
        const error = await response.json()
        toast.error(error.detail || "Failed to generate PDF")
      }
    } catch (error) {
      console.error('Error generating PDF:', error)
      toast.error("Failed to generate PDF")
    } finally {
      setIsGenerating(false)
      setDownloadingStyle(null)
    }
  }

  const handleDownloadAll = async () => {
    for (const style of STYLE_PREVIEWS) {
      await handleDownload(style.key)
      // Small delay between downloads
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }

  const handlePreview = async (style: string) => {
    try {
      const token = await getToken()
      if (!token) {
        toast.error("Authentication required")
        return
      }

      const params = new URLSearchParams({ style })
      if (contentId) {
        params.append('content_id', contentId)
      }

      const url = `/api/pdf/preview/${contentType}?${params.toString()}`
      window.open(url, '_blank')
    } catch (error) {
      console.error('Error opening preview:', error)
      toast.error("Failed to open preview")
    }
  }

  const handleSaveEdits = () => {
    setIsEditing(false)
    toast.success("Changes saved locally. Download PDF to apply changes.")
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[95vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Generate {contentType === "cover_letter" ? "Cover Letter" : "Resume"} PDF
          </DialogTitle>
          <DialogDescription>
            Choose a style, edit content if needed, and download your professionally formatted PDF
          </DialogDescription>
        </DialogHeader>

        {/* Quick Actions Bar */}
        <div className="flex flex-wrap gap-2 p-4 bg-muted/30 rounded-lg border">
          <Button
            onClick={() => handleDownload(selectedStyle)}
            disabled={isGenerating}
            className="flex items-center gap-2"
          >
            {isGenerating && downloadingStyle === selectedStyle ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Quick Download ({STYLE_PREVIEWS.find(s => s.key === selectedStyle)?.name})
          </Button>
          <Button
            variant="outline"
            onClick={() => handlePreview(selectedStyle)}
            className="flex items-center gap-2"
          >
            <Eye className="h-4 w-4" />
            Preview
          </Button>
          <Button
            variant="outline"
            onClick={handleDownloadAll}
            disabled={isGenerating}
            className="flex items-center gap-2"
          >
            <Zap className="h-4 w-4" />
            Download All Styles
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="style" className="flex items-center gap-2">
              <Palette className="h-4 w-4" />
              Style
            </TabsTrigger>
            <TabsTrigger value="edit" className="flex items-center gap-2">
              <Edit3 className="h-4 w-4" />
              Edit
            </TabsTrigger>
            <TabsTrigger value="download" className="flex items-center gap-2">
              <Download className="h-4 w-4" />
              Download
            </TabsTrigger>
          </TabsList>

          <ScrollArea className="flex-1 mt-4 max-h-[60vh]">
            <TabsContent value="style" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {STYLE_PREVIEWS.map((style) => (
                  <Card 
                    key={style.key}
                    className={`cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] ${
                      selectedStyle === style.key 
                        ? 'ring-2 ring-primary border-primary shadow-lg' 
                        : 'hover:border-primary/50'
                    }`}
                    onClick={() => setSelectedStyle(style.key)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${style.color}`} />
                          {style.name}
                          {style.recommended && (
                            <Star className="h-3 w-3 text-yellow-500 fill-current" />
                          )}
                        </CardTitle>
                        {selectedStyle === style.key && (
                          <CheckCircle className="h-5 w-5 text-primary" />
                        )}
                      </div>
                      <CardDescription className="text-sm">
                        {style.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="text-xs text-muted-foreground font-mono bg-muted p-2 rounded">
                          {style.preview}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {style.features.map((feature, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {feature}
                            </Badge>
                          ))}
                        </div>
                        <div className="flex gap-2 pt-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation()
                              handlePreview(style.key)
                            }}
                            className="flex-1 flex items-center gap-1"
                          >
                            <Eye className="h-3 w-3" />
                            Preview
                          </Button>
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDownload(style.key)
                            }}
                            disabled={isGenerating}
                            className="flex-1 flex items-center gap-1"
                          >
                            {isGenerating && downloadingStyle === style.key ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <Download className="h-3 w-3" />
                            )}
                            Download
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <Separator />
              
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="space-y-1">
                  <h4 className="font-medium">Selected: {STYLE_PREVIEWS.find(s => s.key === selectedStyle)?.name}</h4>
                  <p className="text-sm text-muted-foreground">
                    {STYLE_PREVIEWS.find(s => s.key === selectedStyle)?.description}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handlePreview(selectedStyle)}
                    className="flex items-center gap-2"
                  >
                    <Eye className="h-4 w-4" />
                    Preview
                  </Button>
                  <Button
                    onClick={() => handleDownload(selectedStyle)}
                    disabled={isGenerating}
                    className="flex items-center gap-2"
                  >
                    {isGenerating && downloadingStyle === selectedStyle ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Download className="h-4 w-4" />
                    )}
                    {isGenerating && downloadingStyle === selectedStyle ? "Generating..." : "Download"}
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="edit" className="space-y-4">
              {contentType === "cover_letter" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="company">Company Name</Label>
                    <Input
                      id="company"
                      value={editedCompanyName}
                      onChange={(e) => setEditedCompanyName(e.target.value)}
                      placeholder="e.g., Google"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="jobTitle">Job Title</Label>
                    <Input
                      id="jobTitle"
                      value={editedJobTitle}
                      onChange={(e) => setEditedJobTitle(e.target.value)}
                      placeholder="e.g., Software Engineer"
                    />
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="content">
                  {contentType === "cover_letter" ? "Cover Letter Content" : "Resume Content"}
                </Label>
                <Textarea
                  id="content"
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  placeholder={`Edit your ${contentType === "cover_letter" ? "cover letter" : "resume"} content here...`}
                  rows={12}
                  className="font-mono text-sm"
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditedContent(initialContent)
                    setEditedCompanyName(companyName)
                    setEditedJobTitle(jobTitle)
                  }}
                >
                  Reset
                </Button>
                <Button onClick={handleSaveEdits} className="flex items-center gap-2">
                  <Save className="h-4 w-4" />
                  Save Changes
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="download" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {STYLE_PREVIEWS.map((style) => (
                  <Card key={style.key} className="overflow-hidden hover:shadow-lg transition-all duration-200">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center gap-2 text-sm">
                        <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${style.color}`} />
                        {style.name} Style
                        {style.recommended && (
                          <Badge variant="secondary" className="text-xs">
                            <Star className="h-2 w-2 mr-1 fill-current" />
                            Recommended
                          </Badge>
                        )}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="aspect-[8.5/11] bg-white border rounded-lg p-2 text-xs overflow-hidden relative shadow-inner">
                        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-gray-100 opacity-50" />
                        <div className="relative z-10 space-y-1">
                          <div className={`h-3 ${style.key === 'modern' ? 'bg-blue-500' : style.key === 'classic' ? 'bg-gray-700' : 'bg-green-500'} rounded mb-2`} />
                          <div className="space-y-1">
                            {[...Array(12)].map((_, i) => (
                              <div 
                                key={i} 
                                className={`h-0.5 bg-gray-300 rounded ${
                                  i % 4 === 0 ? 'w-3/4' : 
                                  i % 3 === 0 ? 'w-5/6' : 
                                  i % 2 === 0 ? 'w-full' : 'w-4/5'
                                }`} 
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-xs text-muted-foreground">{style.description}</p>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handlePreview(style.key)}
                            className="flex-1 flex items-center gap-1"
                          >
                            <ExternalLink className="h-3 w-3" />
                            Preview
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleDownload(style.key)}
                            disabled={isGenerating}
                            className="flex-1 flex items-center gap-1"
                          >
                            {isGenerating && downloadingStyle === style.key ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <Download className="h-3 w-3" />
                            )}
                            Download
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <Separator />

              <div className="flex flex-col sm:flex-row gap-4 items-center justify-between p-4 bg-muted/30 rounded-lg">
                <div className="text-center sm:text-left">
                  <h4 className="font-medium">Bulk Download</h4>
                  <p className="text-sm text-muted-foreground">Download all PDF styles at once</p>
                </div>
                <Button
                  onClick={handleDownloadAll}
                  disabled={isGenerating}
                  className="flex items-center gap-2"
                  size="lg"
                >
                  {isGenerating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Zap className="h-4 w-4" />
                  )}
                  Download All Styles
                </Button>
              </div>
            </TabsContent>
          </ScrollArea>
        </Tabs>

        <div className="flex flex-col sm:flex-row justify-between items-center pt-4 border-t gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4" />
            Professional PDF generation with multiple styles
          </div>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
} 