"use client";

import { PDFGenerationDialog } from "@/components/chat/pdf-generation-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@clerk/nextjs";
import { FileUp, Loader2, Upload, FileText } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { toast } from "sonner";

export default function OnboardingPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [isUploading, setIsUploading] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [parsedData, setParsedData] = useState<any>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string>("");
  const [isPDFDialogOpen, setIsPDFDialogOpen] = useState(false);
  const [resumeContent, setResumeContent] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    // Validate file type
    const validTypes = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"];
    if (!validTypes.includes(file.type)) {
      toast.error("Please upload a PDF, Word document, or text file");
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error("File size must be less than 10MB");
      return;
    }

    setUploadedFileName(file.name);
    setIsUploading(true);

    try {
      // Step 1: Upload the file
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", file.name);
      formData.append("auto_update_profile", "true");

      const token = await getToken();
      const uploadResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/cv-upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text();
        console.error("Upload failed:", errorText);
        throw new Error("Failed to upload CV");
      }

      const uploadData = await uploadResponse.json();
      console.log("Upload successful:", uploadData);

      // Step 2: Parse the CV
      setIsUploading(false);
      setIsParsing(true);
      toast.success("CV uploaded! Processing your information...");

      // Use the extracted info from the upload response
      let parsedInfo;
      if (uploadData.extracted_info) {
        parsedInfo = uploadData.extracted_info;
      } else if (uploadData.document) {
        // If no extraction, use document content
        parsedInfo = {
          personal_info: {},
          experience: [],
          education: [],
          skills: [],
          summary: uploadData.document.content?.substring(0, 500) || ""
        };
      }
      
      setParsedData(parsedInfo);
      
      // Format the parsed data into resume content
      const formattedResume = formatParsedDataToResume(parsedInfo);
      setResumeContent(formattedResume);
      
      setIsParsing(false);
      toast.success("CV processed successfully!");
      
      // Open PDF dialog immediately after parsing
      setIsPDFDialogOpen(true);
      
    } catch (error) {
      console.error("Error processing CV:", error);
      toast.error("Failed to process your CV. Please try again.");
      setIsUploading(false);
      setIsParsing(false);
    }
  };

  const formatParsedDataToResume = (data: any): string => {
    // Format the parsed data into a resume string while preserving ALL information
    let resume = "";
    
    // Personal Information
    if (data.personal_info) {
      const info = data.personal_info;
      if (info.full_name) resume += `${info.full_name}\n`;
      
      // Contact line
      const contactParts = [];
      if (info.email) contactParts.push(info.email);
      if (info.phone) contactParts.push(info.phone);
      if (info.linkedin) contactParts.push(info.linkedin);
      if (info.website) contactParts.push(info.website);
      if (contactParts.length > 0) {
        resume += contactParts.join(" | ") + "\n";
      }
      
      if (info.address) resume += `${info.address}\n`;
      
      // Professional Summary
      if (info.profile_summary) {
        resume += `\nPROFESSIONAL SUMMARY\n${info.profile_summary}\n`;
      }
      resume += "\n";
    }
    
    // Work Experience - preserve exact titles and dates
    if (data.experience && data.experience.length > 0) {
      resume += "WORK EXPERIENCE\n";
      data.experience.forEach((exp: any) => {
        if (exp.job_title) resume += `${exp.job_title}`;
        if (exp.company) resume += ` at ${exp.company}`;
        resume += "\n";
        if (exp.duration) resume += `${exp.duration}\n`;
        if (exp.description) {
          // Preserve formatting including bullet points
          resume += `${exp.description}\n`;
        }
        resume += "\n";
      });
    }
    
    // Education - preserve exact degree names and dates
    if (data.education && data.education.length > 0) {
      resume += "EDUCATION\n";
      data.education.forEach((edu: any) => {
        if (edu.degree) resume += `${edu.degree}`;
        if (edu.institution) resume += ` - ${edu.institution}`;
        resume += "\n";
        if (edu.graduation_year) resume += `${edu.graduation_year}\n`;
        if (edu.gpa) resume += `GPA: ${edu.gpa}\n`;
        resume += "\n";
      });
    }
    
    // Projects
    if (data.projects && data.projects.length > 0) {
      resume += "PROJECTS\n";
      data.projects.forEach((proj: any) => {
        if (proj.title) resume += `${proj.title}`;
        if (proj.duration) resume += ` (${proj.duration})`;
        resume += "\n";
        if (proj.description) resume += `${proj.description}\n`;
        if (proj.technologies) resume += `Technologies: ${proj.technologies}\n`;
        if (proj.url || proj.github) {
          if (proj.url) resume += `URL: ${proj.url}\n`;
          if (proj.github) resume += `GitHub: ${proj.github}\n`;
        }
        resume += "\n";
      });
    }
    
    // Skills - preserve all categories
    if (data.skills) {
      resume += "SKILLS\n";
      if (data.skills.technical_skills && data.skills.technical_skills.length > 0) {
        resume += `Technical: ${data.skills.technical_skills.join(", ")}\n`;
      }
      if (data.skills.soft_skills && data.skills.soft_skills.length > 0) {
        resume += `Soft Skills: ${data.skills.soft_skills.join(", ")}\n`;
      }
      if (data.skills.languages && data.skills.languages.length > 0) {
        resume += `Languages: ${data.skills.languages.join(", ")}\n`;
      }
      if (data.skills.certifications && data.skills.certifications.length > 0) {
        resume += `Certifications: ${data.skills.certifications.join(", ")}\n`;
      }
    }
    
    // If raw_text exists and nothing was extracted, use the raw text
    if (data.raw_text && !resume.trim()) {
      resume = data.raw_text;
    }
    
    return resume;
  };

  const completeOnboarding = async () => {
    if (hasCompletedOnboarding) return;
    
    try {
      const token = await getToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/onboarding/complete`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          completed: true,
          cv_uploaded: true 
        }),
      });

      if (response.ok) {
        setHasCompletedOnboarding(true);
        toast.success("Welcome to Job Hacker Bot! Let's find your dream job");
        
        // Small delay to ensure metadata propagates
        setTimeout(() => {
          router.push("/");
        }, 1000);
      }
    } catch (error) {
      console.error("Error completing onboarding:", error);
      toast.error("Failed to complete setup. Please try again.");
    }
  };

  const handlePDFDialogClose = () => {
    setIsPDFDialogOpen(false);
    
    // Check if user has saved data (we assume if they close after opening, they might have saved)
    // We'll prompt them to confirm they want to complete onboarding
    if (!hasCompletedOnboarding && parsedData) {
      // Give them option to complete onboarding after closing dialog
      setTimeout(() => {
        toast(
          <div className="flex flex-col gap-2">
            <p>Have you saved your CV?</p>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  completeOnboarding();
                  toast.dismiss();
                }}
                className="px-3 py-1 bg-primary text-primary-foreground rounded-md text-sm"
              >
                Yes, continue
              </button>
              <button
                onClick={() => {
                  // Reset state to show upload options again
                  setParsedData(null);
                  setResumeContent("");
                  setUploadedFileName("");
                  toast.dismiss();
                }}
                className="px-3 py-1 bg-secondary text-secondary-foreground rounded-md text-sm"
              >
                No, go back
              </button>
            </div>
          </div>,
          {
            duration: 10000,
          }
        );
      }, 100);
    } else if (!hasCompletedOnboarding && !parsedData) {
      // Manual entry was cancelled without any data
      toast.info("Please upload your CV or enter your information to continue");
    }
  };

  const handleManualEntry = () => {
    // Open PDF dialog with empty resume for manual entry
    setResumeContent("");
    setParsedData({}); // Set empty parsed data
    setIsPDFDialogOpen(true);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-2xl bg-background/60 backdrop-blur-xl backdrop-saturate-150 border border-white/8 shadow-2xl rounded-2xl">
        <CardHeader className="text-center space-y-2 pb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-2xl bg-blue-500/20 border border-blue-400/40 flex items-center justify-center shadow-lg">
              <FileText className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold">
            Welcome to Job Hacker Bot
          </CardTitle>
          <CardDescription className="text-base text-muted-foreground">
            Let's set up your profile to personalize your job search experience
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!isParsing && !parsedData && (
            <>
              <div
                className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                  dragActive 
                    ? "border-primary bg-primary/5" 
                    : "border-muted-foreground/25 hover:border-primary/50"
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  id="cv-upload"
                  className="hidden"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileSelect}
                  disabled={isUploading}
                  aria-label="Upload CV file"
                />
                
                <div className="space-y-4">
                  {isUploading ? (
                    <>
                      <Loader2 className="w-12 h-12 mx-auto text-primary animate-spin" />
                      <div>
                        <p className="text-sm font-medium">Uploading {uploadedFileName}...</p>
                        <p className="text-xs text-muted-foreground mt-1">Please wait</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="w-14 h-14 mx-auto rounded-xl bg-primary/10 flex items-center justify-center">
                        <Upload className="w-7 h-7 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">Upload your CV/Resume</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Drag & drop or click to browse
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                          Supports PDF, DOC, DOCX, TXT (Max 10MB)
                        </p>
                      </div>
                      <Button
                        onClick={() => document.getElementById("cv-upload")?.click()}
                        variant="default"
                      >
                        <FileUp className="w-4 h-4 mr-2" />
                        Choose File
                      </Button>
                    </>
                  )}
                </div>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-muted-foreground/20" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">Or</span>
                </div>
              </div>

              <div className="text-center space-y-4">
                <div className="space-y-2">
                  <p className="text-sm font-medium">Don't have a CV ready?</p>
                  <p className="text-xs text-muted-foreground">
                    No worries! You can create one by entering your information manually
                  </p>
                </div>
                <Button
                  onClick={handleManualEntry}
                  variant="outline"
                  className="border-primary/50 hover:bg-primary/10"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Enter Information Manually
                </Button>
              </div>
            </>
          )}

          {isParsing && (
            <div className="text-center py-12 space-y-4">
              <div className="relative">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-primary animate-spin" />
                </div>
              </div>
              <div className="space-y-2">
                <p className="font-medium">Processing your CV</p>
                <p className="text-sm text-muted-foreground">
                  Extracting information and optimizing for ATS systems...
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reuse the existing PDFGenerationDialog */}
      <PDFGenerationDialog
        open={isPDFDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            // Dialog is closing
            handlePDFDialogClose();
          }
        }}
        contentType="resume"
        initialContent={resumeContent}
        contentId={`onboarding-${Date.now()}`}
      />
    </div>
  );
}