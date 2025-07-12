"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { cn } from "@/lib/utils";
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
  Loader2,
  Palette,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

// NOTE: No changes made to styling definitions.
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

const ResumeTemplate: React.FC<{ data: PreviewData }> = ({ data }) => {
  const {
    personal_info,
    work_experience,
    education,
    skills,
    additional_sections,
  } = data;

  return (
    // FIX 2: Made the template background transparent to let the new theme show through.
    <div className="p-8 md:p-12 bg-transparent font-serif text-gray-800 dark:text-gray-200">
      <header className="text-center mb-10 border-b pb-6 border-gray-200 dark:border-gray-700">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          {personal_info?.fullName}
        </h1>
        <div className="flex justify-center flex-wrap gap-x-6 gap-y-2 mt-4 text-sm text-gray-500 dark:text-gray-400">
          <span>{personal_info?.email}</span>
          <span>{personal_info?.phone}</span>
          <span>{personal_info?.address}</span>
          {personal_info?.linkedin && (
            <a
              href={personal_info.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline dark:text-blue-400"
            >
              LinkedIn
            </a>
          )}
        </div>
      </header>

      <main>
        {work_experience && work_experience.length > 0 && (
          <section className="mb-8">
            <h2 className="text-xl md:text-2xl font-semibold border-b-2 border-gray-800 dark:border-gray-600 pb-2 mb-4">
              Professional Experience
            </h2>
            {work_experience?.map((job, index) => (
              <div key={index} className="mb-6">
                <h3 className="text-lg md:text-xl font-bold text-gray-900 dark:text-gray-100">
                  {job.title}
                </h3>
                <div className="flex justify-between items-baseline">
                  <p className="font-medium text-gray-700 dark:text-gray-300">
                    {job.company}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {job.startYear} - {job.endYear}
                  </p>
                </div>
                <p className="mt-2 text-gray-600 dark:text-gray-300 whitespace-pre-line">
                  {job.description}
                </p>
              </div>
            ))}
          </section>
        )}

        {education && education.length > 0 && (
          <section className="mb-8">
            <h2 className="text-xl md:text-2xl font-semibold border-b-2 border-gray-800 dark:border-gray-600 pb-2 mb-4">
              Education
            </h2>
            {education?.map((edu, index) => (
              <div key={index} className="mb-4">
                <h3 className="text-lg md:text-xl font-bold">{edu.degree}</h3>
                <p className="font-medium text-gray-700 dark:text-gray-300">
                  {edu.school}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {edu.year}
                </p>
              </div>
            ))}
          </section>
        )}

        {skills && (
          <section>
            <h2 className="text-xl md:text-2xl font-semibold border-b-2 border-gray-800 dark:border-gray-600 pb-2 mb-4">
              Skills
            </h2>
            <p className="text-gray-600 dark:text-gray-300">{skills}</p>
          </section>
        )}

        {additional_sections && (
          <section className="mt-8">
            <div
              className="prose prose-lg max-w-none dark:prose-invert"
              dangerouslySetInnerHTML={{ __html: additional_sections }}
            />
          </section>
        )}
      </main>
    </div>
  );
};

const CoverLetterTemplate: React.FC<{
  data: PreviewData;
  hasMounted: boolean;
}> = ({ data, hasMounted }) => {
  const { personal_info, company_name, job_title, content } = data;

  return (
    // FIX 2: Made the template background transparent to let the new theme show through.
    <div className="p-8 md:p-12 bg-transparent text-gray-800 font-serif text-base leading-relaxed dark:text-gray-200">
      <div className="max-w-4xl mx-auto">
        {/* Sender's Info (Top Right) */}
        <div className="text-right mb-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {personal_info?.fullName}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {personal_info?.address}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            {personal_info?.email} | {personal_info?.phone}
          </p>
          {personal_info?.linkedin && (
            <a
              href={personal_info.linkedin}
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

export default function PreviewPage() {
  const searchParams = useSearchParams();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [previewData, setPreviewData] = React.useState<PreviewData | null>(
    null
  );
  const [loading, setLoading] = React.useState(true);
  const [isDownloading, setIsDownloading] = React.useState(false);
  const [currentStyle, setCurrentStyle] = React.useState("modern");
  const [showStyleSelector, setShowStyleSelector] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [hasMounted, setHasMounted] = React.useState(false);

  React.useEffect(() => {
    setHasMounted(true);
  }, []);

  React.useEffect(() => {
    const loadPreviewData = async () => {
      setLoading(true);
      setError(null);

      try {
        const storedData = sessionStorage.getItem("pdf_preview_data");
        if (storedData) {
          const data = JSON.parse(storedData);
          setPreviewData(data);
          setCurrentStyle(data.style || "modern");
          setLoading(false);
          return;
        }

        const contentType = searchParams.get("type");
        const style = searchParams.get("style") || "modern";
        const contentId = searchParams.get("content_id");

        if (contentType) {
          if (contentType === "resume") {
            await loadResumeData(style);
          } else if (contentType === "cover_letter") {
            if (contentId) {
              await loadCoverLetterData(contentId, style);
            } else {
              await loadLatestCoverLetterData(style);
            }
          } else {
            setError("Invalid content type specified.");
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

    if (isLoaded && hasMounted) {
      loadPreviewData();
    }
  }, [searchParams, isLoaded, hasMounted]);

  const loadResumeData = async (style: string) => {
    try {
      if (!isSignedIn) {
        setError(
          "Authentication required. Please log in to view your resume preview."
        );
        return;
      }
      const token = await getToken();
      if (!token) {
        setError(
          "Authentication token not available. Please log in to view your resume preview."
        );
        return;
      }

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

      if (userResponse.status === 401 || userResponse.status === 403) {
        setError(
          "Authentication required. Please log in to view your resume preview."
        );
        return;
      }
      if (!userResponse.ok)
        throw new Error(
          `Failed to fetch user data: ${userResponse.status} ${userResponse.statusText}`
        );

      let resumeData;
      if (!resumeResponse.ok) {
        if (resumeResponse.status === 404) {
          resumeData = {
            personalInfo: {},
            experience: [],
            education: [],
            skills: [],
            projects: [],
            certifications: [],
          };
        } else {
          throw new Error(
            `Failed to fetch resume data: ${resumeResponse.status} ${resumeResponse.statusText}`
          );
        }
      } else {
        resumeData = await resumeResponse.json();
      }

      const userData = await userResponse.json();
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
          // If parsing fails, assume the content is plain text
          content = coverLetterData.content;
        }
      } else if (typeof coverLetterData.content === "object") {
        // If it's already an object
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
      personal_info: personal_info
        ? {
            fullName: personal_info.name || "",
            email: personal_info.email || "",
            phone: personal_info.phone || "",
            address: personal_info.location || "",
            linkedin: personal_info.linkedin || "",
            website: personal_info.website || "",
          }
        : undefined,
    };
    setPreviewData(coverLetterPreviewData);
    setCurrentStyle(style);
  };

  const loadLatestCoverLetterData = async (style: string) => {
    try {
      if (!isSignedIn) {
        setError(
          "Authentication required. Please log in to view your cover letter preview."
        );
        return;
      }
      const token = await getToken();
      if (!token) {
        setError(
          "Authentication token not available. Please log in to view your cover letter preview."
        );
        return;
      }
      const response = await fetch(
        "http://localhost:8000/api/documents/cover-letters/latest",
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      if (response.status === 401 || response.status === 403) {
        setError(
          "Authentication required. Please log in to view your cover letter preview."
        );
        return;
      }
      if (!response.ok) {
        if (response.status === 404) {
          setError(
            "No cover letter found. Please generate one first to see a preview."
          );
          return;
        }
        throw new Error(
          `Failed to fetch latest cover letter: ${response.status} ${response.statusText}`
        );
      }
      const coverLetterData = await response.json();
      processCoverLetterData(coverLetterData, style);
    } catch (error) {
      console.error("Error loading latest cover letter data:", error);
      setError(
        `Failed to load latest cover letter: ${
          error instanceof Error ? error.message : "Unknown error"
        }. Please ensure you are logged in and the backend server is running.`
      );
    }
  };

  const loadCoverLetterData = async (contentId: string, style: string) => {
    try {
      if (!isSignedIn) {
        setError(
          "Authentication required. Please log in to view your cover letter preview."
        );
        return;
      }
      const token = await getToken();
      if (!token) {
        setError(
          "Authentication token not available. Please log in to view your cover letter preview."
        );
        return;
      }
      const response = await fetch(
        `http://localhost:8000/api/documents/cover-letters/${contentId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
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
      processCoverLetterData(coverLetterData, style);
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
    let content = "";
    if (resumeData.personalInfo?.summary)
      content += `**Professional Summary**\n\n${resumeData.personalInfo.summary}\n\n---\n\n`;
    else if (userData.profile_headline)
      content += `**Professional Summary**\n\n${userData.profile_headline}\n\n---\n\n`;
    if (resumeData.skills && resumeData.skills.length > 0)
      content += `**Skills**\n\n${resumeData.skills.join(", ")}\n\n---\n\n`;
    else if (userData.skills)
      content += `**Skills**\n\n${userData.skills}\n\n---\n\n`;
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
    if (resumeData.education && resumeData.education.length > 0) {
      content += `**Education**\n\n`;
      resumeData.education.forEach((edu: any) => {
        content += `**${edu.degree}** from **${edu.institution}**\n`;
        if (edu.dates) content += `*${edu.dates}*\n\n`;
      });
    } else {
      content += `**Education**\n\nAdd your education details in the resume editor to see them here.\n\n`;
    }
    if (resumeData.projects && resumeData.projects.length > 0) {
      content += `\n---\n\n**Projects**\n\n`;
      resumeData.projects.forEach((project: any) => {
        content += `**${project.name || "Project"}**\n`;
        if (project.description) content += `${project.description}\n`;
        if (project.technologies)
          content += `*Technologies: ${project.technologies}*\n\n`;
      });
    }
    if (resumeData.certifications && resumeData.certifications.length > 0) {
      content += `\n---\n\n**Certifications**\n\n`;
      resumeData.certifications.forEach((cert: any) => {
        if (typeof cert === "string") content += `• ${cert}\n`;
        else if (cert.name) {
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
    else window.location.href = "http://localhost:3000";
  };

  const handleDownload = async () => {
    if (!previewData || isDownloading) return;
    setIsDownloading(true);

    try {
      // Dynamically import the library only on the client-side
      const html2pdf = (await import("html2pdf.js")).default;

      const element = document.getElementById("pdf-preview-content");
      if (!element) {
        throw new Error("Preview content element not found.");
      }

      const opt = {
        margin: 0.5,
        filename: `${previewData.content_type}_${currentStyle}.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: "in", format: "letter", orientation: "portrait" },
      };

      // Use html2pdf to generate the PDF from the element
      await html2pdf().set(opt).from(element).save();
    } catch (error) {
      console.error("Download failed:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "An unknown error occurred during download."
      );
    } finally {
      setIsDownloading(false);
    }
  };

  if (loading || !isLoaded) {
    return (
      <div className="flex flex-col h-screen bg-background">
        <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
          <div className="max-w-4xl mx-auto">
            <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
              <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                <div className="p-1.5 sm:p-2 bg-blue-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                  <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-sm sm:text-base md:text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent truncate">
                    Document Preview
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
        <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
          <div className="max-w-4xl mx-auto">
            <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-sate-150">
              <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                <div className="p-1.5 sm:p-2 bg-gradient-to-br from-red-500 to-pink-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                  <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-sm sm:text-base md:text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent truncate">
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
        <main className="flex-1 overflow-hidden pt-14 sm:pt-16 md:pt-20">
          <div className="flex items-center justify-center h-full p-6">
            <div className="text-center max-w-md mx-auto">
              <div className="w-20 h-20 mx-auto mb-6 p-4 bg-gradient-to-br from-red-500/10 to-pink-600/10 rounded-3xl border border-red-500/20">
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

  return (
    <div className="flex flex-col h-screen bg-background">
      <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
          <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
            <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
              <div className="p-1.5 sm:p-2 bg-blue-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
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
                disabled={isDownloading}
                className="h-9 lg:h-10 px-3 lg:px-4 rounded-xl bg-blue-600 hover:bg-blue-700 transition-all duration-200 hover:scale-105"
              >
                {isDownloading ? (
                  <Loader2 className="h-4 w-4 animate-spin lg:mr-2" />
                ) : (
                  <Download className="h-4 w-4 lg:mr-2" />
                )}
                <span className="hidden lg:inline">
                  {isDownloading ? "Generating..." : "Download PDF"}
                </span>
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
                disabled={isDownloading}
                size="sm"
                className="h-8 px-3 sm:h-9 sm:px-4 rounded-lg sm:rounded-xl bg-blue-600 hover:bg-blue-700"
              >
                {isDownloading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-1" />
                )}
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

      <main className="flex-1 overflow-y-auto pt-24 sm:pt-28 md:pt-32">
        <div className="max-w-4xl mx-auto p-4 sm:p-6">
          <div
            id="pdf-preview-content" // Add an ID to the preview wrapper
            className={cn(
              "rounded-2xl sm:rounded-3xl overflow-hidden",
              "bg-white/95 text-foreground border border-slate-200/70 shadow-lg shadow-slate-900/8",
              "dark:bg-black/90 dark:border-gray-600/50 dark:shadow-black/15"
            )}
          >
            {previewData.content_type === "cover_letter" ? (
              <CoverLetterTemplate data={previewData} hasMounted={hasMounted} />
            ) : previewData.content_type === "resume" ? (
              <ResumeTemplate data={previewData} />
            ) : (
              <div className="p-8">
                <p>Unsupported document type.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
