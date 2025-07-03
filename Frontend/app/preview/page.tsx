"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
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
  FileText,
  Palette,
  Sparkles,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import * as React from "react";

// App-themed style options using CSS custom properties
const PDF_STYLES = [
  {
    key: "modern",
    name: "Modern",
    description: "Clean design with primary accents",
    useTheme: true,
  },
  {
    key: "professional",
    name: "Professional",
    description: "Traditional business layout",
    useTheme: true,
  },
  {
    key: "creative",
    name: "Creative",
    description: "Modern layout with accent colors",
    useTheme: true,
  },
];

interface PreviewData {
  content: string;
  style: string;
  company_name: string;
  job_title: string;
  content_type: "cover_letter" | "resume";
  personal_info?: {
    fullName: string;
    email: string;
    phone: string;
    address: string;
    linkedin: string;
    website: string;
  };
  work_experience?: Array<{
    title: string;
    company: string;
    startYear: string;
    endYear: string;
    description: string;
  }>;
  education?: Array<{
    degree: string;
    school: string;
    year: string;
    description: string;
  }>;
  skills?: string;
  additional_sections?: string;
}

export default function PreviewPage() {
  const searchParams = useSearchParams();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [previewData, setPreviewData] = React.useState<PreviewData | null>(
    null
  );
  const [loading, setLoading] = React.useState(true);
  const [currentStyle, setCurrentStyle] = React.useState("modern");
  const [showStyleSelector, setShowStyleSelector] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const loadPreviewData = async () => {
      setLoading(true);
      setError(null);

      try {
        // First try to load from sessionStorage (existing behavior)
        const storedData = sessionStorage.getItem("pdf_preview_data");
        if (storedData) {
          const data = JSON.parse(storedData);
          setPreviewData(data);
          setCurrentStyle(data.style || "modern");
          setLoading(false);
          return;
        }

        // If no sessionStorage data, try to load from URL parameters
        const contentType = searchParams.get("type");
        const style = searchParams.get("style") || "modern";
        const contentId = searchParams.get("content_id");

        if (contentType) {
          // Fetch data from backend based on URL parameters
          if (contentType === "resume") {
            await loadResumeData(style);
          } else if (contentType === "cover_letter" && contentId) {
            await loadCoverLetterData(contentId, style);
          } else {
            setError("Missing required parameters for cover letter preview");
          }
        } else {
          setError("No preview data available");
        }
      } catch (error) {
        console.error("Failed to load preview data:", error);
        setError("Failed to load preview data");
      } finally {
        setLoading(false);
      }
    };

    // Wait for Clerk to load before attempting authentication
    if (isLoaded) {
      loadPreviewData();
    }
  }, [searchParams, isLoaded]);

  const loadResumeData = async (style: string) => {
    try {
      console.log("Loading resume data with style:", style);

      // Check if user is signed in
      if (!isSignedIn) {
        setError(
          "Authentication required. Please log in to view your resume preview."
        );
        return;
      }

      // Get the authentication token from Clerk
      const token = await getToken();
      if (!token) {
        setError(
          "Authentication token not available. Please log in to view your resume preview."
        );
        return;
      }

      console.log("Using authentication token for API calls");

      // Fetch user data and resume data from backend with proper authentication
      const [userResponse, resumeResponse] = await Promise.all([
        fetch("http://localhost:8000/api/me", {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }),
        fetch("http://localhost:8000/api/resume", {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }),
      ]);

      console.log("User response status:", userResponse.status);
      console.log("Resume response status:", resumeResponse.status);

      // Handle authentication errors properly
      if (userResponse.status === 401 || userResponse.status === 403) {
        setError(
          "Authentication required. Please log in to view your resume preview."
        );
        return;
      }

      if (!userResponse.ok) {
        throw new Error(
          `Failed to fetch user data: ${userResponse.status} ${userResponse.statusText}`
        );
      }

      // Handle resume data - create basic structure if not found
      let resumeData;
      if (!resumeResponse.ok) {
        if (resumeResponse.status === 404) {
          console.log("No resume data found, creating basic structure");
          resumeData = {
            personalInfo: {},
            experience: [],
            education: [],
            skills: [],
            projects: [],
            certifications: [],
          };
        } else if (
          resumeResponse.status === 401 ||
          resumeResponse.status === 403
        ) {
          setError(
            "Authentication required. Please log in to view your resume preview."
          );
          return;
        } else {
          throw new Error(
            `Failed to fetch resume data: ${resumeResponse.status} ${resumeResponse.statusText}`
          );
        }
      } else {
        resumeData = await resumeResponse.json();
      }

      const userData = await userResponse.json();
      console.log("User data loaded:", userData.name || userData.first_name);
      console.log("Resume data loaded:", !!resumeData.personalInfo);

      createResumePreviewData(userData, resumeData, style);
    } catch (error) {
      console.error("Error loading resume data:", error);
      setError(
        `Failed to load resume data: ${
          error instanceof Error ? error.message : "Unknown error"
        }. Please ensure you are logged in and the backend server is running.`
      );
    }
  };

  const createResumePreviewData = (
    userData: any,
    resumeData: any,
    style: string
  ) => {
    // Create preview data structure for resume
    const resumePreviewData: PreviewData = {
      content_type: "resume",
      style: style,
      content: generateResumeContent(userData, resumeData),
      company_name: "",
      job_title: "",
      personal_info: {
        fullName:
          resumeData.personalInfo?.name ||
          userData.name ||
          `${userData.first_name || ""} ${userData.last_name || ""}`.trim() ||
          "User",
        email: resumeData.personalInfo?.email || userData.email || "",
        phone: resumeData.personalInfo?.phone || userData.phone || "",
        address: resumeData.personalInfo?.location || userData.address || "",
        linkedin: resumeData.personalInfo?.linkedin || userData.linkedin || "",
        website: "",
      },
    };

    setPreviewData(resumePreviewData);
    setCurrentStyle(style);
  };

  const loadCoverLetterData = async (contentId: string, style: string) => {
    try {
      console.log(
        "Loading cover letter data with ID:",
        contentId,
        "style:",
        style
      );

      // Check if user is signed in
      if (!isSignedIn) {
        setError(
          "Authentication required. Please log in to view your cover letter preview."
        );
        return;
      }

      // Get the authentication token from Clerk
      const token = await getToken();
      if (!token) {
        setError(
          "Authentication token not available. Please log in to view your cover letter preview."
        );
        return;
      }

      console.log("Using authentication token for cover letter API call");

      // Fetch cover letter data from backend
      const response = await fetch(
        `http://localhost:8000/api/pdf/cover-letter/${contentId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      console.log("Cover letter response status:", response.status);

      // Handle authentication errors properly
      if (response.status === 401 || response.status === 403) {
        setError(
          "Authentication required. Please log in to view your cover letter preview."
        );
        return;
      }

      if (!response.ok) {
        if (response.status === 404) {
          setError(
            "Cover letter not found. It may have been deleted or you don't have access to it."
          );
          return;
        }
        throw new Error(
          `Failed to fetch cover letter: ${response.status} ${response.statusText}`
        );
      }

      const coverLetterData = await response.json();
      console.log("Cover letter data loaded:", !!coverLetterData.content);

      // Extract company and job info from the content if available
      const content = coverLetterData.content || "";
      let companyName = "";
      let jobTitle = "";

      // Try to extract company and job title from content
      const lines = content.split("\n");
      for (const line of lines) {
        if (line.toLowerCase().includes("dear") && line.includes(" hiring")) {
          // Extract company name from "Dear [Company] Hiring Team"
          const match = line.match(/dear\s+(.+?)\s+hiring/i);
          if (match) {
            companyName = match[1].trim();
          }
        }
        if (
          line.toLowerCase().includes("position at") ||
          line.toLowerCase().includes("role at")
        ) {
          // Extract job title and company from "the [Title] position at [Company]"
          const positionMatch = line.match(
            /the\s+(.+?)\s+(?:position|role)\s+at\s+(.+?)[\.,]/i
          );
          if (positionMatch) {
            jobTitle = positionMatch[1].trim();
            if (!companyName) {
              companyName = positionMatch[2].trim();
            }
          }
        }
      }

      const coverLetterPreviewData: PreviewData = {
        content_type: "cover_letter",
        style: style,
        content: content,
        company_name: companyName,
        job_title: jobTitle,
      };

      setPreviewData(coverLetterPreviewData);
      setCurrentStyle(style);
    } catch (error) {
      console.error("Error loading cover letter data:", error);
      setError(
        `Failed to load cover letter: ${
          error instanceof Error ? error.message : "Unknown error"
        }. Please ensure you are logged in and the backend server is running.`
      );
    }
  };

  const generateResumeContent = (userData: any, resumeData: any) => {
    // Generate resume content from user and resume data
    let content = "";

    // Professional Summary
    if (resumeData.personalInfo?.summary) {
      content += `**Professional Summary**\n\n${resumeData.personalInfo.summary}\n\n---\n\n`;
    } else if (userData.profile_headline) {
      content += `**Professional Summary**\n\n${userData.profile_headline}\n\n---\n\n`;
    }

    // Skills
    if (resumeData.skills && resumeData.skills.length > 0) {
      content += `**Skills**\n\n${resumeData.skills.join(", ")}\n\n---\n\n`;
    } else if (userData.skills) {
      content += `**Skills**\n\n${userData.skills}\n\n---\n\n`;
    }

    // Experience
    if (resumeData.experience && resumeData.experience.length > 0) {
      content += `**Professional Experience**\n\n`;
      resumeData.experience.forEach((exp: any) => {
        content += `**${exp.jobTitle}** at **${exp.company}**\n`;
        if (exp.dates) content += `*${exp.dates}*\n`;
        if (exp.description) content += `${exp.description}\n\n`;
      });
      content += `---\n\n`;
    } else {
      content += `**Professional Experience**\n\nAdd your work experience in the resume editor to see it here.\n\n---\n\n`;
    }

    // Education
    if (resumeData.education && resumeData.education.length > 0) {
      content += `**Education**\n\n`;
      resumeData.education.forEach((edu: any) => {
        content += `**${edu.degree}** from **${edu.institution}**\n`;
        if (edu.dates) content += `*${edu.dates}*\n\n`;
      });
    } else {
      content += `**Education**\n\nAdd your education details in the resume editor to see them here.\n\n`;
    }

    // Projects
    if (resumeData.projects && resumeData.projects.length > 0) {
      content += `\n---\n\n**Projects**\n\n`;
      resumeData.projects.forEach((project: any) => {
        content += `**${project.name || "Project"}**\n`;
        if (project.description) content += `${project.description}\n`;
        if (project.technologies)
          content += `*Technologies: ${project.technologies}*\n\n`;
      });
    }

    // Certifications
    if (resumeData.certifications && resumeData.certifications.length > 0) {
      content += `\n---\n\n**Certifications**\n\n`;
      resumeData.certifications.forEach((cert: any) => {
        if (typeof cert === "string") {
          content += `• ${cert}\n`;
        } else if (cert.name) {
          content += `• ${cert.name}`;
          if (cert.date) content += ` (${cert.date})`;
          content += `\n`;
        }
      });
    }

    return (
      content.trim() ||
      "No resume content available. Please add your information in the resume editor."
    );
  };

  // Close style selector when clicking outside or pressing escape
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest(".style-selector-container")) {
        setShowStyleSelector(false);
      }
    };

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setShowStyleSelector(false);
      }
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

  // Cleanup effect to ensure no lingering event listeners
  React.useEffect(() => {
    return () => {
      // Clean up any remaining event listeners when component unmounts
      setShowStyleSelector(false);
    };
  }, []);

  // Simple markdown to HTML conversion with theme-aware styling
  const formatContent = (content: string) => {
    if (!content) return "";

    return (
      content
        // Bold text
        .replace(
          /\*\*(.*?)\*\*/g,
          '<strong class="font-semibold text-foreground">$1</strong>'
        )
        // Italic text
        .replace(
          /\*(.*?)\*/g,
          '<em class="italic text-muted-foreground">$1</em>'
        )
        // Bullet points
        .replace(
          /^• (.*$)/gim,
          '<li class="ml-6 mb-2 list-disc text-foreground">$1</li>'
        )
        // Section dividers
        .replace(/^---$/gm, '<hr class="my-6 border-border">')
        // Paragraphs (double line breaks)
        .replace(
          /\n\n/g,
          '</p><p class="mb-4 leading-relaxed text-foreground">'
        )
        // Single line breaks
        .replace(/\n/g, "<br>")
        // Wrap consecutive list items in ul tags
        .replace(
          /(<li.*?<\/li>(\s*<li.*?<\/li>)*)/g,
          '<ul class="mb-4 space-y-1">$1</ul>'
        )
    );
  };

  const handleGoBack = () => {
    // Use proper navigation instead of window.close() to avoid popup blockers
    if (document.referrer) {
      // If we came from another page, go back
      window.history.back();
    } else {
      // If opened directly, navigate to main app
      window.location.href = "http://localhost:3000";
    }
  };

  const handleDownload = () => {
    // Simple download trigger without popup behavior
    if (previewData) {
      // Create a custom event that the parent page can listen for
      const downloadEvent = new CustomEvent("requestPdfDownload", {
        detail: previewData,
      });

      // Dispatch to current window (in case this is in an iframe)
      window.dispatchEvent(downloadEvent);

      // Also try sessionStorage for cross-tab communication
      try {
        sessionStorage.setItem(
          "pdf_download_request",
          JSON.stringify(previewData)
        );
        // Show user feedback
        alert(
          "Download request saved. Please return to the main app to complete the download."
        );
      } catch (error) {
        console.error("Failed to save download request:", error);
        alert("Please return to the main app to download the PDF.");
      }
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-background">
        {/* Modern App Header */}
        <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
          <div className="max-w-4xl mx-auto">
            <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
              <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                <div className="p-1.5 sm:p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                  <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-sm sm:text-base md:text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent truncate">
                    Resume Preview
                  </h1>
                  <p className="text-xs text-muted-foreground/80 -mt-0.5 hidden sm:block">
                    Loading...
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

        {/* Loading Content */}
        <main className="flex-1 overflow-hidden pt-14 sm:pt-16 md:pt-20">
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground text-lg">
                Loading preview...
              </p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !previewData) {
    return (
      <div className="flex flex-col h-screen bg-background">
        {/* Modern App Header */}
        <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
          <div className="max-w-4xl mx-auto">
            <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
              <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                <div className="p-1.5 sm:p-2 bg-gradient-to-br from-red-500 to-pink-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                  <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-sm sm:text-base md:text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent truncate">
                    Preview Error
                  </h1>
                  <p className="text-xs text-muted-foreground/80 -mt-0.5 hidden sm:block">
                    Authentication Required
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
                      className="h-8 px-3 lg:h-9 lg:px-4 rounded-lg lg:rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-600/10 hover:from-blue-500/20 hover:to-purple-600/20 border border-blue-500/20 text-blue-600 dark:text-blue-400 transition-all duration-200 hover:scale-105"
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

        {/* Error Content */}
        <main className="flex-1 overflow-hidden pt-14 sm:pt-16 md:pt-20">
          <div className="flex items-center justify-center h-full p-6">
            <div className="text-center max-w-md mx-auto">
              <div className="w-20 h-20 mx-auto mb-6 p-4 bg-gradient-to-br from-red-500/10 to-pink-600/10 rounded-3xl border border-red-500/20">
                <AlertCircle className="h-full w-full text-red-500" />
              </div>

              <h1 className="text-2xl font-bold text-foreground mb-3">
                Authentication Required
              </h1>

              <p className="text-muted-foreground mb-6 leading-relaxed">
                {error || "Please log in to view your resume preview."}
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
                        // Use window.location.href instead of window.open to avoid popup blockers
                        window.location.href = "http://localhost:3000";
                      }}
                      variant="default"
                      size="sm"
                      className="mt-4 w-full sm:w-auto rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open Main App
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const formattedContent = formatContent(previewData.content);

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Modern App Header */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
          <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
            {/* Logo and Title */}
            <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
              <div className="p-1.5 sm:p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="text-sm sm:text-base md:text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent truncate">
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

            {/* Desktop Actions */}
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

              {/* Style Selector */}
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
                  <div className="absolute right-0 top-full mt-2 w-64 bg-background/95 backdrop-blur-xl border border-border/50 rounded-2xl shadow-2xl z-20 p-3">
                    <div className="space-y-2">
                      <h3 className="text-sm font-semibold text-foreground mb-3">
                        Choose Style
                      </h3>
                      {PDF_STYLES.map((style) => (
                        <button
                          key={style.key}
                          onClick={() => {
                            setCurrentStyle(style.key);
                            setShowStyleSelector(false);
                          }}
                          className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-all ${
                            currentStyle === style.key
                              ? "border-primary bg-primary/5"
                              : "border-border hover:border-primary/50 hover:bg-accent/50"
                          }`}
                        >
                          <div className="w-4 h-4 rounded-full flex-shrink-0 bg-gradient-to-br from-blue-500 to-purple-600" />
                          <div className="text-left">
                            <div className="text-sm font-medium text-foreground">
                              {style.name}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {style.description}
                            </div>
                          </div>
                          {currentStyle === style.key && (
                            <div className="ml-auto w-2 h-2 bg-primary rounded-full" />
                          )}
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
                className="h-9 lg:h-10 px-3 lg:px-4 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 transition-all duration-200 hover:scale-105"
              >
                <Download className="h-4 w-4 lg:mr-2" />
                <span className="hidden lg:inline">Download PDF</span>
              </Button>

              <div className="h-6 w-px bg-border/50 mx-1" />
              <ThemeToggle />
              <SignedIn>
                <UserButton />
              </SignedIn>
            </div>

            {/* Mobile Actions */}
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
                className="h-8 px-3 sm:h-9 sm:px-4 rounded-lg sm:rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
              >
                <Download className="h-4 w-4 mr-1" />
                <span className="text-xs">PDF</span>
              </Button>
              <ThemeToggle />
              <SignedIn>
                <UserButton />
              </SignedIn>
            </div>
          </header>
        </div>
      </div>

      {/* Content */}
      <main className="flex-1 overflow-hidden pt-14 sm:pt-16 md:pt-20">
        <div className="max-w-4xl mx-auto p-4 sm:p-6 h-full overflow-y-auto">
          <div className="bg-background/60 backdrop-blur-xl border border-white/8 rounded-2xl sm:rounded-3xl shadow-2xl overflow-hidden">
            {/* Document Header */}
            <div className="text-center py-8 px-6 border-b border-border/30 bg-gradient-to-r from-blue-500/5 to-purple-600/5">
              {previewData.content_type === "cover_letter" ? (
                <div>
                  <h1 className="text-3xl font-bold mb-3 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    Cover Letter
                  </h1>
                  {(previewData.job_title || previewData.company_name) && (
                    <p className="text-lg text-muted-foreground mb-2">
                      {previewData.job_title}{" "}
                      {previewData.job_title &&
                        previewData.company_name &&
                        "at"}{" "}
                      {previewData.company_name}
                    </p>
                  )}
                  {previewData.personal_info?.fullName && (
                    <p className="text-base text-foreground font-medium">
                      {previewData.personal_info.fullName}
                    </p>
                  )}
                </div>
              ) : (
                <div>
                  <h1 className="text-3xl font-bold mb-3 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    {previewData.personal_info?.fullName ||
                      "Professional Resume"}
                  </h1>
                  {previewData.personal_info?.email && (
                    <p className="text-base text-muted-foreground">
                      {previewData.personal_info.email}
                    </p>
                  )}
                  {previewData.personal_info?.phone && (
                    <p className="text-base text-muted-foreground">
                      {previewData.personal_info.phone}
                    </p>
                  )}
                </div>
              )}
              <p className="text-sm text-muted-foreground/70 mt-4">
                Generated on {new Date().toLocaleDateString()}
              </p>
            </div>

            {/* Document Content */}
            <div className="p-8">
              <div className="border-l-4 border-gradient-to-b from-blue-500 to-purple-600 pl-6 prose prose-lg max-w-none">
                <div
                  className="text-base leading-relaxed text-foreground"
                  dangerouslySetInnerHTML={{
                    __html: `<p class="mb-4 leading-relaxed">${formattedContent}</p>`,
                  }}
                />
              </div>

              {/* Footer */}
              <div className="mt-12 pt-6 border-t border-border/30 text-center">
                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground/70">
                  <Sparkles className="h-4 w-4" />
                  <span>Generated by Job Hacker Bot</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
