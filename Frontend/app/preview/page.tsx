"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { getApiUrl } from "@/lib/utils";
import {
  SignedIn,
  SignedOut,
  SignInButton,
  useAuth,
  UserButton,
} from "@clerk/nextjs";
import {
  AlertCircle,
  ArrowLeft,
  Download,
  ExternalLink,
  Eye,
  EyeOff,
  FileText,
  Info,
  Palette,
  Layout,
  Briefcase,
  Sparkles,
  Check,
  X,
  Loader2,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import * as React from "react";
import html2canvas from 'html2canvas-pro';
import jsPDF from 'jspdf';
// EDIT: Import the new cover letter templates alongside the resume templates.
import { cn } from "@/lib/utils";
import { ModernCoverLetterTemplate } from "./templates/ModernCoverLetterTemplate";
import { ModernResumeTemplate } from "./templates/ModernResumeTemplate";
import { ProfessionalCoverLetterTemplate } from "./templates/ProfessionalCoverLetterTemplate";
import { ProfessionalResumeTemplate } from "./templates/ProfessionalResumeTemplate";
import { ProfessionalATSTemplate } from "./templates/ProfessionalATSTemplate";
import { ImprovedProfessionalTemplate } from "./templates/ImprovedProfessionalTemplate";
import { PreviewData } from "./types";
import { PreviewLoader } from "@/components/preview-loader";

// NOTE: Helper function remains unchanged.
const getElementCss = (element: HTMLElement): string => {
  const sheets = Array.from(document.styleSheets);
  let css = "";
  for (const sheet of sheets) {
    try {
      if (sheet.cssRules) {
        const rules = Array.from(sheet.cssRules);
        for (const rule of rules) {
          if (
            rule instanceof CSSStyleRule &&
            element.matches(rule.selectorText)
          ) {
            css += rule.cssText;
          } else if (
            rule instanceof CSSStyleRule &&
            element.querySelector(rule.selectorText)
          ) {
            css += rule.cssText;
          }
        }
      }
    } catch (e) {
      console.warn("Could not read stylesheet:", e);
    }
  }
  return css;
};

const PDF_STYLES = [
  {
    key: "modern",
    name: "Modern",
    description: "Clean and minimalist with smart color accents",
    color: "bg-blue-500",
    useTheme: true,
  },
  {
    key: "professional",
    name: "Professional",
    description: "Classic corporate layout for traditional industries",
    color: "bg-gray-600",
    useTheme: true,
  },
  {
    key: "ats",
    name: "Professional ATS",
    description: "ATS-optimized format for applicant tracking systems",
    color: "bg-indigo-600",
    useTheme: true,
  },
];

const CoverLetterTemplate: React.FC<{
  data: PreviewData;
  hasMounted: boolean;
}> = ({ data, hasMounted }) => {
  const { personalInfo, company_name, job_title, content } = data;

  return (
    <div className="p-8 md:p-12 bg-transparent text-gray-800 font-serif text-base leading-relaxed dark:text-gray-200">
      <div className="max-w-4xl mx-auto">
        {/* Sender's Info (Top Right) */}
        <div className="text-right mb-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {personalInfo?.name}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {personalInfo?.location}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            {personalInfo?.email} | {personalInfo?.phone}
          </p>
          {personalInfo?.linkedin && (
            <a
              href={personalInfo.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline dark:text-blue-400"
            >
              LinkedIn Profile
            </a>
          )}
        </div>

        {/* Date */}
        {hasMounted && (
          <p className="mb-8 text-gray-600 dark:text-gray-400">
            {new Date().toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        )}

        {/* Recipient's Info */}
        <div className="mb-8">
          <p className="font-semibold text-gray-900 dark:text-gray-100">
            Hiring Team
          </p>
          <p className="text-gray-700 dark:text-gray-300">{company_name}</p>
        </div>

        {/* Subject Line */}
        <h2 className="text-lg font-semibold mb-6 text-gray-900 dark:text-gray-100">
          RE: {job_title} Position
        </h2>

        {/* Body of the letter */}
        <div className="whitespace-pre-line text-justify text-gray-700 dark:text-gray-300">
          {content}
        </div>
      </div>
    </div>
  );
};

// Updated PrintStyles to use A4 page size and removed borders
const PrintStyles = () => (
  <style jsx global>{`
    @media print {
      @page {
        /* Use A4 size for standard printing */
        size: A4;
        margin: 0;
      }

      * {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }

      body {
        background: white !important;
        margin: 0;
        padding: 0;
      }

      body * {
        visibility: hidden;
      }

      #pdf-preview-content,
      #pdf-preview-content * {
        visibility: visible;
      }

      #pdf-preview-content {
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        margin: 0;
        padding: 0;
        box-shadow: none !important;
        border: none !important;
        background: white !important;
      }

      .resume-light-mode {
        background: white !important;
      }

      /* Page break control - these are still good practice */
      h1,
      h2,
      h3,
      h4,
      h5,
      h6 {
        break-after: avoid;
      }
      img,
      figure,
      pre,
      blockquote,
      table,
      ul,
      ol {
        break-inside: avoid;
      }
      p {
        orphans: 3;
        widows: 3;
      }
    }
  `}</style>
);

// EDIT: Create template maps for BOTH resumes and cover letters.
const resumeTemplates: { [key: string]: React.FC<{ data: PreviewData }> } = {
  modern: ModernResumeTemplate,
  professional: ProfessionalResumeTemplate,
  ats: ProfessionalATSTemplate,
  enhanced: ImprovedProfessionalTemplate,
};

const coverLetterTemplates: {
  [key: string]: React.FC<{ data: PreviewData; hasMounted: boolean }>;
} = {
  modern: ModernCoverLetterTemplate,
  professional: ProfessionalCoverLetterTemplate,
  ats: CoverLetterTemplate, // Using default template for ATS cover letters
};

export default function PreviewPage() {
  const searchParams = useSearchParams();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [previewData, setPreviewData] = React.useState<PreviewData | null>(
    null
  );
  const [loading, setLoading] = React.useState(true);
  const [currentStyle, setCurrentStyle] = React.useState("modern");
  const [showStyleSelector, setShowStyleSelector] = React.useState(false);
  // EDIT: Added state to control the visibility of the new download helper.
  const [showDownloadHelper, setShowDownloadHelper] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [hasMounted, setHasMounted] = React.useState(false);
  const [isClient, setIsClient] = React.useState(false);

  React.useEffect(() => {
    setHasMounted(true);
    setIsClient(true);
  }, []);

  React.useEffect(() => {
    if (!isClient || !isLoaded || !hasMounted) return;

    const loadPreviewData = async () => {
      setLoading(true);
      setError(null);

      try {
        const contentType = searchParams.get("type");
        const style = searchParams.get("style") || "modern";
        setCurrentStyle(style);

        if (contentType === "resume") {
          await loadResumeData(style);
        } else if (contentType === "cover_letter") {
          const contentId = searchParams.get("content_id");
          if (contentId) {
            await loadCoverLetterData(contentId, style);
          } else {
            await loadLatestCoverLetterData(style);
          }
        } else {
          setError("Invalid or missing content type specified in URL.");
        }
      } catch (err) {
        console.error("Failed to load preview data:", err);
        const message =
          err instanceof Error ? err.message : "An unknown error occurred.";
        setError(`Failed to load preview data: ${message}`);
      } finally {
        setLoading(false);
      }
    };

    loadPreviewData();
  }, [searchParams, isLoaded, hasMounted, isClient]);

  const loadResumeData = async (style: string) => {
    if (!isSignedIn) {
      setError("Authentication required. Please sign in to view your resume.");
      return;
    }
    const token = await getToken();
    if (!token) {
      setError("Authentication token not available.");
      return;
    }

    try {
      // Add timestamp to prevent caching
      const timestamp = Date.now();
      const response = await fetch(getApiUrl(`/api/resume?t=${timestamp}`), {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
        },
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch resume: ${response.statusText}`);
      }

      const resumeData = await response.json();
      console.log("Fetched resume data from API:", resumeData);

      const dataForPreview: PreviewData = {
        content_type: "resume",
        style: style,
        content: "",
        company_name: "",
        job_title: resumeData.job_title || resumeData.personalInfo?.professionalTitle || "",
        section_order: resumeData.section_order,
        personalInfo: resumeData.personalInfo,
        work_experience: resumeData.experience,
        education: resumeData.education,
        skills: resumeData.skills,
        projects: resumeData.projects,
        certifications: resumeData.certifications,
        languages: resumeData.languages,
      };

      setPreviewData(dataForPreview);
    } catch (err) {
      console.error("Error loading resume data:", err);
      const message =
        err instanceof Error ? err.message : "An unknown error occurred.";
      setError(`Failed to load resume data: ${message}`);
    }
  };

  const processCoverLetterData = (coverLetterData: any, style: string) => {
    let content = "";
    let company_name = "";
    let job_title = "";
    let personal_info;

    if (coverLetterData?.content) {
      if (typeof coverLetterData.content === "string") {
        try {
          const parsedContent = JSON.parse(coverLetterData.content);
          content = parsedContent.body || "";
          company_name = parsedContent.company_name || "";
          job_title = parsedContent.job_title || "";
          personal_info = parsedContent.personal_info;
        } catch (e) {
          content = coverLetterData.content;
        }
      } else if (typeof coverLetterData.content === "object") {
        const parsedContent = coverLetterData.content;
        content = parsedContent.body || "";
        company_name = parsedContent.company_name || "";
        job_title = parsedContent.job_title || "";
        personal_info = parsedContent.personal_info;
      }
    }

    const coverLetterPreviewData: PreviewData = {
      content_type: "cover_letter",
      style: style,
      content: content,
      company_name: company_name,
      job_title: job_title,
      personalInfo: personal_info
        ? {
            name: personal_info.fullName || "",
            email: personal_info.email || "",
            phone: personal_info.phone || "",
            location: personal_info.address || "",
            linkedin: personal_info.linkedin || "",
            website: personal_info.website || "",
            summary: personal_info.summary || "",
          }
        : undefined,
    };
    setPreviewData(coverLetterPreviewData);
    setCurrentStyle(style);
  };

  const loadLatestCoverLetterData = async (style: string) => {
    try {
      if (!isSignedIn) {
        setError("Authentication required. Please sign in.");
        return;
      }
      const token = await getToken();
      if (!token) {
        setError("Authentication token not available.");
        return;
      }
      // Add timestamp to prevent caching
      const timestamp = Date.now();
      const response = await fetch(
        getApiUrl(`/api/documents/cover-letters/latest?t=${timestamp}`),
        { 
          headers: { 
            Authorization: `Bearer ${token}`,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
          },
          cache: 'no-store',
        }
      );
      if (!response.ok) {
        if (response.status === 404) {
          setError("No cover letter found. Please generate one first.");
          return;
        }
        throw new Error(
          `Failed to fetch latest cover letter: ${response.status} ${response.statusText}`
        );
      }
      const coverLetterData = await response.json();
      processCoverLetterData(coverLetterData, style);
    } catch (err) {
      console.error("Error loading latest cover letter data:", err);
      const message =
        err instanceof Error ? err.message : "An unknown error occurred.";
      setError(`Failed to load latest cover letter: ${message}`);
    }
  };

  const loadCoverLetterData = async (contentId: string, style: string) => {
    try {
      if (!isSignedIn) {
        setError("Authentication required. Please sign in.");
        return;
      }
      const token = await getToken();
      if (!token) {
        setError("Authentication token not available.");
        return;
      }
      // Add timestamp to prevent caching
      const timestamp = Date.now();
      const response = await fetch(
        getApiUrl(`/api/documents/cover-letters/${contentId}?t=${timestamp}`),
        { 
          headers: { 
            Authorization: `Bearer ${token}`,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
          },
          cache: 'no-store',
        }
      );
      if (!response.ok) {
        if (response.status === 404) {
          setError("Cover letter not found or access denied.");
          return;
        }
        throw new Error(
          `Failed to fetch cover letter: ${response.status} ${response.statusText}`
        );
      }
      const coverLetterData = await response.json();
      processCoverLetterData(coverLetterData, style);
    } catch (err) {
      console.error("Error loading cover letter data:", err);
      const message =
        err instanceof Error ? err.message : "An unknown error occurred.";
      setError(`Failed to load cover letter: ${message}`);
    }
  };

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest(".style-selector-container"))
        setShowStyleSelector(false);
    };
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setShowStyleSelector(false);
    };
    if (showStyleSelector) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscapeKey);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
        document.removeEventListener("keydown", handleEscapeKey);
      };
    }
  }, [showStyleSelector]);

  React.useEffect(() => {
    return () => setShowStyleSelector(false);
  }, []);

  const handleGoBack = () => {
    if (document.referrer) window.history.back();
    else window.location.href = "https://jobhackerbot.com";
  };

  // Create a ref for the PDF content
  const targetRef = React.useRef<HTMLDivElement>(null);
  const [isGeneratingPDF, setIsGeneratingPDF] = React.useState(false);

  const handleDownload = async () => {
    if (!targetRef.current) {
      console.error('No element reference found');
      return;
    }
    
    try {
      setIsGeneratingPDF(true);
      
      // Get the inner content div (the actual resume/cover letter)
      const innerContent = targetRef.current.querySelector('.resume-light-mode') || targetRef.current.firstElementChild;
      const elementToCapture = innerContent || targetRef.current;
      
      // Clone the element to modify without affecting the display
      const clonedElement = elementToCapture.cloneNode(true) as HTMLElement;
      
      // Create a temporary container
      const tempContainer = document.createElement('div');
      tempContainer.style.position = 'absolute';
      tempContainer.style.top = '-9999px';
      tempContainer.style.left = '-9999px';
      tempContainer.style.background = 'white';
      tempContainer.style.width = '210mm'; // A4 width
      tempContainer.style.padding = '0';
      tempContainer.style.margin = '0';
      
      // Clean up the cloned element
      clonedElement.style.border = 'none';
      clonedElement.style.boxShadow = 'none';
      clonedElement.style.borderRadius = '0';
      clonedElement.style.background = 'white';
      clonedElement.style.margin = '0';
      clonedElement.style.padding = '20px';
      
      // Remove dark mode classes and ensure white background
      clonedElement.classList.remove('dark', 'dark:bg-black/90', 'dark:border-gray-600/50');
      clonedElement.classList.add('!bg-white');
      
      // Append to document temporarily
      tempContainer.appendChild(clonedElement);
      document.body.appendChild(tempContainer);
      
      // Small delay to ensure rendering
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Use html2canvas-pro with optimized settings
      const canvas = await html2canvas(clonedElement, {
        useCORS: true,
        scale: 3, // High quality
        logging: false,
        backgroundColor: '#ffffff',
        width: clonedElement.scrollWidth,
        height: clonedElement.scrollHeight,
        windowWidth: clonedElement.scrollWidth,
        windowHeight: clonedElement.scrollHeight,
      });
      
      // Remove temporary container
      document.body.removeChild(tempContainer);
      
      // Check if canvas is valid
      if (!canvas || canvas.width === 0 || canvas.height === 0) {
        throw new Error('Failed to capture content - canvas is empty');
      }
      
      // Calculate PDF dimensions for A4 size
      const pdfWidth = 210; // A4 width in mm
      const pdfHeight = 297; // A4 height in mm
      const imgWidth = pdfWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      // Create PDF with A4 size
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });
      
      // Convert canvas to high-quality image
      const imgData = canvas.toDataURL('image/png', 1.0);
      
      // Add image to PDF with intelligent page breaks
      if (imgHeight <= pdfHeight) {
        // Single page - no vertical centering, start from top
        pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
      } else {
        // Multiple pages with proper content height calculation
        const pageMargin = 10; // 10mm margin between page breaks
        
        // First page gets full height, subsequent pages get reduced height
        const firstPageHeight = pdfHeight - pageMargin; // Leave margin at bottom of first page
        const subsequentPageHeight = pdfHeight - (pageMargin * 2); // Margin top and bottom
        
        // Track position in the original image
        let currentSourceY = 0;
        let remainingHeight = imgHeight;
        let pageIndex = 0;
        
        while (remainingHeight > 0) {
          if (pageIndex > 0) {
            pdf.addPage();
          }
          
          // Determine how much content fits on this page
          const availableHeight = pageIndex === 0 ? firstPageHeight : subsequentPageHeight;
          const contentHeight = Math.min(availableHeight, remainingHeight);
          
          // Calculate the pixel coordinates for this slice
          const pixelY = (currentSourceY / imgHeight) * canvas.height;
          const pixelHeight = (contentHeight / imgHeight) * canvas.height;
          
          // Create a canvas for this page's content
          const sliceCanvas = document.createElement('canvas');
          const sliceCtx = sliceCanvas.getContext('2d');
          
          if (sliceCtx) {
            sliceCanvas.width = canvas.width;
            sliceCanvas.height = pixelHeight;
            
            // Draw the slice from the original canvas
            sliceCtx.drawImage(
              canvas,
              0, pixelY, // Source x, y
              canvas.width, pixelHeight, // Source width, height
              0, 0, // Dest x, y
              canvas.width, pixelHeight // Dest width, height
            );
            
            // Convert slice to image
            const sliceData = sliceCanvas.toDataURL('image/png', 1.0);
            
            // Position on page: first page starts at 0, others start with margin
            const yPosition = pageIndex === 0 ? 0 : pageMargin;
            
            // Add to PDF
            pdf.addImage(sliceData, 'PNG', 0, yPosition, imgWidth, contentHeight);
          }
          
          // Update counters
          currentSourceY += contentHeight;
          remainingHeight -= contentHeight;
          pageIndex++;
        }
      }
      
      // Generate filename
      const filename = `${previewData?.content_type || 'document'}_${new Date().toISOString().split('T')[0]}.pdf`;
      
      // Save the PDF
      pdf.save(filename);
      
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert(`Failed to generate PDF: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  if (!isClient) {
    return null;
  }

  if (loading || !isLoaded) {
    const contentType = searchParams.get("type") as "resume" | "cover_letter" | null;
    
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
          <div className="max-w-4xl mx-auto">
            <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
              <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                <div className="p-1.5 sm:p-2 bg-blue-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                  <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-sm sm:text-base md:text-xl font-bold text-foreground truncate">
                    {contentType === "cover_letter" ? "Cover Letter" : contentType === "resume" ? "Resume" : "Document"} Preview
                  </h1>
                  <p className="text-xs text-muted-foreground/80 -mt-0.5 hidden sm:block">
                    Preparing your document...
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <ThemeToggle />
                <SignedIn>
                  <UserButton />
                </SignedIn>
              </div>
            </header>
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <PreviewLoader contentType={contentType} />
        </div>
      </div>
    );
  }

  if (error || !previewData) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background p-6">
        <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
          <div className="max-w-4xl mx-auto">
            <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-sate-150">
              <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                <div className="p-1.5 sm:p-2 bg-red-500 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                  <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-sm sm:text-base md:text-xl font-bold text-foreground truncate">
                    Preview Error
                  </h1>
                  <p className="text-xs text-muted-foreground/80 -mt-0.5 hidden sm:block">
                    An error occurred
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <ThemeToggle />
                <SignedOut>
                  <SignInButton mode="modal">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 px-3 lg:h-9 lg:px-4 rounded-lg lg:rounded-xl bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 text-blue-600 dark:text-blue-400 transition-all duration-200 hover:scale-105"
                    >
                      Sign In
                    </Button>
                  </SignInButton>
                </SignedOut>
                <SignedIn>
                  <UserButton />
                </SignedIn>
              </div>
            </header>
          </div>
        </div>
        <div className="text-center max-w-md mx-auto">
          <div className="w-20 h-20 mx-auto mb-6 p-4 bg-red-500/10 rounded-3xl border border-red-500/20">
            <AlertCircle className="h-full w-full text-red-500" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-3">
            Could not load preview
          </h1>
          <p className="text-muted-foreground mb-6 leading-relaxed">
            {error || "An unknown error occurred."}
          </p>
          <div className="space-y-4">
            <Button
              onClick={handleGoBack}
              variant="outline"
              className="w-full sm:w-auto rounded-xl"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
            {error && error.includes("Authentication") && (
              <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-2xl">
                <p className="text-sm text-muted-foreground mb-3">
                  To use the preview, please:
                </p>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                    <span>Go to the main app and log in</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                    <span>Return to this preview page</span>
                  </div>
                </div>
                <Button
                  onClick={() => {
                    window.location.href = "http://localhost:3000";
                  }}
                  variant="default"
                  size="sm"
                  className="mt-4 w-full sm:w-auto rounded-xl bg-blue-600 hover:bg-blue-700"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Open Main App
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // EDIT: Dynamically select the correct template component based on content type and style.
  const SelectedResumeTemplate =
    resumeTemplates[currentStyle] || resumeTemplates.modern;
  const SelectedCoverLetterTemplate =
    coverLetterTemplates[currentStyle] || coverLetterTemplates.modern;

  return (
    <div className="flex flex-col min-h-screen bg-background print:!bg-white">
      <PrintStyles />
      <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6 print:hidden">
        <div className="max-w-4xl mx-auto">
          <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
            <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
              <div className="p-1.5 sm:p-2 bg-blue-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="hidden lg:inline text-sm sm:text-base md:text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent truncate">
                  {previewData.content_type === "cover_letter"
                    ? "Cover Letter"
                    : "Resume"}{" "}
                  Preview
                </h1>
                <p className="text-xs text-muted-foreground/80 -mt-0.5 hidden sm:block">
                  {previewData.company_name && previewData.job_title
                    ? `${previewData.job_title} at ${previewData.company_name}`
                    : "Document Preview"}
                </p>
              </div>
            </div>

            <div className="md:hidden relative style-selector-container">
              <Button
                onClick={() => setShowStyleSelector(!showStyleSelector)}
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105"
                title="Change Style"
              >
                <Palette className="h-4 w-4" />
              </Button>
              {showStyleSelector && (
                <div className="absolute right-0 left-1/2 top-full mt-4 w-80 bg-background/98 backdrop-blur-2xl border border-border/40 rounded-2xl shadow-2xl z-20 p-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-base font-semibold text-foreground">
                        Choose Template Style
                      </h3>
                      <button
                        type="button"
                        onClick={() => setShowStyleSelector(false)}
                        className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-lg hover:bg-accent/50"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    {PDF_STYLES.map((style) => (
                      <button
                        type="button"
                        key={style.key}
                        onClick={() => {
                          setCurrentStyle(style.key);
                          setShowStyleSelector(false);
                        }}
                        className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all transform hover:scale-[1.02] ${
                          currentStyle === style.key
                            ? "border-primary bg-primary/10 shadow-lg"
                            : "border-border/50 hover:border-primary/40 hover:bg-accent/30"
                        }`}
                      >
                        <div className={`w-12 h-12 rounded-lg flex-shrink-0 ${style.color} flex items-center justify-center shadow-md`}>
                          {style.key === 'modern' && <Layout className="h-6 w-6 text-white" />}
                          {style.key === 'professional' && <Briefcase className="h-6 w-6 text-white" />}
                          {style.key === 'ats' && <FileText className="h-6 w-6 text-white" />}
                        </div>
                        <div className="text-left flex-1">
                          <div className="flex items-center gap-2">
                            <div className="text-sm font-semibold text-foreground">
                              {style.name}
                            </div>
                            {currentStyle === style.key && (
                              <Check className="h-4 w-4 text-primary" />
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                            {style.description}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="hidden md:flex items-center gap-1.5 lg:gap-2 flex-shrink-0">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleGoBack}
                className="h-9 w-9 lg:h-10 lg:w-10 rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105"
                title="Go Back"
              >
                <ArrowLeft className="h-4 w-4 lg:h-5 lg:w-5" />
              </Button>
              <div className="relative style-selector-container">
                <Button
                  onClick={() => setShowStyleSelector(!showStyleSelector)}
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 lg:h-10 lg:w-10 rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105"
                  title="Change Style"
                >
                  <Palette className="h-4 w-4 lg:h-5 lg:w-5" />
                </Button>
                {showStyleSelector && (
                  <div className="absolute right-0 top-full mt-2 w-72 bg-background/98 backdrop-blur-2xl border border-border/40 rounded-2xl shadow-2xl z-20 p-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-semibold text-foreground">
                          Template Style
                        </h3>
                        <button
                          type="button"
                          aria-label="Close style selector"
                          onClick={() => setShowStyleSelector(false)}
                          className="text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded-lg hover:bg-accent/50"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      {PDF_STYLES.map((style) => (
                        <button
                          type="button"
                          key={style.key}
                          onClick={() => {
                            setCurrentStyle(style.key);
                            setShowStyleSelector(false);
                          }}
                          className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${
                            currentStyle === style.key
                              ? "border-primary bg-primary/10"
                              : "border-border/50 hover:border-primary/40 hover:bg-accent/30"
                          }`}
                        >
                          <div className={`w-10 h-10 rounded-lg flex-shrink-0 ${style.color} flex items-center justify-center shadow-sm`}>
                            {style.key === 'modern' && <Layout className="h-5 w-5 text-white" />}
                            {style.key === 'professional' && <Briefcase className="h-5 w-5 text-white" />}
                            {style.key === 'ats' && <FileText className="h-5 w-5 text-white" />}
                          </div>
                          <div className="text-left flex-1">
                            <div className="flex items-center gap-2">
                              <div className="text-sm font-medium text-foreground">
                                {style.name}
                              </div>
                              {currentStyle === style.key && (
                                <Check className="h-3.5 w-3.5 text-primary" />
                              )}
                            </div>
                            <div className="text-xs text-muted-foreground mt-0.5">
                              {style.description}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <Badge variant="outline" className="capitalize rounded-xl">
                {PDF_STYLES.find((s) => s.key === currentStyle)?.name} Style
              </Badge>
              <Button
                onClick={handleDownload}
                disabled={isGeneratingPDF}
                className="h-9 lg:h-10 px-3 lg:px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGeneratingPDF ? (
                  <>
                    <Loader2 className="h-4 w-4 lg:mr-2 text-white animate-spin" />
                    <span className="hidden lg:inline text-white">Generating...</span>
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 lg:mr-2 text-white" />
                    <span className="hidden lg:inline text-white">Download PDF</span>
                  </>
                )}
              </Button>
              <div className="h-6 w-px bg-border/50 mx-1" />
              <ThemeToggle />
              <SignedIn>
                <UserButton />
              </SignedIn>
            </div>

            <div className="flex md:hidden items-center space-x-1.5 sm:space-x-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleGoBack}
                className="h-8 w-8 sm:h-9 sm:w-9 rounded-lg sm:rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105"
              >
                <ArrowLeft className="h-4 w-4 sm:h-5 sm:w-5" />
              </Button>
              <Button
                onClick={handleDownload}
                size="sm"
                disabled={isGeneratingPDF}
                className="h-5 px-3 sm:h-5 sm:px-2 rounded-lg sm:rounded-xl bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGeneratingPDF ? (
                  <Loader2 className="h-4 w-4 text-white animate-spin" />
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-1 text-white" />
                    <span className="text-xs text-white">PDF</span>
                  </>
                )}
              </Button>
              <ThemeToggle />
              <SignedIn>
                <UserButton />
              </SignedIn>
            </div>
          </header>
        </div>
      </div>

      <main className="flex-1 pt-24 sm:pt-28 md:pt-32 print:pt-0">
        <div className="max-w-4xl mx-auto p-4 sm:p-6 print:p-0">
          <div
            ref={targetRef}
            id="pdf-preview-content"
            className={cn(
              "rounded-2xl sm:rounded-3xl overflow-hidden",
              "bg-white/95 text-foreground border border-slate-200/70 shadow-lg shadow-slate-900/8",
              "dark:bg-black/90 dark:border-gray-600/50 dark:shadow-black/15",
              "print:!bg-transparent print:!border-none print:!shadow-none print:rounded-none"
            )}
          >
            <div className="resume-light-mode !bg-white dark:!bg-white print:!bg-white print:!border-none [&_*]:!text-gray-900 dark:[&_*]:!text-gray-900 [&_h1]:!text-gray-900 dark:[&_h1]:!text-gray-900 [&_h2]:!text-gray-600 dark:[&_h2]:!text-gray-600 [&_h3]:!text-gray-800 dark:[&_h3]:!text-gray-800 [&_h4]:!text-gray-800 dark:[&_h4]:!text-gray-800 [&_h5]:!text-gray-700 dark:[&_h5]:!text-gray-700 [&_h6]:!text-gray-700 dark:[&_h6]:!text-gray-700 [&_p]:!text-gray-700 dark:[&_p]:!text-gray-700 [&_span]:!text-gray-700 dark:[&_span]:!text-gray-700 [&_li]:!text-gray-600 dark:[&_li]:!text-gray-600 [&_a]:!text-blue-500 dark:[&_a]:!text-blue-500 hover:[&_a]:!text-blue-600 dark:hover:[&_a]:!text-blue-600 [&_hr]:!border-gray-300 dark:[&_hr]:!border-gray-300 [&_.border-gray-300]:!border-gray-300 dark:[&_.border-gray-300]:!border-gray-300 [&_.border-gray-600]:!border-gray-300 dark:[&_.border-gray-600]:!border-gray-300 [&_.border-gray-700]:!border-gray-300 dark:[&_.border-gray-700]:!border-gray-300 [&_.bg-gray-800]:!bg-gray-100 dark:[&_.bg-gray-800]:!bg-gray-100 [&_.bg-gray-100]:!bg-gray-100 dark:[&_.bg-gray-100]:!bg-gray-100 [&_.text-gray-400]:!text-gray-500 dark:[&_.text-gray-400]:!text-gray-500 [&_.text-gray-500]:!text-gray-500 dark:[&_.text-gray-500]:!text-gray-500 [&_.text-gray-600]:!text-gray-600 dark:[&_.text-gray-600]:!text-gray-600 [&_.text-gray-300]:!text-gray-700 dark:[&_.text-gray-300]:!text-gray-700 [&_.text-gray-100]:!text-gray-900 dark:[&_.text-gray-100]:!text-gray-900 [&_.text-gray-200]:!text-gray-800 dark:[&_.text-gray-200]:!text-gray-800 [&_.text-white]:!text-gray-900 dark:[&_.text-white]:!text-gray-900 [&_.text-blue-400]:!text-blue-500 dark:[&_.text-blue-400]:!text-blue-500 [&_.text-blue-600]:!text-blue-500 dark:[&_.text-blue-600]:!text-blue-500 [&_.text-blue-700]:!text-blue-600 dark:[&_.text-blue-700]:!text-blue-600 [&_.bg-blue-600]:!bg-blue-100 dark:[&_.bg-blue-600]:!bg-blue-100 [&_.bg-blue-700]:!bg-blue-100 dark:[&_.bg-blue-700]:!bg-blue-100">
              {previewData.content_type === "cover_letter" ? (
                <SelectedCoverLetterTemplate
                  data={previewData}
                  hasMounted={hasMounted}
                />
              ) : previewData.content_type === "resume" ? (
                <SelectedResumeTemplate data={previewData} />
              ) : (
                <div className="p-8">
                  <p>Unsupported document type.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* EDIT: Removed the 'w-full' class from the floating container to fix the centering and layout. */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex justify-center items-center gap-3 print:hidden">
        {showDownloadHelper && (
          <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-3 px-4 py-3 rounded-2xl bg-background/60 backdrop-blur-xl backdrop-saturate-150 border border-white/8 shadow-lg text-sm text-gray-700 dark:text-gray-300">
            <div className="flex items-center gap-1.5">
              <Info className="h-4 w-4 text-blue-500" />
              <span className="font-bold text-primary">Print Tip:</span>
            </div>
            <div className="flex items-center gap-1.5">
              <strong className="font-semibold">Headers & Footers:</strong>
              <span className="text-red-500 font-medium">Off</span>
            </div>
            <span className="text-gray-400 dark:text-gray-500 hidden sm:inline">
              •
            </span>
            <div className="flex items-center gap-1.5">
              <strong className="font-semibold">Margins:</strong>
              {currentStyle === "professional" ? (
                <span className="text-green-600 font-medium">None</span>
              ) : (
                <span className="text-green-600 font-medium">Default</span>
              )}
            </div>
          </div>
        )}
        <button
          type="button"
          onClick={() => setShowDownloadHelper(!showDownloadHelper)}
          className="flex items-center justify-center p-3 rounded-2xl text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 bg-background/60 backdrop-blur-xl backdrop-saturate-150 border border-white/8 shadow-lg transition-all"
          title={showDownloadHelper ? "Hide help" : "Show help"}
        >
          {showDownloadHelper ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}
