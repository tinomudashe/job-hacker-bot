"use client";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/lib/toast";
import { useAuth } from "@clerk/nextjs";
import {
  Award,
  Briefcase,
  ChevronDown,
  Edit3,
  ExternalLink,
  FileText,
  Globe,
  GraduationCap,
  Lightbulb,
  Plus,
  Save,
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
  const [recipientName, setRecipientName] = React.useState("");
  const [recipientTitle, setRecipientTitle] = React.useState("");
  const [isMobile, setIsMobile] = React.useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = React.useState(false);
  const [isLoadingUserData, setIsLoadingUserData] = React.useState(false);
  const [isSaving, setIsSaving] = React.useState(false);

  // Additional form fields for structured input
  const [personalInfo, setPersonalInfo] = React.useState({
    fullName: "",
    email: "",
    phone: "",
    address: "",
    linkedin: "",
    website: "",
    summary: "",
  });

  const [workExperience, setWorkExperience] = React.useState([
    {
      id: "",
      title: "",
      company: "",
      startYear: "",
      endYear: "",
      description: "",
    },
  ]);

  const [education, setEducation] = React.useState([
    { id: "", degree: "", school: "", year: "", description: "" },
  ]);

  const [skills, setSkills] = React.useState("");
  const [skillsArray, setSkillsArray] = React.useState<string[]>([]);
  const [newSkill, setNewSkill] = React.useState("");
  const [additionalSections, setAdditionalSections] = React.useState("");

  const [projects, setProjects] = React.useState([
    { name: "", description: "", technologies: "", url: "" },
  ]);
  const [certifications, setCertifications] = React.useState([
    { name: "", issuing_organization: "", date_issued: "" },
  ]);
  const [languages, setLanguages] = React.useState([
    { name: "", proficiency: "" },
  ]);

  // Collapsible sections state
  const [expandedSections, setExpandedSections] = React.useState({
    personalInfo: true,
    workExperience: false,
    education: false,
    skills: false,
    projects: false,
    certifications: false,
    languages: false,
    additionalSections: false,
    content: contentType === "cover_letter",
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections({
      personalInfo: false,
      workExperience: false,
      education: false,
      skills: false,
      projects: false,
      certifications: false,
      languages: false,
      additionalSections: false,
      content: false,
      [section]: true,
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
        if (!token) {
          toast.error("Authentication session not found.");
          return;
        }

        if (contentType === "cover_letter") {
          const [coverLetterResponse, profileResponse] = await Promise.all([
            fetch("/api/documents/cover-letters/latest", {
              headers: { Authorization: `Bearer ${token}` },
              cache: "no-store",
            }),
            fetch("/api/profile", {
              headers: { Authorization: `Bearer ${token}` },
            }),
          ]);

          let parsedCoverLetterData: any = {};
          if (coverLetterResponse.ok) {
            const rawData = await coverLetterResponse.json();
            if (rawData?.content && typeof rawData.content === "string") {
              try {
                parsedCoverLetterData = JSON.parse(rawData.content);
              } catch (e) {
                console.error("Failed to parse cover letter content:", e);
                // Handle cases where content might not be JSON
                parsedCoverLetterData = { body: rawData.content };
              }
            } else if (rawData?.content) {
              // Handle cases where content is already an object
              parsedCoverLetterData = rawData.content;
            }
          }

          let profileData: any = {};
          if (profileResponse.ok) profileData = await profileResponse.json();

          setPersonalInfo({
            fullName:
              parsedCoverLetterData?.personal_info?.fullName ||
              `${profileData?.first_name || ""} ${
                profileData?.last_name || ""
              }`.trim() ||
              profileData?.name ||
              "",
            email:
              parsedCoverLetterData?.personal_info?.email ||
              profileData?.email ||
              "",
            phone:
              parsedCoverLetterData?.personal_info?.phone ||
              profileData?.phone ||
              "",
            address:
              parsedCoverLetterData?.personal_info?.address ||
              profileData?.address ||
              "",
            linkedin:
              parsedCoverLetterData?.personal_info?.linkedin ||
              profileData?.linkedin ||
              "",
            website: parsedCoverLetterData?.personal_info?.website || "",
            summary:
              parsedCoverLetterData?.personal_info?.summary ||
              profileData?.profile_headline ||
              "",
          });

          setEditedCompanyName(
            parsedCoverLetterData?.company_name || companyName
          );
          setEditedJobTitle(parsedCoverLetterData?.job_title || jobTitle);
          setRecipientName(parsedCoverLetterData?.recipient_name || "");
          setRecipientTitle(parsedCoverLetterData?.recipient_title || "");
          setEditedContent(parsedCoverLetterData?.body || "");
        } else if (contentType === "resume") {
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

            // EDIT: The data loading logic is now more robust. It prioritizes the comprehensive
            // /api/resume endpoint as the source of truth and uses /api/profile only as a fallback.
            // This prevents race conditions where the faster but less complete profile data could
            // overwrite the more detailed resume data.
            const finalPersonalInfo = {
              fullName:
                resumeData?.personalInfo?.name ||
                `${profileData?.first_name || ""} ${
                  profileData?.last_name || ""
                }`.trim() ||
                profileData?.name ||
                "",
              email:
                resumeData?.personalInfo?.email || profileData?.email || "",
              phone:
                resumeData?.personalInfo?.phone || profileData?.phone || "",
              address:
                resumeData?.personalInfo?.location ||
                profileData?.address ||
                "",
              linkedin:
                resumeData?.personalInfo?.linkedin ||
                profileData?.linkedin ||
                "",
              website: resumeData?.personalInfo?.website || "", // Profile doesn't have this
              summary:
                resumeData?.personalInfo?.summary ||
                profileData?.profile_headline ||
                "",
            };
            setPersonalInfo(finalPersonalInfo);
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
                summary: resumeData.personalInfo.summary || prev.summary,
              }));
            }

            // Populate work experience
            if (resumeData.experience && resumeData.experience.length > 0) {
              setWorkExperience(
                resumeData.experience.map((exp: any) => ({
                  id: exp.id || crypto.randomUUID(),
                  title: exp.jobTitle || "",
                  company: exp.company || "",
                  startYear: exp.dates?.start || "",
                  endYear: exp.dates?.end || "",
                  description: exp.description || "",
                }))
              );
            }

            // Populate education
            if (resumeData.education && resumeData.education.length > 0) {
              setEducation(
                resumeData.education.map((edu: any) => ({
                  id: edu.id || crypto.randomUUID(),
                  degree: edu.degree || "",
                  school: edu.institution || "",
                  year: edu.dates?.end || edu.dates?.start || "",
                  description: edu.description || "",
                }))
              );
            }

            // Populate skills
            if (resumeData.skills && resumeData.skills.length > 0) {
              setSkillsArray(resumeData.skills);
              setSkills(resumeData.skills.join(", "));
            }

            if (resumeData.projects && resumeData.projects.length > 0) {
              setProjects(
                resumeData.projects.map((p: any) => ({
                  ...p,
                  technologies: (p.technologies || []).join(", "),
                }))
              );
            }
            if (
              resumeData.certifications &&
              resumeData.certifications.length > 0
            ) {
              setCertifications(resumeData.certifications);
            }
            if (resumeData.languages && resumeData.languages.length > 0) {
              setLanguages(resumeData.languages);
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
        }
      } catch (error) {
        console.error("Error fetching user data:", error);
        toast.error("Could not load personal information");
      } finally {
        setIsLoadingUserData(false);
      }
    };

    if (open) {
      fetchUserData();
    }
  }, [open, getToken, contentType]);

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
          summary: "",
        });
        setWorkExperience([
          {
            id: "",
            title: "",
            company: "",
            startYear: "",
            endYear: "",
            description: "",
          },
        ]);
        setEducation([
          { id: "", degree: "", school: "", year: "", description: "" },
        ]);
        setSkillsArray([]);
        setSkills("");
        setAdditionalSections("");
        setProjects([{ name: "", description: "", technologies: "", url: "" }]);
        setCertifications([
          { name: "", issuing_organization: "", date_issued: "" },
        ]);
        setLanguages([{ name: "", proficiency: "" }]);
        setIsLoadingUserData(false);
      }
    }
  }, [open]);

  // EDIT: Simplified handlePreview to remove sessionStorage dependency for resumes.
  // The preview page is now always responsible for fetching its own data from the database.
  const handlePreview = () => {
    const previewUrl = `/preview?type=${contentType}&style=${selectedStyle}${
      contentId ? `&content_id=${contentId}` : ""
    }`;

    const newWindow = window.open(previewUrl, "_blank", "noopener,noreferrer");

    if (newWindow) {
      newWindow.focus();
      toast.success("Preview opened in a new tab.");
    } else {
      toast.error("Please allow pop-ups to view the preview.");
    }
  };

  const selectedStyleData =
    PDF_STYLES.find((s) => s.key === selectedStyle) || PDF_STYLES[0];

  // Check if content is valid - either free-form text or structured data
  const isContentValid = React.useMemo(() => {
    // For cover letters, we only need the body text to be valid.
    if (contentType === "cover_letter") {
      return editedContent && editedContent.trim().length > 0;
    }

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

      const hasProjects = projects.some(
        (p) => p.name.trim() || p.description.trim()
      );
      const hasCerts = certifications.some((c) => c.name.trim());
      const hasLangs = languages.some((l) => l.name.trim());

      return (
        hasPersonalInfo ||
        hasWorkExperience ||
        hasEducation ||
        hasSkills ||
        hasProjects ||
        hasCerts ||
        hasLangs
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
    projects,
    certifications,
    languages,
  ]);

  const handleSaveCoverLetter = async () => {
    if (isSaving || !isContentValid) return;

    setIsSaving(true);
    toast.loading("Saving your changes...", { id: "save-toast" });

    try {
      const token = await getToken();
      if (!token) {
        toast.error("Authentication session not found.", { id: "save-toast" });
        setIsSaving(false);
        return;
      }

      const coverLetterPayload = {
        company_name: editedCompanyName,
        job_title: editedJobTitle,
        recipient_name: recipientName,
        recipient_title: recipientTitle,
        body: editedContent,
        personal_info: {
          fullName: personalInfo.fullName,
          email: personalInfo.email,
          phone: personalInfo.phone,
          linkedin: personalInfo.linkedin,
          website: personalInfo.website,
        },
      };

      const requestBody = {
        content: JSON.stringify(coverLetterPayload),
      };

      const response = await fetch("/api/documents/cover-letters/latest", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || "Failed to save the cover letter."
        );
      }

      toast.success("Cover letter saved successfully!", { id: "save-toast" });
    } catch (error) {
      console.error("Error saving cover letter:", error);
      const message =
        error instanceof Error ? error.message : "An unknown error occurred.";
      toast.error(message, { id: "save-toast" });
    } finally {
      setIsSaving(false);
    }
  };

  // EDIT: Added a new save handler specifically for resumes.
  const handleSaveResume = async () => {
    if (isSaving || !isContentValid) return;

    setIsSaving(true);
    toast.loading("Saving your resume...", { id: "save-resume-toast" });

    try {
      const token = await getToken();
      if (!token) {
        toast.error("Authentication session not found.", {
          id: "save-resume-toast",
        });
        setIsSaving(false);
        return;
      }

      const resumePayload = {
        personalInfo: {
          name: personalInfo.fullName,
          email: personalInfo.email,
          phone: personalInfo.phone,
          linkedin: personalInfo.linkedin,
          location: personalInfo.address,
          summary: personalInfo.summary,
        },
        experience: workExperience
          .filter((exp) => exp.title || exp.company)
          .map((exp) => ({
            id: exp.id || crypto.randomUUID(),
            jobTitle: exp.title,
            company: exp.company,
            dates: { start: exp.startYear, end: exp.endYear },
            description: exp.description,
          })),
        education: education
          .filter((edu) => edu.degree || edu.school)
          .map((edu) => ({
            id: edu.id || crypto.randomUUID(),
            degree: edu.degree,
            institution: edu.school,
            dates: edu.year,
            description: edu.description,
          })),
        skills: skillsArray.filter((s) => s.trim()),
        projects: projects
          .filter((p) => p.name)
          .map((p) => ({
            title: p.name,
            description: p.description,
            technologies: p.technologies,
            url: p.url,
          })),
        certifications: certifications.filter((c) => c.name),
        languages: languages.filter((l) => l.name),
      };

      const response = await fetch("/api/resume/full", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(resumePayload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || "Failed to save the resume.");
      }

      toast.success("Resume saved successfully!", { id: "save-resume-toast" });
    } catch (error) {
      console.error("Error saving resume:", error);
      const message =
        error instanceof Error ? error.message : "An unknown error occurred.";
      toast.error(message, { id: "save-resume-toast" });
    } finally {
      setIsSaving(false);
    }
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

  // Helper functions to manage new structured sections
  const handleProjectChange = (
    index: number,
    field: keyof (typeof projects)[0],
    value: string
  ) => {
    const updated = [...projects];
    updated[index][field] = value;
    setProjects(updated);
  };

  const addProject = () => {
    setProjects([
      ...projects,
      { name: "", description: "", technologies: "", url: "" },
    ]);
  };

  const removeProject = (index: number) => {
    setProjects(projects.filter((_, i) => i !== index));
  };

  const handleCertificationChange = (
    index: number,
    field: keyof (typeof certifications)[0],
    value: string
  ) => {
    const updated = [...certifications];
    updated[index][field] = value;
    setCertifications(updated);
  };

  const addCertification = () => {
    setCertifications([
      ...certifications,
      { name: "", issuing_organization: "", date_issued: "" },
    ]);
  };

  const removeCertification = (index: number) => {
    setCertifications(certifications.filter((_, i) => i !== index));
  };

  const handleLanguageChange = (
    index: number,
    field: keyof (typeof languages)[0],
    value: string
  ) => {
    const updated = [...languages];
    updated[index][field] = value;
    setLanguages(updated);
  };

  const addLanguage = () => {
    setLanguages([...languages, { name: "", proficiency: "" }]);
  };

  const removeLanguage = (index: number) => {
    setLanguages(languages.filter((_, i) => i !== index));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        hideCloseButton
        className="max-w-[95vw] sm:max-w-6xl max-h-[92vh] sm:max-h-[95vh] w-[95vw] h-[92vh] sm:w-[95vw] sm:h-[95vh] flex flex-col !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 !border !border-gray-200 dark:!border-white/8 shadow-2xl rounded-2xl sm:rounded-3xl overflow-hidden p-0"
      >
        {/* --- UI FIX: Header structure corrected for proper responsive button visibility --- */}
        <div className="flex-shrink-0 !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 !border-b !border-gray-200 dark:!border-white/8 p-3 sm:p-5 relative z-10">
          {/* Mobile Header */}
          <div className="sm:hidden flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="w-10 h-10 rounded-xl !bg-blue-100 !border !border-blue-200 shadow-lg flex items-center justify-center backdrop-blur-sm flex-shrink-0 dark:!bg-blue-500/20 dark:!border-blue-500/40">
                <FileText className="h-5 w-5 !text-blue-600 dark:!text-blue-400" />
              </div>
              <div className="min-w-0 flex-1">
                <DialogTitle className="text-lg font-bold text-gray-900 dark:text-gray-100 leading-tight">
                  {contentType === "cover_letter" ? "Cover Letter" : "Resume"}
                </DialogTitle>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5 leading-tight">
                  Generator
                </p>
              </div>
            </div>
            {/* This is the close button for MOBILE ONLY */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onOpenChange(false)}
              className="h-9 w-9 rounded-lg transition-all duration-300 hover:scale-105 !bg-gray-100 !border !border-gray-200 hover:!bg-gray-200 dark:!bg-background/60 dark:!border-white/8 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:hover:!bg-background/80 flex-shrink-0"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </Button>
          </div>

          {/* Mobile Actions Row */}
          <div className="flex sm:hidden items-center justify-center gap-2 mt-3 pt-3 !border-t !border-gray-200 dark:!border-white/8">
            <Button
              onClick={
                contentType === "resume"
                  ? handleSaveResume
                  : handleSaveCoverLetter
              }
              disabled={isSaving || !isContentValid}
              size="sm"
              variant="outline"
              // --- UI FIX: Explicitly prevent this button from growing. ---
              className="flex-grow-0 flex items-center gap-2 text-sm px-4 h-9 rounded-lg disabled:opacity-50 font-semibold transition-all duration-300"
            >
              {isSaving ? (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              <span>{isSaving ? "Saving..." : "Save"}</span>
            </Button>
            <Button
              onClick={handlePreview}
              disabled={isSaving || !isContentValid}
              size="sm"
              // --- UI FIX: This button will now correctly grow to fill the remaining space. ---
              className="flex-1 flex items-center gap-2 !bg-primary hover:!bg-primary/90 text-primary-foreground text-sm px-4 h-9 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-all duration-300 hover:scale-105 disabled:hover:scale-100"
            >
              <ExternalLink className="h-4 w-4" />
              <span>Preview</span>
            </Button>
          </div>

          {/* Desktop Header */}
          <div className="hidden sm:flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl !bg-blue-100 !border !border-blue-200 shadow-lg flex items-center justify-center backdrop-blur-sm dark:!bg-blue-500/20 dark:!border-blue-500/40">
                <FileText className="h-6 w-6 !text-blue-600 dark:!text-blue-400" />
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
            <div className="flex items-center gap-3">
              <Button
                onClick={
                  contentType === "resume"
                    ? handleSaveResume
                    : handleSaveCoverLetter
                }
                disabled={isSaving || !isContentValid}
                size="sm"
                variant="outline"
                className="flex items-center gap-2 text-sm px-5 h-10 rounded-xl disabled:opacity-50 font-semibold transition-all duration-300 hover:scale-105"
              >
                {isSaving ? (
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                <span>{isSaving ? "Saving..." : "Save"}</span>
              </Button>
              <Button
                onClick={handlePreview}
                disabled={isSaving || !isContentValid}
                size="sm"
                className="flex items-center gap-2 !bg-primary hover:!bg-primary/90 text-primary-foreground text-sm px-5 h-10 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-all duration-300 hover:scale-105 disabled:hover:scale-100"
              >
                <ExternalLink className="h-4 w-4" />
                <span>Preview & Download</span>
              </Button>
              {/* This is the close button for DESKTOP ONLY */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onOpenChange(false)}
                className="h-10 w-10 rounded-xl transition-all duration-300 hover:scale-105 !bg-gray-100 !border !border-gray-200 hover:!bg-gray-200 dark:!bg-background/60 dark:!border-white/8 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:hover:!bg-background/80 ml-2"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Close</span>
              </Button>
            </div>
          </div>
        </div>
        {/* --- END UI FIX --- */}

        {/* Navigation */}
        <div className="flex-shrink-0 !border-b !border-gray-200 dark:!border-white/8 !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150">
          {/* Mobile Navigation - Collapsible */}
          <div className="sm:hidden px-5 py-4">
            <button
              onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
              className="flex items-center justify-between w-full p-4 rounded-xl !bg-white dark:!bg-background/80 backdrop-blur-md !border !border-gray-200 dark:!border-white/8 hover:!bg-gray-50 dark:hover:!bg-background/90 transition-all duration-300 hover:scale-[1.02] shadow-lg hover:shadow-xl"
            >
              <div className="flex items-center gap-3">
                {/* Show current section icon */}
                {contentType === "cover_letter" &&
                  expandedSections.personalInfo && (
                    <>
                      <Briefcase className="h-4 w-4 text-foreground" />
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        Job Details
                      </span>
                    </>
                  )}
                {contentType === "resume" && expandedSections.personalInfo && (
                  <>
                    <User className="h-4 w-4 text-foreground" />
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
                {expandedSections.projects && (
                  <>
                    <Lightbulb className="h-4 w-4 text-yellow-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Projects
                    </span>
                  </>
                )}
                {expandedSections.certifications && (
                  <>
                    <Award className="h-4 w-4 text-blue-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Certifications
                    </span>
                  </>
                )}
                {expandedSections.languages && (
                  <>
                    <Globe className="h-4 w-4 text-pink-600" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      Languages
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
              <div className="mt-3 p-3 !bg-white dark:!bg-background/80 rounded-xl !border !border-gray-200 dark:!border-white/8 shadow-xl backdrop-blur-md space-y-2">
                {/* Cover Letter Job Details */}
                {contentType === "cover_letter" && (
                  <button
                    onClick={() => {
                      toggleSection("personalInfo");
                      setIsMobileNavOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                      expandedSections.personalInfo
                        ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-md dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700/50"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
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
                          ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-md dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700/50"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
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
                          ? "bg-green-50 text-green-700 border border-green-200 shadow-md dark:bg-green-900/30 dark:text-green-300 dark:border-green-700/50"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
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
                          ? "bg-purple-50 text-purple-700 border border-purple-200 shadow-md dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-700/50"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
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
                          ? "bg-orange-50 text-orange-700 border border-orange-200 shadow-md dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-700/50"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
                      }`}
                    >
                      <Sparkles className="h-4 w-4 flex-shrink-0" />
                      Skills & Competencies
                    </button>

                    <button
                      onClick={() => {
                        toggleSection("projects");
                        setIsMobileNavOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                        expandedSections.projects
                          ? "bg-yellow-50 text-yellow-700 border border-yellow-200 shadow-md dark:bg-yellow-900/30 dark:text-yellow-300 dark:border-yellow-700/50"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
                      }`}
                    >
                      <Lightbulb className="h-4 w-4 flex-shrink-0" />
                      Projects
                    </button>

                    <button
                      onClick={() => {
                        toggleSection("certifications");
                        setIsMobileNavOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                        expandedSections.certifications
                          ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-md dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700/50"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
                      }`}
                    >
                      <Award className="h-4 w-4 flex-shrink-0" />
                      Certifications
                    </button>

                    <button
                      onClick={() => {
                        toggleSection("languages");
                        setIsMobileNavOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                        expandedSections.languages
                          ? "bg-pink-50 text-pink-700 border border-pink-200 shadow-md dark:bg-pink-900/30 dark:text-pink-300 dark:border-pink-700/50"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
                      }`}
                    >
                      <Globe className="h-4 w-4 flex-shrink-0" />
                      Languages
                    </button>
                  </>
                )}

                {contentType === "cover_letter" && (
                  <button
                    onClick={() => {
                      toggleSection("content");
                      setIsMobileNavOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.02] ${
                      expandedSections.content
                        ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-md dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700/50"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-md"
                    }`}
                  >
                    <Edit3 className="h-4 w-4 flex-shrink-0" />
                    Cover Letter Content
                  </button>
                )}
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
                      ? "border-blue-500 text-blue-600 bg-blue-50 shadow-lg dark:border-blue-400 dark:text-blue-400 dark:bg-blue-500/20"
                      : "border-transparent text-gray-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-lg dark:text-gray-400 dark:hover:text-blue-400 dark:hover:border-blue-500/50 dark:hover:bg-blue-500/10"
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
                        ? "border-blue-500 text-blue-600 bg-blue-50 shadow-lg dark:border-blue-400 dark:text-blue-400 dark:bg-blue-500/20"
                        : "border-transparent text-gray-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-lg dark:text-gray-400 dark:hover:text-blue-400 dark:hover:border-blue-500/50 dark:hover:bg-blue-500/10"
                    }`}
                  >
                    <User className="h-4 w-4 flex-shrink-0" />
                    <span>Personal</span>
                  </button>

                  <button
                    onClick={() => toggleSection("workExperience")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.workExperience
                        ? "border-green-500 text-green-700 bg-green-50 shadow-lg dark:bg-green-900/30 dark:text-green-300 dark:border-green-400"
                        : "border-transparent text-muted-foreground hover:text-green-700 hover:border-green-500 hover:bg-green-50 hover:shadow-lg dark:hover:text-green-300 dark:hover:bg-green-900/30 dark:hover:border-green-400"
                    }`}
                  >
                    <Briefcase className="h-4 w-4 flex-shrink-0" />
                    <span>Work</span>
                  </button>

                  <button
                    onClick={() => toggleSection("education")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.education
                        ? "border-purple-500 text-purple-700 bg-purple-50 shadow-lg dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-400"
                        : "border-transparent text-muted-foreground hover:text-purple-700 hover:border-purple-500 hover:bg-purple-50 hover:shadow-lg dark:hover:text-purple-300 dark:hover:bg-purple-900/30 dark:hover:border-purple-400"
                    }`}
                  >
                    <GraduationCap className="h-4 w-4 flex-shrink-0" />
                    <span>Education</span>
                  </button>

                  <button
                    onClick={() => toggleSection("skills")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.skills
                        ? "border-orange-500 text-orange-700 bg-orange-50 shadow-lg dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-400"
                        : "border-transparent text-muted-foreground hover:text-orange-700 hover:border-orange-500 hover:bg-orange-50 hover:shadow-lg dark:hover:text-orange-300 dark:hover:bg-orange-900/30 dark:hover:border-orange-400"
                    }`}
                  >
                    <Sparkles className="h-4 w-4 flex-shrink-0" />
                    <span>Skills</span>
                  </button>

                  <button
                    onClick={() => toggleSection("projects")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.projects
                        ? "border-yellow-500 text-yellow-700 bg-yellow-50 shadow-lg dark:bg-yellow-900/30 dark:text-yellow-300 dark:border-yellow-400"
                        : "border-transparent text-muted-foreground hover:text-yellow-700 hover:border-yellow-500 hover:bg-yellow-50 hover:shadow-lg dark:hover:text-yellow-300 dark:hover:bg-yellow-900/30 dark:hover:border-yellow-400"
                    }`}
                  >
                    <Lightbulb className="h-4 w-4 flex-shrink-0" />
                    <span>Projects</span>
                  </button>
                  <button
                    onClick={() => toggleSection("certifications")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.certifications
                        ? "border-blue-500 text-blue-700 bg-blue-50 shadow-lg dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-400"
                        : "border-transparent text-muted-foreground hover:text-blue-700 hover:border-blue-500 hover:bg-blue-50 hover:shadow-lg dark:hover:text-blue-300 dark:hover:bg-blue-900/30 dark:hover:border-blue-400"
                    }`}
                  >
                    <Award className="h-4 w-4 flex-shrink-0" />
                    <span>Certifications</span>
                  </button>
                  <button
                    onClick={() => toggleSection("languages")}
                    className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                      expandedSections.languages
                        ? "border-pink-500 text-pink-700 bg-pink-50 shadow-lg dark:bg-pink-900/30 dark:text-pink-300 dark:border-pink-400"
                        : "border-transparent text-muted-foreground hover:text-pink-700 hover:border-pink-500 hover:bg-pink-50 hover:shadow-lg dark:hover:text-pink-300 dark:hover:bg-pink-900/30 dark:hover:border-pink-400"
                    }`}
                  >
                    <Globe className="h-4 w-4 flex-shrink-0" />
                    <span>Languages</span>
                  </button>
                </>
              )}

              {contentType === "cover_letter" && (
                <button
                  onClick={() => toggleSection("content")}
                  className={`flex items-center gap-2 px-5 py-3 border-b-3 font-semibold text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-xl hover:scale-105 ${
                    expandedSections.content
                      ? "border-blue-500 text-blue-600 bg-blue-50 shadow-lg dark:border-blue-400 dark:text-blue-400 dark:bg-blue-500/20"
                      : "border-transparent text-gray-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-lg dark:text-gray-400 dark:hover:text-blue-400 dark:hover:border-blue-500/50 dark:hover:bg-blue-500/10"
                  }`}
                >
                  <Edit3 className="h-4 w-4 flex-shrink-0" />
                  <span>Content</span>
                </button>
              )}
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
            <div className="flex-1 p-3 sm:p-6">
              <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
                {/* Cover Letter Job Details */}
                {contentType === "cover_letter" &&
                  expandedSections.personalInfo && (
                    <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                        <Briefcase className="h-4 w-4 sm:h-5 sm:w-5 text-foreground flex-shrink-0" />
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
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                            Recipient Name (Optional)
                          </Label>
                          <Input
                            placeholder="e.g., Jane Doe"
                            value={recipientName}
                            onChange={(e) => setRecipientName(e.target.value)}
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                        <div>
                          <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                            Recipient Title (Optional)
                          </Label>
                          <Input
                            placeholder="e.g., Hiring Manager"
                            value={recipientTitle}
                            onChange={(e) => setRecipientTitle(e.target.value)}
                            className="w-full h-10 sm:h-11 text-sm sm:text-base px-3 sm:px-4"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                {/* Personal Information Section */}
                {contentType === "resume" && expandedSections.personalInfo && (
                  <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <User className="h-4 w-4 sm:h-5 sm:w-5 text-foreground flex-shrink-0" />
                      <span className="truncate">Personal Information</span>
                      {isLoadingUserData && (
                        <div className="ml-auto flex items-center gap-2 text-xs text-foreground">
                          <div className="w-3 h-3 border border-foreground border-t-transparent rounded-full animate-spin"></div>
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
                    <div className="mt-4 sm:mt-6">
                      <Label className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 sm:mb-2 block">
                        Professional Summary
                      </Label>
                      <Textarea
                        placeholder="Write a brief summary of your career objectives and key qualifications..."
                        value={personalInfo.summary}
                        onChange={(e) =>
                          setPersonalInfo({
                            ...personalInfo,
                            summary: e.target.value,
                          })
                        }
                        rows={4}
                        className="w-full text-sm sm:text-base px-3 sm:px-4"
                      />
                    </div>
                  </div>
                )}

                {/* Work Experience Section */}
                {contentType === "resume" &&
                  expandedSections.workExperience && (
                    <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                        <Briefcase className="h-4 w-4 sm:h-5 sm:w-5 text-green-600 flex-shrink-0" />
                        <span className="truncate">Work Experience</span>
                      </h2>
                      <div className="space-y-4 sm:space-y-6">
                        {workExperience.map((job, index) => (
                          <div
                            key={job.id || index}
                            className="relative !border !border-gray-200 dark:!border-white/20 rounded-xl p-4 sm:p-6 !bg-gray-50 dark:!bg-background/70 backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-200 group"
                          >
                            {/* Header with improved styling */}
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center shadow-lg">
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
                                className="resize-none text-sm sm:text-base px-3 sm:px-4 py-2.5 sm:py-3 focus:ring-2 focus:ring-primary/20 focus:border-primary/40 transition-all duration-200 cursor-text"
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
                                id: crypto.randomUUID(),
                                title: "",
                                company: "",
                                startYear: "",
                                endYear: "",
                                description: "",
                              },
                            ])
                          }
                          variant="outline"
                          className="w-full border-dashed border-2 h-11 sm:h-12 text-gray-600 hover:text-foreground hover:border-gray-400 text-sm sm:text-base font-medium touch-manipulation"
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
                  <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <GraduationCap className="h-4 w-4 sm:h-5 sm:w-5 text-purple-600 flex-shrink-0" />
                      <span className="truncate">Education</span>
                    </h2>
                    <div className="space-y-6">
                      {education.map((edu, index) => (
                        <div
                          key={edu.id || index}
                          className="!border !border-gray-200 dark:!border-white/20 rounded-xl p-4 sm:p-6 !bg-gray-50 dark:!bg-background/70 backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-200 group"
                        >
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center shadow-lg">
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
                              className="resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary/40 transition-all duration-200 cursor-text"
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
                              id: crypto.randomUUID(),
                              degree: "",
                              school: "",
                              year: "",
                              description: "",
                            },
                          ])
                        }
                        variant="outline"
                        className="w-full border-dashed border-2 h-12 text-gray-600 hover:text-foreground hover:border-gray-400"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add Another Education
                      </Button>
                    </div>
                  </div>
                )}

                {/* Skills Section */}
                {contentType === "resume" && expandedSections.skills && (
                  <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
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
                              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-medium !bg-white dark:!bg-background/70 backdrop-blur-md text-gray-700 dark:text-gray-200 !border !border-gray-200 dark:!border-white/40 hover:!bg-gray-50 dark:hover:!bg-background/80 hover:!border-gray-300 dark:hover:!border-white/50 shadow-sm hover:shadow-md transition-all duration-200 group"
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
                        className="resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary/40 transition-all duration-200 cursor-text text-xs"
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

                {contentType === "resume" && expandedSections.projects && (
                  <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <Lightbulb className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-600 flex-shrink-0" />
                      <span className="truncate">Projects</span>
                    </h2>
                    <div className="space-y-6">
                      {projects.map((project, index) => (
                        <div
                          key={index}
                          className="relative !border !border-gray-200 dark:!border-white/20 rounded-xl p-4 sm:p-6 !bg-gray-50 dark:!bg-background/70 backdrop-blur-md shadow-lg group"
                        >
                          <div className="flex justify-end mb-2">
                            {projects.length > 1 && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => removeProject(index)}
                                className="text-red-500 hover:text-red-700 h-8 w-8 p-0 opacity-50 group-hover:opacity-100"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="sm:col-span-2">
                              <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                Project Name
                              </Label>
                              <Input
                                placeholder="e.g., Personal Portfolio"
                                value={project.name}
                                onChange={(e) =>
                                  handleProjectChange(
                                    index,
                                    "name",
                                    e.target.value
                                  )
                                }
                              />
                            </div>
                            <div>
                              <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                Project URL
                              </Label>
                              <Input
                                placeholder="e.g., https://my-portfolio.com"
                                value={project.url}
                                onChange={(e) =>
                                  handleProjectChange(
                                    index,
                                    "url",
                                    e.target.value
                                  )
                                }
                              />
                            </div>
                            <div>
                              <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                Technologies Used
                              </Label>
                              <Input
                                placeholder="e.g., React, Next.js, Vercel"
                                value={project.technologies}
                                onChange={(e) =>
                                  handleProjectChange(
                                    index,
                                    "technologies",
                                    e.target.value
                                  )
                                }
                              />
                            </div>
                            <div className="sm:col-span-2">
                              <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                Description
                              </Label>
                              <Textarea
                                placeholder="Describe your project..."
                                value={project.description}
                                onChange={(e) =>
                                  handleProjectChange(
                                    index,
                                    "description",
                                    e.target.value
                                  )
                                }
                                rows={3}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                      <Button
                        onClick={addProject}
                        variant="outline"
                        className="w-full border-dashed border-2 h-12 text-gray-600 hover:text-foreground hover:border-gray-400"
                      >
                        <Plus className="h-4 w-4 mr-2" /> Add Project
                      </Button>
                    </div>
                  </div>
                )}

                {contentType === "resume" &&
                  expandedSections.certifications && (
                    <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                        <Award className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 flex-shrink-0" />
                        <span className="truncate">Certifications</span>
                      </h2>
                      <div className="space-y-6">
                        {certifications.map((cert, index) => (
                          <div
                            key={index}
                            className="relative !border !border-gray-200 dark:!border-white/20 rounded-xl p-4 sm:p-6 !bg-gray-50 dark:!bg-background/70 backdrop-blur-md shadow-lg group"
                          >
                            <div className="flex justify-end mb-2">
                              {certifications.length > 1 && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => removeCertification(index)}
                                  className="text-red-500 hover:text-red-700 h-8 w-8 p-0 opacity-50 group-hover:opacity-100"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                              <div>
                                <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                  Certificate Name
                                </Label>
                                <Input
                                  placeholder="e.g., AWS Certified Developer"
                                  value={cert.name}
                                  onChange={(e) =>
                                    handleCertificationChange(
                                      index,
                                      "name",
                                      e.target.value
                                    )
                                  }
                                />
                              </div>
                              <div>
                                <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                  Issuing Organization
                                </Label>
                                <Input
                                  placeholder="e.g., Amazon Web Services"
                                  value={cert.issuing_organization}
                                  onChange={(e) =>
                                    handleCertificationChange(
                                      index,
                                      "issuing_organization",
                                      e.target.value
                                    )
                                  }
                                />
                              </div>
                              <div className="sm:col-span-2">
                                <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                  Date Issued
                                </Label>
                                <Input
                                  placeholder="e.g., June 2023"
                                  value={cert.date_issued}
                                  onChange={(e) =>
                                    handleCertificationChange(
                                      index,
                                      "date_issued",
                                      e.target.value
                                    )
                                  }
                                />
                              </div>
                            </div>
                          </div>
                        ))}
                        <Button
                          onClick={addCertification}
                          variant="outline"
                          className="w-full border-dashed border-2 h-12 text-gray-600 hover:text-foreground hover:border-gray-400"
                        >
                          <Plus className="h-4 w-4 mr-2" /> Add Certification
                        </Button>
                      </div>
                    </div>
                  )}

                {contentType === "resume" && expandedSections.languages && (
                  <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                      <Globe className="h-4 w-4 sm:h-5 sm:w-5 text-pink-600 flex-shrink-0" />
                      <span className="truncate">Languages</span>
                    </h2>
                    <div className="space-y-6">
                      {languages.map((lang, index) => (
                        <div
                          key={index}
                          className="relative !border !border-gray-200 dark:!border-white/20 rounded-xl p-4 sm:p-6 !bg-gray-50 dark:!bg-background/70 backdrop-blur-md shadow-lg group"
                        >
                          <div className="flex justify-end mb-2">
                            {languages.length > 1 && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => removeLanguage(index)}
                                className="text-red-500 hover:text-red-700 h-8 w-8 p-0 opacity-50 group-hover:opacity-100"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                              <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                Language
                              </Label>
                              <Input
                                placeholder="e.g., English"
                                value={lang.name}
                                onChange={(e) =>
                                  handleLanguageChange(
                                    index,
                                    "name",
                                    e.target.value
                                  )
                                }
                              />
                            </div>
                            <div>
                              <Label className="text-sm font-medium text-gray-700 dark:text-white mb-2 block">
                                Proficiency
                              </Label>
                              <Input
                                placeholder="e.g., Native, Fluent, Conversational"
                                value={lang.proficiency}
                                onChange={(e) =>
                                  handleLanguageChange(
                                    index,
                                    "proficiency",
                                    e.target.value
                                  )
                                }
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                      <Button
                        onClick={addLanguage}
                        variant="outline"
                        className="w-full border-dashed border-2 h-12 text-gray-600 hover:text-foreground hover:border-gray-400"
                      >
                        <Plus className="h-4 w-4 mr-2" /> Add Language
                      </Button>
                    </div>
                  </div>
                )}

                {contentType === "resume" &&
                  expandedSections.additionalSections && (
                    <div className="hidden">
                      {/* This section is now replaced by structured fields */}
                    </div>
                  )}

                {expandedSections.content && contentType === "cover_letter" && (
                  <div className="!bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
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

I am writing to express my strong interest in the ${
                        editedJobTitle || "[Job Title]"
                      } position at ${
                        editedCompanyName || "[Company Name]"
                      }. With my background in [Your Field] and [X] years of experience, I am confident that I would be a valuable addition to your team.

In my previous role at [Previous Company], I successfully [Key Achievement]. This experience has equipped me with [Relevant Skills] that directly align with the requirements of this position.

I am particularly drawn to [Company Name] because [Reason for Interest in Company]. I am excited about the opportunity to contribute to [Specific Project/Goal] and help drive [Company Objective].

Thank you for considering my application. I look forward to discussing how my skills and experience can contribute to your team's success.

Sincerely,
[Your Name]`}
                      rows={16}
                      data-scrollable="true"
                      className="resize-none text-sm sm:text-base px-3 sm:px-4 py-2.5 sm:py-3 leading-relaxed min-h-[300px] sm:min-h-[400px] focus:ring-2 focus:ring-primary/20 focus:border-primary/40 transition-all duration-200 cursor-text scrollbar-thin !bg-white dark:!bg-background/80"
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
