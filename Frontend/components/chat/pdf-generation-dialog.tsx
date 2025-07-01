"use client";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/lib/toast";
import { useAuth } from "@clerk/nextjs";
import {
  Briefcase,
  ChevronDown,
  Download,
  Edit3,
  ExternalLink,
  FileText,
  GraduationCap,
  Plus,
  Sparkles,
  Trash2,
  User,
  X,
} from "lucide-react";
import * as React from "react";

interface PDFGenerationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contentType: "cover_letter" | "resume";
  initialContent?: string;
  contentId?: string;
  companyName?: string;
  jobTitle?: string;
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
      text: "#1f2937",
    },
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
      text: "#111827",
    },
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
      text: "#1f2937",
    },
  },
];

export function PDFGenerationDialog({
  open,
  onOpenChange,
  contentType,
  initialContent = "",
  contentId,
  companyName = "",
  jobTitle = "",
}: PDFGenerationDialogProps) {
  const [selectedStyle, setSelectedStyle] = React.useState("modern");
  const [editedContent, setEditedContent] = React.useState(initialContent);
  const [editedCompanyName, setEditedCompanyName] = React.useState(companyName);
  const [editedJobTitle, setEditedJobTitle] = React.useState(jobTitle);
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [isMobile, setIsMobile] = React.useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = React.useState(false);
  const [isLoadingUserData, setIsLoadingUserData] = React.useState(false);

  // Additional form fields for structured input
  const [personalInfo, setPersonalInfo] = React.useState({
    fullName: "",
    email: "",
    phone: "",
    address: "",
    linkedin: "",
    website: "",
  });

  const [workExperience, setWorkExperience] = React.useState([
    { title: "", company: "", startYear: "", endYear: "", description: "" },
  ]);

  const [education, setEducation] = React.useState([
    { degree: "", school: "", year: "", description: "" },
  ]);

  const [skills, setSkills] = React.useState("");
  const [skillsArray, setSkillsArray] = React.useState<string[]>([]);
  const [newSkill, setNewSkill] = React.useState("");
  const [additionalSections, setAdditionalSections] = React.useState("");

  // Collapsible sections state
  const [expandedSections, setExpandedSections] = React.useState({
    personalInfo: true,
    workExperience: false,
    education: false,
    skills: false,
    additionalSections: false,
    content: contentType === "cover_letter",
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => {
      // Close all sections first
      const allClosed = {
        personalInfo: false,
        workExperience: false,
        education: false,
        skills: false,
        additionalSections: false,
        content: false,
      };

      // If the clicked section was already open, close it (close all)
      // If it was closed, open only that section
      return {
        ...allClosed,
        [section]: !prev[section],
      };
    });
  };

  // Skills management functions
  const addSkill = () => {
    if (
      newSkill.trim() &&
      !skillsArray.includes(newSkill.trim()) &&
      skillsArray.length < 15
    ) {
      setSkillsArray([...skillsArray, newSkill.trim()]);
      setNewSkill("");
      // Also update the skills text for backward compatibility
      setSkills([...skillsArray, newSkill.trim()].join(", "));
    }
  };

  const removeSkill = (skillToRemove: string) => {
    const newSkillsArray = skillsArray.filter(
      (skill) => skill !== skillToRemove
    );
    setSkillsArray(newSkillsArray);
    setSkills(newSkillsArray.join(", "));
  };

  const handleSkillKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addSkill();
    }
  };

  // Initialize skills array from skills string on mount
  React.useEffect(() => {
    if (skills && skillsArray.length === 0) {
      const skillsFromString = skills
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      setSkillsArray(skillsFromString);
    }
  }, [skills, skillsArray.length]);

  const { getToken } = useAuth();

  // Fetch user data when dialog opens
  React.useEffect(() => {
    const fetchUserData = async () => {
      if (!open || isLoadingUserData) return;

      setIsLoadingUserData(true);
      try {
        const token = await getToken();
        if (!token) return;

        // Fetch user profile data
        const [profileResponse, resumeResponse] = await Promise.all([
          fetch("/api/profile", {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch("/api/resume", {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        let profileData: any = null;
        let resumeData: any = null;
        let profileLoaded = false;
        let resumeLoaded = false;

        if (profileResponse.ok) {
          profileData = await profileResponse.json();
          profileLoaded = !!(
            profileData.first_name ||
            profileData.last_name ||
            profileData.name ||
            profileData.email ||
            profileData.phone
          );

          // Populate personal info with user's profile data
          setPersonalInfo({
            fullName:
              `${profileData.first_name || ""} ${
                profileData.last_name || ""
              }`.trim() ||
              profileData.name ||
              "",
            email: profileData.email || "",
            phone: profileData.phone || "",
            address: profileData.address || "",
            linkedin: profileData.linkedin || "",
            website: "", // No website field in user profile currently
          });
        }

        if (resumeResponse.ok) {
          resumeData = await resumeResponse.json();
          resumeLoaded = !!(
            (resumeData.personalInfo &&
              (resumeData.personalInfo.name ||
                resumeData.personalInfo.email)) ||
            (resumeData.experience && resumeData.experience.length > 0) ||
            (resumeData.education && resumeData.education.length > 0) ||
            (resumeData.skills && resumeData.skills.length > 0)
          );

          // Update personal info with resume data if available
          if (resumeData.personalInfo) {
            setPersonalInfo((prev) => ({
              fullName: resumeData.personalInfo.name || prev.fullName,
              email: resumeData.personalInfo.email || prev.email,
              phone: resumeData.personalInfo.phone || prev.phone,
              address: resumeData.personalInfo.location || prev.address,
              linkedin: resumeData.personalInfo.linkedin || prev.linkedin,
              website: prev.website,
            }));
          }

          // Populate work experience
          if (resumeData.experience && resumeData.experience.length > 0) {
            setWorkExperience(
              resumeData.experience.map((exp: any) => ({
                title: exp.jobTitle || "",
                company: exp.company || "",
                startYear: exp.dates
                  ? exp.dates.split("-")[0]?.trim() || ""
                  : "",
                endYear: exp.dates ? exp.dates.split("-")[1]?.trim() || "" : "",
                description: exp.description || "",
              }))
            );
          }

          // Populate education
          if (resumeData.education && resumeData.education.length > 0) {
            setEducation(
              resumeData.education.map((edu: any) => ({
                degree: edu.degree || "",
                school: edu.institution || "",
                year: edu.dates || "",
                description: edu.description || "",
              }))
            );
          }

          // Populate skills
          if (resumeData.skills && resumeData.skills.length > 0) {
            setSkillsArray(resumeData.skills);
            setSkills(resumeData.skills.join(", "));
          }
        }

        // Show appropriate toast message based on loaded data
        if (profileLoaded || resumeLoaded) {
          toast.success("Personal information loaded from your profile");
        } else {
          toast.info(
            "No profile data found. Please fill in your information manually.",
            {
              description:
                "You can create or update your profile to auto-populate this form in the future",
            }
          );
        }
      } catch (error) {
        console.error("Error fetching user data:", error);
        toast.error("Could not load personal information");
      } finally {
        setIsLoadingUserData(false);
      }
    };

    fetchUserData();
  }, [open, getToken]);

  // Handle mobile detection
  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);

    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Improved modal scroll lock - more selective and doesn't interfere with content editing
  React.useEffect(() => {
    if (!open) return;

    const originalScrollY = window.scrollY;
    const originalBodyStyle = {
      overflow: document.body.style.overflow,
      position: document.body.style.position,
      top: document.body.style.top,
      width: document.body.style.width,
    };

    // Apply scroll lock only to the body, not the modal content
    document.body.style.overflow = "hidden";
    document.body.style.scrollbarGutter = "stable";
    document.body.classList.add("modal-open");

    // For iOS Safari, use position fixed approach
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    if (isIOS) {
      document.body.style.position = "fixed";
      document.body.style.top = `-${originalScrollY}px`;
      document.body.style.width = "100%";
    }

    // Prevent background scroll but allow modal content to scroll
    const preventDefault = (e: TouchEvent) => {
      const target = e.target as Element;
      const isWithinModal = target.closest("[data-radix-dialog-content]");
      const isScrollableContent =
        target.closest('textarea, input, [role="textbox"]') ||
        target.closest('[data-scrollable="true"]');

      // Allow scrolling within modal content and text inputs
      if (!isWithinModal && !isScrollableContent) {
        e.preventDefault();
      }
    };

    // Use passive: false only for the prevention check, not for all events
    document.addEventListener("touchmove", preventDefault, { passive: false });

    return () => {
      document.body.style.overflow = originalBodyStyle.overflow;
      document.body.style.position = originalBodyStyle.position;
      document.body.style.top = originalBodyStyle.top;
      document.body.style.width = originalBodyStyle.width;
      document.body.style.scrollbarGutter = "";
      document.body.classList.remove("modal-open");

      // Restore scroll position for iOS
      if (isIOS) {
        window.scrollTo(0, originalScrollY);
      }

      document.removeEventListener("touchmove", preventDefault);
    };
  }, [open]);

  // Initialize content
  React.useEffect(() => {
    if (initialContent && !editedContent) {
      setEditedContent(initialContent);
    }
  }, [initialContent]);

  // Reset form when dialog closes
  React.useEffect(() => {
    if (!open) {
      // Reset only if dialog is closing, not on first mount
      const hasBeenOpened =
        personalInfo.fullName ||
        personalInfo.email ||
        workExperience.some((exp) => exp.title);
      if (hasBeenOpened) {
        setPersonalInfo({
          fullName: "",
          email: "",
          phone: "",
          address: "",
          linkedin: "",
          website: "",
        });
        setWorkExperience([
          {
            title: "",
            company: "",
            startYear: "",
            endYear: "",
            description: "",
          },
        ]);
        setEducation([{ degree: "", school: "", year: "", description: "" }]);
        setSkillsArray([]);
        setSkills("");
        setAdditionalSections("");
        setIsLoadingUserData(false);
      }
    }
  }, [open]);

  const handleDownload = async () => {
    if (isGenerating) return;

    setIsGenerating(true);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Please sign in to download PDFs");
      }

      const contentToUse = getCombinedContent() || initialContent;
      if (!contentToUse || contentToUse.trim().length === 0) {
        throw new Error("Please add some content before downloading");
      }

      const selectedStyleData =
        PDF_STYLES.find((s) => s.key === selectedStyle) || PDF_STYLES[0];

      const requestData: any = {
        style: selectedStyle,
        colors: selectedStyleData.colors,
        company_name: editedCompanyName || "",
        job_title: editedJobTitle || "",
        content_type: contentType,
      };

      // Use content_id if available (saved content), otherwise use content_text (fallback)
      if (contentId) {
        requestData.content_id = contentId;
        console.log("🎯 PDF Dialog using content_id:", contentId);
      } else {
        requestData.content_text = contentToUse.trim();
        console.log("📝 PDF Dialog using content_text as fallback");
      }

      const response = await fetch("/api/pdf/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        let errorMessage = "Failed to generate PDF";
        try {
          const responseContentType = response.headers.get("content-type");
          if (
            responseContentType &&
            responseContentType.includes("application/json")
          ) {
            const errorData = await response.json();
            errorMessage =
              errorData.detail ||
              errorData.message ||
              errorData.error ||
              errorMessage;
          } else {
            const errorText = await response.text();
            errorMessage =
              errorText || `HTTP ${response.status}: ${response.statusText}`;
          }
        } catch (parseError) {
          errorMessage = `Server error (${response.status}): ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const responseContentType = response.headers.get("content-type");
      if (
        !responseContentType ||
        !responseContentType.includes("application/pdf")
      ) {
        throw new Error("Server did not return a PDF file");
      }

      const blob = await response.blob();
      if (blob.size === 0) {
        throw new Error("Received empty PDF file");
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;

      const fileName = `${
        contentType === "cover_letter" ? "cover-letter" : "resume"
      }-${selectedStyle}-${new Date().toISOString().split("T")[0]}.pdf`;
      a.download = fileName;

      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`PDF downloaded successfully!`, {
        description: `File: ${fileName}`,
      });
    } catch (error) {
      console.error("Download error:", error);

      let userMessage = "Failed to download PDF";
      if (error instanceof Error) {
        userMessage = error.message;
      }

      toast.error(userMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePreview = () => {
    try {
      const contentToUse = getCombinedContent() || initialContent;
      if (!contentToUse || contentToUse.trim().length === 0) {
        throw new Error("Please add some content before previewing");
      }

      const selectedStyleData =
        PDF_STYLES.find((s) => s.key === selectedStyle) || PDF_STYLES[0];

      // Create preview data
      const previewData = {
        content: contentToUse.trim(),
        style: selectedStyle,
        colors: selectedStyleData.colors,
        company_name: editedCompanyName || "",
        job_title: editedJobTitle || "",
        content_type: contentType,
        personal_info: personalInfo,
        work_experience: workExperience,
        education: education,
        skills: skills,
        additional_sections: additionalSections,
      };

      // Store preview data in sessionStorage for the preview page
      sessionStorage.setItem("pdf_preview_data", JSON.stringify(previewData));

      // Open preview in new tab with content_id if available for cover letters
      let previewUrl = `/preview?type=${contentType}&style=${selectedStyle}`;
      if (contentType === "cover_letter" && contentId) {
        previewUrl += `&content_id=${contentId}`;
        console.log(
          "🎯 Opening cover letter preview with content_id:",
          contentId
        );
      }

      const newWindow = window.open(
        previewUrl,
        "_blank",
        "noopener,noreferrer"
      );

      if (newWindow) {
        newWindow.focus();
        toast.success("Preview opened in new tab");
      } else {
        toast.error("Please allow popups to view the preview");
      }
    } catch (error) {
      console.error("Preview error:", error);

      let userMessage = "Failed to open preview";
      if (error instanceof Error) {
        userMessage = error.message;
      }

      toast.error(userMessage);
    }
  };

  const selectedStyleData =
    PDF_STYLES.find((s) => s.key === selectedStyle) || PDF_STYLES[0];

  // Check if content is valid - either free-form text or structured data
  const isContentValid = React.useMemo(() => {
    if (editedContent && editedContent.trim().length > 0) return true;

    if (contentType === "resume") {
      // For resumes, check if at least personal info or work experience has content
      const hasPersonalInfo = Object.values(personalInfo).some(
        (val) => val.trim().length > 0
      );
      const hasWorkExperience = workExperience.some(
        (job) =>
          job.title.trim() || job.company.trim() || job.description.trim()
      );
      const hasEducation = education.some(
        (edu) =>
          edu.degree.trim() || edu.school.trim() || edu.description.trim()
      );
      const hasSkills = skills.trim().length > 0 || skillsArray.length > 0;
      const hasAdditionalSections = additionalSections.trim().length > 0;

      return (
        hasPersonalInfo ||
        hasWorkExperience ||
        hasEducation ||
        hasSkills ||
        hasAdditionalSections
      );
    }

    return false;
  }, [
    editedContent,
    contentType,
    personalInfo,
    workExperience,
    education,
    skills,
    additionalSections,
  ]);

  // Combine all content for PDF generation
  const getCombinedContent = () => {
    if (contentType === "cover_letter") {
      return editedContent;
    }

    // For resumes, combine structured data with free-form content
    let combined = "";

    // Personal Information
    if (Object.values(personalInfo).some((val) => val.trim().length > 0)) {
      combined += "**Personal Information**\n\n";
      if (personalInfo.fullName)
        combined += `**Name:** ${personalInfo.fullName}\n`;
      if (personalInfo.email) combined += `**Email:** ${personalInfo.email}\n`;
      if (personalInfo.phone) combined += `**Phone:** ${personalInfo.phone}\n`;
      if (personalInfo.address)
        combined += `**Address:** ${personalInfo.address}\n`;
      if (personalInfo.linkedin)
        combined += `**LinkedIn:** ${personalInfo.linkedin}\n`;
      if (personalInfo.website)
        combined += `**Website:** ${personalInfo.website}\n`;
      combined += "\n---\n\n";
    }

    // Work Experience
    const validJobs = workExperience.filter(
      (job) => job.title.trim() || job.company.trim() || job.description.trim()
    );
    if (validJobs.length > 0) {
      combined += "**Work Experience**\n\n";
      validJobs.forEach((job) => {
        if (job.title || job.company) {
          combined += `**${job.title}** ${
            job.company ? `at ${job.company}` : ""
          }\n`;
        }
        if (job.startYear || job.endYear) {
          combined += `*${job.startYear}${
            job.endYear ? ` - ${job.endYear}` : " - Present"
          }*\n`;
        }
        if (job.description) combined += `${job.description}\n`;
        combined += "\n";
      });
      combined += "---\n\n";
    }

    // Education
    const validEducation = education.filter(
      (edu) => edu.degree.trim() || edu.school.trim() || edu.description.trim()
    );
    if (validEducation.length > 0) {
      combined += "**Education**\n\n";
      validEducation.forEach((edu) => {
        if (edu.degree || edu.school) {
          combined += `**${edu.degree}** ${
            edu.school ? `from ${edu.school}` : ""
          }\n`;
        }
        if (edu.year) combined += `*${edu.year}*\n`;
        if (edu.description) combined += `${edu.description}\n`;
        combined += "\n";
      });
      combined += "---\n\n";
    }

    // Skills
    if (skills.trim() || skillsArray.length > 0) {
      combined += "**Skills**\n\n";
      if (skillsArray.length > 0) {
        combined += `${skillsArray.join(", ")}\n\n---\n\n`;
      } else {
        combined += `${skills}\n\n---\n\n`;
      }
    }

    // Additional Sections
    if (additionalSections.trim()) {
      combined += "**Additional Information**\n\n";
      combined += `${additionalSections}\n\n---\n\n`;
    }

    // Free-form content
    if (editedContent.trim()) {
      combined += editedContent;
    }

    return combined.trim();
  };

  // Simple markdown to HTML conversion for preview
  const formatContentForPreview = (content: string) => {
    if (!content)
      return '<p class="text-gray-500 italic">Start writing your content in the editor to see it here...</p>';

    let formatted = content
      // Bold text
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
      // Italic text
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      // Bullet points
      .replace(/^• (.*$)/gim, '<li class="ml-4 mb-1">$1</li>')
      // Section dividers
      .replace(/^---$/gm, '<hr class="my-4 border-gray-300">')
      // Paragraphs (double line breaks)
      .replace(/\n\n/g, '</p><p class="mb-3">')
      // Single line breaks
      .replace(/\n/g, "<br>");

    // Wrap consecutive list items in ul tags
    formatted = formatted.replace(
      /(<li.*<\/li>)/g,
      '<ul class="list-disc list-inside mb-3 space-y-1">$1</ul>'
    );

    // Wrap in paragraph tags if not already wrapped
    if (!formatted.startsWith("<")) {
      formatted = `<p class="mb-3">${formatted}</p>`;
    }

    return formatted;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] sm:max-w-6xl max-h-[92vh] sm:max-h-[95vh] w-[95vw] h-[92vh] sm:w-[95vw] sm:h-[95vh] flex flex-col bg-white/95 dark:bg-gray-950/95 backdrop-blur-3xl backdrop-saturate-200 rounded-2xl sm:rounded-3xl overflow-hidden p-0 border border-white/40 dark:border-gray-800/50 shadow-2xl">
        {/* Enhanced glassmorphism effects */}
        <div className="absolute inset-0 rounded-2xl sm:rounded-3xl pointer-events-none bg-gradient-to-br from-white/30 via-white/10 to-transparent dark:from-white/20 dark:via-white/5 dark:to-transparent" />
        <div className="absolute inset-0 rounded-2xl sm:rounded-3xl pointer-events-none border border-white/50 dark:border-white/30" />
        <div className="absolute inset-[1px] rounded-2xl sm:rounded-3xl pointer-events-none bg-gradient-to-b from-white/20 via-transparent to-transparent dark:from-white/10 dark:via-transparent dark:to-transparent" />

        {/* Header */}
        <div className="flex-shrink-0 bg-white/90 dark:bg-gray-950/90 backdrop-blur-md border-b border-white/40 dark:border-gray-800/60 p-3 sm:p-5 relative z-10">
          {/* Mobile Layout */}
          <div className="flex sm:hidden items-center justify-between gap-3">
            {/* Left: Document Type */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-300/40 shadow-lg dark:from-blue-400/20 dark:to-purple-400/20 dark:border-blue-600/40 flex items-center justify-center backdrop-blur-sm flex-shrink-0">
                <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="min-w-0 flex-1">
                <DialogTitle className="text-lg font-bold text-gray-900 dark:text-gray-100 leading-tight">
                  {contentType === "cover_letter" ? "Cover Letter" : "Resume"}{" "}
                  Generator
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
              className="h-9 w-9 rounded-lg transition-all duration-300 hover:scale-105 bg-gray-200 border border-gray-300 backdrop-blur-sm hover:bg-gray-300 hover:border-gray-400 dark:bg-gray-700 dark:border-gray-600 dark:hover:bg-gray-600 dark:hover:border-gray-500 flex-shrink-0 relative z-20 shadow-lg"
            >
              <X className="h-4 w-4 text-gray-700 dark:text-gray-200" />
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
                  {contentType === "cover_letter" ? "Cover Letter" : "Resume"}{" "}
                  Generator
                </DialogTitle>
                <p className="text-sm text-gray-600 dark:text-gray-400 -mt-0.5">
                  Create and customize your professional document
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
        <div className="flex-shrink-0 border-b border-white/40 dark:border-gray-800/60 bg-gray-50/90 dark:bg-gray-900/90 backdrop-blur-md relative z-10">
          {/* Mobile Navigation - Collapsible */}
          <div className="sm:hidden px-5 py-4">
            <button
              onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
              className="flex items-center justify-between w-full p-4 rounded-xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border border-white/40 dark:border-gray-700/60 hover:bg-white/95 dark:hover:bg-gray-750/95 transition-all duration-300 hover:scale-[1.02] shadow-lg hover:shadow-xl"
            >
              <div className="flex items-center gap-3">
                {/* Show current section icon */}
                {contentType === "cover_letter" &&
                  expandedSections.personalInfo && (
                    <>
                      <Briefcase className="h-4 w-4 text-blue-600" />
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        Job Details
                      </span>
                    </>
                  )}
                {contentType === "resume" && expandedSections.personalInfo && (
                  <>
                    <User className="h-4 w-4 text-blue-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Personal Info
                    </span>
                  </>
                )}
                {expandedSections.workExperience && (
                  <>
                    <Briefcase className="h-4 w-4 text-green-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Work Experience
                    </span>
                  </>
                )}
                {expandedSections.education && (
                  <>
                    <GraduationCap className="h-4 w-4 text-purple-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Education
                    </span>
                  </>
                )}
                {expandedSections.skills && (
                  <>
                    <Sparkles className="h-4 w-4 text-orange-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Skills
                    </span>
                  </>
                )}
                {expandedSections.additionalSections && (
                  <>
                    <FileText className="h-4 w-4 text-indigo-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Additional
                    </span>
                  </>
                )}
                {expandedSections.content && (
                  <>
                    <Edit3 className="h-4 w-4 text-teal-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Content
                    </span>
                  </>
                )}
                {!Object.values(expandedSections).some(Boolean) && (
                  <>
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span className="font-medium text-gray-500">
                      Select Section
                    </span>
                  </>
                )}
              </div>
              <ChevronDown
                className={`h-4 w-4 text-gray-500 transition-transform ${
                  isMobileNavOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {/* Mobile dropdown menu */}
            {isMobileNavOpen && (
              <div className="mt-3 p-3 bg-white/95 dark:bg-gray-800/95 rounded-xl border border-gray-200/60 dark:border-gray-700/60 shadow-xl backdrop-blur-md space-y-2">
                {/* Cover Letter Job Details */}
                {contentType === "cover_letter" && (
                  <button
                    onClick={() => {
                      toggleSection("personalInfo");
                      setIsMobileNavOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                      expandedSections.personalInfo
                        ? "bg-gradient-to-r from-blue-100 to-blue-50 text-blue-700 border border-blue-200/50 shadow-md dark:from-blue-900/40 dark:to-blue-800/30 dark:text-blue-300 dark:border-blue-700/50"
                        : "text-gray-700 hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 hover:shadow-md dark:text-gray-300 dark:hover:from-gray-700 dark:hover:to-gray-600"
                    }`}
                  >
                    <Briefcase className="h-4 w-4 flex-shrink-0" />
                    Job Application Details
                  </button>
                )}

                {/* Resume Sections */}
                {contentType === "resume" && (
                  <>
                    <button
                      onClick={() => {
                        toggleSection("personalInfo");
                        setIsMobileNavOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                        expandedSections.personalInfo
                          ? "bg-gradient-to-r from-blue-100 to-blue-50 text-blue-700 border border-blue-200/50 shadow-md dark:from-blue-900/40 dark:to-blue-800/30 dark:text-blue-300 dark:border-blue-700/50"
                          : "text-gray-700 hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 hover:shadow-md dark:text-gray-300 dark:hover:from-gray-700 dark:hover:to-gray-600"
                      }`}
                    >
                      <User className="h-4 w-4 flex-shrink-0" />
                      Personal Information
                    </button>

                    <button
                      onClick={() => {
                        toggleSection("workExperience");
                        setIsMobileNavOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                        expandedSections.workExperience
                          ? "bg-gradient-to-r from-green-100 to-emerald-50 text-green-700 border border-green-200/50 shadow-md dark:from-green-900/40 dark:to-emerald-800/30 dark:text-green-300 dark:border-green-700/50"
                          : "text-gray-700 hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 hover:shadow-md dark:text-gray-300 dark:hover:from-gray-700 dark:hover:to-gray-600"
                      }`}
                    >
                      <Briefcase className="h-4 w-4 flex-shrink-0" />
                      Work Experience
                    </button>

                    <button
                      onClick={() => {
                        toggleSection("education");
                        setIsMobileNavOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                        expandedSections.education
                          ? "bg-gradient-to-r from-purple-100 to-violet-50 text-purple-700 border border-purple-200/50 shadow-md dark:from-purple-900/40 dark:to-violet-800/30 dark:text-purple-300 dark:border-purple-700/50"
                          : "text-gray-700 hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 hover:shadow-md dark:text-gray-300 dark:hover:from-gray-700 dark:hover:to-gray-600"
                      }`}
                    >
                      <GraduationCap className="h-4 w-4 flex-shrink-0" />
                      Education
                    </button>

                    <button
                      onClick={() => {
                        toggleSection("skills");
                        setIsMobileNavOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                        expandedSections.skills
                          ? "bg-gradient-to-r from-orange-100 to-amber-50 text-orange-700 border border-orange-200/50 shadow-md dark:from-orange-900/40 dark:to-amber-800/30 dark:text-orange-300 dark:border-orange-700/50"
                          : "text-gray-700 hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 hover:shadow-md dark:text-gray-300 dark:hover:from-gray-700 dark:hover:to-gray-600"
                      }`}
                    >
                      <Sparkles className="h-4 w-4 flex-shrink-0" />
                      Skills & Competencies
                    </button>

                    <button
                      onClick={() => {
                        toggleSection("additionalSections");
                        setIsMobileNavOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                        expandedSections.additionalSections
                          ? "bg-gradient-to-r from-indigo-100 to-blue-50 text-indigo-700 border border-indigo-200/50 shadow-md dark:from-indigo-900/40 dark:to-blue-800/30 dark:text-indigo-300 dark:border-indigo-700/50"
                          : "text-gray-700 hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 hover:shadow-md dark:text-gray-300 dark:hover:from-gray-700 dark:hover:to-gray-600"
                      }`}
                    >
                      <FileText className="h-4 w-4 flex-shrink-0" />
                      Additional Sections
                    </button>
                  </>
                )}

                <button
                  onClick={() => {
                    toggleSection("content");
                    setIsMobileNavOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                    expandedSections.content
                      ? "bg-gradient-to-r from-teal-100 to-cyan-50 text-teal-700 border border-teal-200/50 shadow-md dark:from-teal-900/40 dark:to-cyan-800/30 dark:text-teal-300 dark:border-teal-700/50"
                      : "text-gray-700 hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 hover:shadow-md dark:text-gray-300 dark:hover:from-gray-700 dark:hover:to-gray-600"
                  }`}
                >
                  <Edit3 className="h-4 w-4 flex-shrink-0" />
                  {contentType === "cover_letter"
                    ? "Cover Letter Content"
                    : "Free-form Content"}
                </button>
              </div>
            )}
          </div>

          {/* Desktop Navigation - Tabs */}
          <div className="hidden sm:block px-5 sm:px-6">
            <div className="flex overflow-x-auto scrollbar-hide -mb-px gap-1">
              {/* Cover Letter Job Details */}
              {contentType === "cover_letter" && (
                <button
                  onClick={() => toggleSection("personalInfo")}
                  className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                    expandedSections.personalInfo
                      ? "border-blue-500 text-blue-700 bg-gradient-to-t from-blue-50 to-blue-25 shadow-lg dark:from-blue-900/30 dark:to-blue-800/20 dark:text-blue-300 dark:border-blue-400"
                      : "border-transparent text-gray-600 hover:text-blue-700 hover:border-blue-500 hover:bg-gradient-to-t hover:from-blue-50 hover:to-blue-25 hover:shadow-lg dark:text-gray-400 dark:hover:text-blue-300 dark:hover:from-blue-900/30 dark:hover:to-blue-800/20 dark:hover:border-blue-400"
                  }`}
                >
                  <Briefcase className="h-4 w-4 flex-shrink-0" />
                  <span>Job Details</span>
                </button>
              )}

              {/* Resume Sections */}
              {contentType === "resume" && (
                <>
                  <button
                    onClick={() => toggleSection("personalInfo")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.personalInfo
                        ? "border-blue-500 text-blue-700 bg-gradient-to-t from-blue-50 to-blue-25 shadow-lg dark:from-blue-900/30 dark:to-blue-800/20 dark:text-blue-300 dark:border-blue-400"
                        : "border-transparent text-gray-600 hover:text-blue-700 hover:border-blue-500 hover:bg-gradient-to-t hover:from-blue-50 hover:to-blue-25 hover:shadow-lg dark:text-gray-400 dark:hover:text-blue-300 dark:hover:from-blue-900/30 dark:hover:to-blue-800/20 dark:hover:border-blue-400"
                    }`}
                  >
                    <User className="h-4 w-4 flex-shrink-0" />
                    <span>Personal</span>
                  </button>

                  <button
                    onClick={() => toggleSection("workExperience")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.workExperience
                        ? "border-green-500 text-green-700 bg-gradient-to-t from-green-50 to-emerald-25 shadow-lg dark:from-green-900/30 dark:to-emerald-800/20 dark:text-green-300 dark:border-green-400"
                        : "border-transparent text-gray-600 hover:text-green-700 hover:border-green-500 hover:bg-gradient-to-t hover:from-green-50 hover:to-emerald-25 hover:shadow-lg dark:text-gray-400 dark:hover:text-green-300 dark:hover:from-green-900/30 dark:hover:to-emerald-800/20 dark:hover:border-green-400"
                    }`}
                  >
                    <Briefcase className="h-4 w-4 flex-shrink-0" />
                    <span>Work</span>
                  </button>

                  <button
                    onClick={() => toggleSection("education")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.education
                        ? "border-purple-500 text-purple-700 bg-gradient-to-t from-purple-50 to-violet-25 shadow-lg dark:from-purple-900/30 dark:to-violet-800/20 dark:text-purple-300 dark:border-purple-400"
                        : "border-transparent text-gray-600 hover:text-purple-700 hover:border-purple-500 hover:bg-gradient-to-t hover:from-purple-50 hover:to-violet-25 hover:shadow-lg dark:text-gray-400 dark:hover:text-purple-300 dark:hover:from-purple-900/30 dark:hover:to-violet-800/20 dark:hover:border-purple-400"
                    }`}
                  >
                    <GraduationCap className="h-4 w-4 flex-shrink-0" />
                    <span>Education</span>
                  </button>

                  <button
                    onClick={() => toggleSection("skills")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.skills
                        ? "border-orange-500 text-orange-700 bg-gradient-to-t from-orange-50 to-amber-25 shadow-lg dark:from-orange-900/30 dark:to-amber-800/20 dark:text-orange-300 dark:border-orange-400"
                        : "border-transparent text-gray-600 hover:text-orange-700 hover:border-orange-500 hover:bg-gradient-to-t hover:from-orange-50 hover:to-amber-25 hover:shadow-lg dark:text-gray-400 dark:hover:text-orange-300 dark:hover:from-orange-900/30 dark:hover:to-amber-800/20 dark:hover:border-orange-400"
                    }`}
                  >
                    <Sparkles className="h-4 w-4 flex-shrink-0" />
                    <span>Skills</span>
                  </button>

                  <button
                    onClick={() => toggleSection("additionalSections")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.additionalSections
                        ? "border-indigo-500 text-indigo-700 bg-gradient-to-t from-indigo-50 to-blue-25 shadow-lg dark:from-indigo-900/30 dark:to-blue-800/20 dark:text-indigo-300 dark:border-indigo-400"
                        : "border-transparent text-gray-600 hover:text-indigo-700 hover:border-indigo-500 hover:bg-gradient-to-t hover:from-indigo-50 hover:to-blue-25 hover:shadow-lg dark:text-gray-400 dark:hover:text-indigo-300 dark:hover:from-indigo-900/30 dark:hover:to-blue-800/20 dark:hover:border-indigo-400"
                    }`}
                  >
                    <FileText className="h-4 w-4 flex-shrink-0" />
                    <span>More</span>
                  </button>
                </>
              )}

              <button
                onClick={() => toggleSection("content")}
                className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                  expandedSections.content
                    ? "border-teal-500 text-teal-700 bg-gradient-to-t from-teal-50 to-cyan-25 shadow-lg dark:from-teal-900/30 dark:to-cyan-800/20 dark:text-teal-300 dark:border-teal-400"
                    : "border-transparent text-gray-600 hover:text-teal-700 hover:border-teal-500 hover:bg-gradient-to-t hover:from-teal-50 hover:to-cyan-25 hover:shadow-lg dark:text-gray-400 dark:hover:text-teal-300 dark:hover:from-teal-900/30 dark:hover:to-cyan-800/20 dark:hover:border-teal-400"
                }`}
              >
                <Edit3 className="h-4 w-4 flex-shrink-0" />
                <span>Content</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div
          className="flex-1 overflow-auto scrollbar-thin"
          data-scrollable="true"
        >
          {/* Editor View */}
          <div className="h-full flex flex-col">
            {/* Content Editor */}
            <div className="flex-1 p-3 sm:p-6 bg-gradient-to-br from-gray-50/30 via-white/20 to-gray-100/30 dark:from-gray-900/30 dark:via-gray-800/20 dark:to-gray-900/40 backdrop-blur-sm">
              <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
                {/* Cover Letter Job Details */}
                {contentType === "cover_letter" &&
                  expandedSections.personalInfo && (
                    <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                        <Briefcase className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 flex-shrink-0" />
                        <span className="truncate">
                          Job Application Details
                        </span>
                      </h2>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                            Company Name
                          </Label>
                          <Input
                            placeholder="e.g., Google Inc."
                            value={editedCompanyName}
                            onChange={(e) =>
                              setEditedCompanyName(e.target.value)
                            }
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
                    </div>
                  )}

                {/* Personal Information Section */}
                {contentType === "resume" && expandedSections.personalInfo && (
                  <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <User className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 flex-shrink-0" />
                      <span className="truncate">Personal Information</span>
                      {isLoadingUserData && (
                        <div className="ml-auto flex items-center gap-2 text-xs text-blue-600">
                          <div className="w-3 h-3 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                          Loading...
                        </div>
                      )}
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                      <div className="space-y-3 sm:space-y-4">
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 sm:mb-2 block">
                            Full Name
                          </Label>
                          <Input
                            placeholder="John Doe"
                            value={personalInfo.fullName}
                            onChange={(e) =>
                              setPersonalInfo({
                                ...personalInfo,
                                fullName: e.target.value,
                              })
                            }
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
                            onChange={(e) =>
                              setPersonalInfo({
                                ...personalInfo,
                                email: e.target.value,
                              })
                            }
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
                            onChange={(e) =>
                              setPersonalInfo({
                                ...personalInfo,
                                phone: e.target.value,
                              })
                            }
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
                            onChange={(e) =>
                              setPersonalInfo({
                                ...personalInfo,
                                address: e.target.value,
                              })
                            }
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
                            onChange={(e) =>
                              setPersonalInfo({
                                ...personalInfo,
                                linkedin: e.target.value,
                              })
                            }
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
                            onChange={(e) =>
                              setPersonalInfo({
                                ...personalInfo,
                                website: e.target.value,
                              })
                            }
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Work Experience Section */}
                {contentType === "resume" &&
                  expandedSections.workExperience && (
                    <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                        <Briefcase className="h-4 w-4 sm:h-5 sm:w-5 text-green-600 flex-shrink-0" />
                        <span className="truncate">Work Experience</span>
                      </h2>
                      <div className="space-y-4 sm:space-y-6">
                        {workExperience.map((job, index) => (
                          <div
                            key={index}
                            className="relative border border-gray-200 dark:border-gray-600/30 rounded-xl p-4 sm:p-6 bg-gray-50/50 dark:bg-gradient-to-br dark:from-gray-800/90 dark:via-gray-700/80 dark:to-gray-900/90 backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-200 group"
                          >
                            {/* Header with improved styling */}
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center shadow-lg">
                                  <span className="text-white text-xs font-bold">
                                    {index + 1}
                                  </span>
                                </div>
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                                    {job.title || `Job Position ${index + 1}`}
                                  </h4>
                                  {job.company && (
                                    <p className="text-xs text-gray-600 dark:text-gray-300">
                                      at {job.company}
                                    </p>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                {(job.startYear || job.endYear) && (
                                  <div className="text-xs bg-gray-100 dark:bg-white/20 text-gray-700 dark:text-white px-2 py-1 rounded-md backdrop-blur-sm">
                                    {job.startYear} - {job.endYear || "Present"}
                                  </div>
                                )}
                                {workExperience.length > 1 && (
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() =>
                                      setWorkExperience(
                                        workExperience.filter(
                                          (_, i) => i !== index
                                        )
                                      )
                                    }
                                    className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                                  >
                                    <Trash2 className="h-3 w-3 sm:h-4 sm:w-4" />
                                  </Button>
                                )}
                              </div>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-3 sm:mb-4">
                              <div>
                                <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-white mb-1.5 sm:mb-2 block">
                                  Job Title
                                </Label>
                                <Input
                                  placeholder="Software Engineer"
                                  value={job.title}
                                  onChange={(e) => {
                                    const updated = [...workExperience];
                                    updated[index].title = e.target.value;
                                    setWorkExperience(updated);
                                  }}
                                  className="h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                                />
                              </div>
                              <div>
                                <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-white mb-1.5 sm:mb-2 block">
                                  Company
                                </Label>
                                <Input
                                  placeholder="Google Inc."
                                  value={job.company}
                                  onChange={(e) => {
                                    const updated = [...workExperience];
                                    updated[index].company = e.target.value;
                                    setWorkExperience(updated);
                                  }}
                                  className="h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                                />
                              </div>
                              <div>
                                <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-white mb-1.5 sm:mb-2 block">
                                  Start Year
                                </Label>
                                <Input
                                  placeholder="2020"
                                  value={job.startYear}
                                  onChange={(e) => {
                                    const updated = [...workExperience];
                                    updated[index].startYear = e.target.value;
                                    setWorkExperience(updated);
                                  }}
                                  className="h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                                />
                              </div>
                              <div>
                                <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-white mb-1.5 sm:mb-2 block">
                                  End Year
                                </Label>
                                <Input
                                  placeholder="2023 or Present"
                                  value={job.endYear}
                                  onChange={(e) => {
                                    const updated = [...workExperience];
                                    updated[index].endYear = e.target.value;
                                    setWorkExperience(updated);
                                  }}
                                  className="h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                                />
                              </div>
                            </div>
                            <div>
                              <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-white mb-1.5 sm:mb-2 block">
                                Job Description & Achievements
                              </Label>
                              <Textarea
                                placeholder="• Developed and maintained web applications using React and Node.js&#10;• Led a team of 5 developers in delivering high-quality software solutions&#10;• Improved application performance by 40% through code optimization"
                                value={job.description}
                                onChange={(e) => {
                                  const updated = [...workExperience];
                                  updated[index].description = e.target.value;
                                  setWorkExperience(updated);
                                }}
                                rows={4}
                                data-scrollable="true"
                                className="resize-none text-sm sm:text-base px-3 sm:px-4 py-2.5 sm:py-3 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all duration-200 cursor-text"
                                style={{
                                  fontSize: isMobile ? "16px" : undefined,
                                  lineHeight: "1.5",
                                  overflowY: "auto",
                                  scrollbarWidth: "thin",
                                }}
                              />
                            </div>
                          </div>
                        ))}
                        <Button
                          onClick={() =>
                            setWorkExperience([
                              ...workExperience,
                              {
                                title: "",
                                company: "",
                                startYear: "",
                                endYear: "",
                                description: "",
                              },
                            ])
                          }
                          variant="outline"
                          className="w-full border-dashed border-2 h-11 sm:h-12 text-gray-600 hover:text-gray-900 hover:border-gray-400 text-sm sm:text-base font-medium touch-manipulation"
                        >
                          <Plus className="h-4 w-4 mr-2 flex-shrink-0" />
                          <span className="hidden sm:inline">
                            Add Another Job
                          </span>
                          <span className="sm:hidden">Add Job</span>
                        </Button>
                      </div>
                    </div>
                  )}

                {/* Education Section */}
                {contentType === "resume" && expandedSections.education && (
                  <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <GraduationCap className="h-4 w-4 sm:h-5 sm:w-5 text-purple-600 flex-shrink-0" />
                      <span className="truncate">Education</span>
                    </h2>
                    <div className="space-y-6">
                      {education.map((edu, index) => (
                        <div
                          key={index}
                          className="border border-gray-200 dark:border-gray-600/30 rounded-xl p-4 sm:p-6 bg-gray-50 dark:bg-gradient-to-br dark:from-gray-800/90 dark:via-gray-700/80 dark:to-gray-900/90 backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-200 group"
                        >
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-violet-500 flex items-center justify-center shadow-lg">
                                <span className="text-white text-xs font-bold">
                                  {index + 1}
                                </span>
                              </div>
                              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                                Education #{index + 1}
                              </h4>
                            </div>
                            {education.length > 1 && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() =>
                                  setEducation(
                                    education.filter((_, i) => i !== index)
                                  )
                                }
                                className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                              >
                                <Trash2 className="h-3 w-3 sm:h-4 sm:w-4" />
                              </Button>
                            )}
                          </div>
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                            <div>
                              <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                Degree/Certification
                              </Label>
                              <Input
                                placeholder="Bachelor of Computer Science"
                                value={edu.degree}
                                onChange={(e) => {
                                  const updated = [...education];
                                  updated[index].degree = e.target.value;
                                  setEducation(updated);
                                }}
                              />
                            </div>
                            <div>
                              <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                School/Institution
                              </Label>
                              <Input
                                placeholder="Stanford University"
                                value={edu.school}
                                onChange={(e) => {
                                  const updated = [...education];
                                  updated[index].school = e.target.value;
                                  setEducation(updated);
                                }}
                              />
                            </div>
                          </div>
                          <div className="mb-4">
                            <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                              Graduation Year
                            </Label>
                            <Input
                              placeholder="2020"
                              value={edu.year}
                              onChange={(e) => {
                                const updated = [...education];
                                updated[index].year = e.target.value;
                                setEducation(updated);
                              }}
                            />
                          </div>
                          <div>
                            <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                              Additional Details
                            </Label>
                            <Textarea
                              placeholder="GPA: 3.8/4.0&#10;Magna Cum Laude&#10;Relevant Coursework: Data Structures, Algorithms, Machine Learning"
                              value={edu.description}
                              onChange={(e) => {
                                const updated = [...education];
                                updated[index].description = e.target.value;
                                setEducation(updated);
                              }}
                              rows={3}
                              data-scrollable="true"
                              className="resize-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all duration-200 cursor-text"
                              style={{
                                fontSize: isMobile ? "16px" : undefined,
                                lineHeight: "1.5",
                                overflowY: "auto",
                                scrollbarWidth: "thin",
                              }}
                            />
                          </div>
                        </div>
                      ))}
                      <Button
                        onClick={() =>
                          setEducation([
                            ...education,
                            {
                              degree: "",
                              school: "",
                              year: "",
                              description: "",
                            },
                          ])
                        }
                        variant="outline"
                        className="w-full border-dashed border-2 h-12 text-gray-600 hover:text-gray-900 hover:border-gray-400"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add Another Education
                      </Button>
                    </div>
                  </div>
                )}

                {/* Skills Section */}
                {contentType === "resume" && expandedSections.skills && (
                  <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <Sparkles className="h-4 w-4 sm:h-5 sm:w-5 text-orange-600 flex-shrink-0" />
                      <span className="truncate">Skills & Competencies</span>
                    </h2>

                    {/* Skill Input */}
                    <div className="mb-4">
                      <Label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                        Add Skills
                      </Label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="e.g., JavaScript, React, Python..."
                          value={newSkill}
                          onChange={(e) => setNewSkill(e.target.value)}
                          onKeyPress={handleSkillKeyPress}
                          className="flex-1 h-10 text-sm px-3"
                        />
                        <Button
                          onClick={addSkill}
                          variant="outline"
                          size="sm"
                          className="h-10 px-4 text-sm font-medium"
                          disabled={
                            !newSkill.trim() || skillsArray.length >= 15
                          }
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Press Enter or click + to add skills (
                        {skillsArray.length}/15)
                      </p>
                    </div>

                    {/* Skills Display */}
                    <div className="space-y-3">
                      <Label className="text-sm font-medium text-gray-700 dark:text-gray-300 block">
                        Your Skills ({skillsArray.length})
                      </Label>
                      {skillsArray.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {skillsArray.map((skill, index) => (
                            <div
                              key={index}
                              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-medium bg-white/70 dark:bg-gray-800/70 backdrop-blur-md text-gray-700 dark:text-gray-200 border border-white/40 dark:border-gray-600/40 hover:bg-white/90 dark:hover:bg-gray-700/90 hover:border-gray-300/60 dark:hover:border-gray-500/60 shadow-sm hover:shadow-md transition-all duration-200 group"
                            >
                              <span className="max-w-[120px] truncate">
                                {skill}
                              </span>
                              <button
                                onClick={() => removeSkill(skill)}
                                className="ml-1 rounded-full p-0.5 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 hover:text-red-700 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all duration-150 group-hover:scale-110"
                                aria-label={`Remove ${skill}`}
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                          <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">No skills added yet</p>
                          <p className="text-xs">Add your first skill above</p>
                        </div>
                      )}
                    </div>

                    {/* Fallback Textarea for Advanced Users */}
                    <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <Label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                        Raw Skills Text (Advanced)
                      </Label>
                      <Textarea
                        placeholder="You can also paste a formatted skills list here..."
                        value={skills}
                        onChange={(e) => {
                          setSkills(e.target.value);
                          // Parse skills from text and update array
                          const newSkillsArray = e.target.value
                            .split(/[,\n]/)
                            .map((s) => s.trim())
                            .filter((s) => s.length > 0)
                            .slice(0, 15); // Limit to 15 skills
                          setSkillsArray(newSkillsArray);
                        }}
                        rows={3}
                        data-scrollable="true"
                        className="resize-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all duration-200 cursor-text text-xs"
                        style={{
                          fontSize: isMobile ? "14px" : undefined,
                          lineHeight: "1.4",
                          overflowY: "auto",
                          scrollbarWidth: "thin",
                        }}
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Skills are automatically synced between bubbles and text
                      </p>
                    </div>
                  </div>
                )}

                {/* Additional Sections */}
                {contentType === "resume" &&
                  expandedSections.additionalSections && (
                    <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-3">
                        <FileText className="h-5 w-5 text-indigo-600" />
                        Additional Sections
                      </h2>
                      <Label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                        Additional Information
                      </Label>
                      <Textarea
                        placeholder="**Projects**&#10;• Personal Portfolio Website - Built with React and deployed on Vercel&#10;• E-commerce API - RESTful API built with Node.js and MongoDB&#10;&#10;**Certifications**&#10;• AWS Certified Solutions Architect&#10;• Google Cloud Professional Developer&#10;&#10;**Awards**&#10;• Employee of the Month - March 2023&#10;• Dean's List - Fall 2019, Spring 2020"
                        value={additionalSections}
                        onChange={(e) => setAdditionalSections(e.target.value)}
                        rows={8}
                        data-scrollable="true"
                        className="resize-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all duration-200 cursor-text"
                        style={{
                          fontSize: isMobile ? "16px" : undefined,
                          lineHeight: "1.5",
                          overflowY: "auto",
                          scrollbarWidth: "thin",
                        }}
                      />
                    </div>
                  )}

                {/* Content Editor Section */}
                {expandedSections.content && (
                  <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg border border-white/30 dark:border-gray-700/50">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <Edit3 className="h-4 w-4 sm:h-5 sm:w-5 text-teal-600 flex-shrink-0" />
                      <span className="truncate">
                        {contentType === "cover_letter"
                          ? "Cover Letter Content"
                          : "Free-form Content"}
                      </span>
                    </h2>
                    <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                      {contentType === "cover_letter"
                        ? "Cover Letter Text"
                        : "Additional Content"}
                    </Label>
                    <Textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      placeholder={
                        contentType === "cover_letter"
                          ? `Dear Hiring Manager,

I am writing to express my strong interest in the ${
                              editedJobTitle || "[Job Title]"
                            } position at ${
                              editedCompanyName || "[Company Name]"
                            }. With my background in [Your Field] and [X] years of experience, I am confident that I would be a valuable addition to your team.

In my previous role at [Previous Company], I successfully [Key Achievement]. This experience has equipped me with [Relevant Skills] that directly align with the requirements of this position.

I am particularly drawn to [Company Name] because [Reason for Interest in Company]. I am excited about the opportunity to contribute to [Specific Project/Goal] and help drive [Company Objective].

Thank you for considering my application. I look forward to discussing how my skills and experience can contribute to your team's success.

Sincerely,
[Your Name]`
                          : `Use this section to add any additional content or to override the structured format above with custom text.

**Formatting Tips:**
• Use **bold** and *italic* text for emphasis
• Create bullet points with • at the start of lines
• Add section dividers with ---
• Write in a professional, clear tone

This content will be added to your resume after the structured sections above.`
                      }
                      rows={contentType === "cover_letter" ? 16 : 12}
                      data-scrollable="true"
                      className="resize-none text-sm sm:text-base px-3 sm:px-4 py-2.5 sm:py-3 leading-relaxed min-h-[300px] sm:min-h-[400px] focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all duration-200 cursor-text scrollbar-thin backdrop-blur-sm bg-white/50 dark:bg-gray-900/50"
                      style={{
                        fontSize: isMobile ? "16px" : undefined,
                        lineHeight: "1.6",
                        resize: "none",
                        overflowY: "auto",
                      }}
                      onFocus={(e) => {
                        // Ensure cursor is properly positioned
                        setTimeout(() => {
                          e.target.scrollIntoView({
                            behavior: "smooth",
                            block: "center",
                          });
                        }, 100);
                      }}
                    />
                    <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                      <div className="flex items-center gap-4">
                        <span>{editedContent.length} characters</span>
                        <span>
                          ~{Math.ceil(editedContent.split(" ").length / 250)}{" "}
                          pages
                        </span>
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
  );
}
