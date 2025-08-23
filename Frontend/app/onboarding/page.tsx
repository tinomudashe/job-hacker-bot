"use client";

import "./onboarding.css";
import { PDFGenerationDialog } from "@/components/chat/pdf-generation-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Logo } from "@/components/ui/logo";
import { useAuth, useClerk } from "@clerk/nextjs";
import { FileUp, Loader2, Upload, FileText, X, CheckCircle2, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { toast } from "sonner";

export default function OnboardingPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  const [isUploading, setIsUploading] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [parsedData, setParsedData] = useState<any>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string>("");
  const [isPDFDialogOpen, setIsPDFDialogOpen] = useState(false);
  const [resumeContent, setResumeContent] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
  const [hasSavedCV, setHasSavedCV] = useState(false);
  const [isCompletingOnboarding, setIsCompletingOnboarding] = useState(false);
  const [isNavigatingAway, setIsNavigatingAway] = useState(false);

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
      
      // Debug logging
      console.log("About to open PDF dialog with content:", formattedResume.substring(0, 200));
      console.log("Dialog state before opening:", { isPDFDialogOpen, resumeContent: resumeContent.substring(0, 100) });
      
      // Open PDF dialog immediately after parsing with a special marker
      // The dialog will parse this special format to populate fields
      const structuredContent = `[ONBOARDING_RESUME_DATA]${JSON.stringify(parsedInfo)}[/ONBOARDING_RESUME_DATA]\n\n${formattedResume}`;
      setResumeContent(structuredContent);
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
    console.log("CompleteOnboarding called, hasCompletedOnboarding:", hasCompletedOnboarding);
    if (hasCompletedOnboarding || isCompletingOnboarding) {
      console.log("Already completed or in progress, skipping...");
      return;
    }
    
    setIsCompletingOnboarding(true);
    
    // Failsafe: Stop loading after 10 seconds no matter what
    const timeoutId = setTimeout(() => {
      console.warn("Onboarding completion timeout - stopping loader");
      setIsCompletingOnboarding(false);
      toast.error("Taking too long. Please refresh and try again.");
    }, 10000);
    
    try {
      const token = await getToken();
      console.log("Got token:", token ? "Token exists" : "No token");
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/users/onboarding/complete`;
      console.log("Making API call to:", apiUrl);
      
      const response = await fetch(apiUrl, {
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

      console.log("Onboarding API response status:", response.status);
      
      if (response.ok) {
        console.log("Onboarding completed successfully, navigating to chat...");
        clearTimeout(timeoutId);
        setHasCompletedOnboarding(true);
        // Navigate immediately to chat without toast or delay
        await router.push("/");
        // Ensure loader stops after navigation
        setIsCompletingOnboarding(false);
      } else {
        console.error("Onboarding API returned error:", response.status);
        clearTimeout(timeoutId);
        const errorData = await response.text();
        console.error("Error details:", errorData);
        setIsCompletingOnboarding(false);
        toast.error("Failed to complete setup. Please try again.");
      }
    } catch (error) {
      console.error("Error completing onboarding:", error);
      clearTimeout(timeoutId);
      toast.error("Failed to complete setup. Please try again.");
      setIsCompletingOnboarding(false);
    }
  };


  const handleManualEntry = () => {
    // Open PDF dialog with empty resume for manual entry
    setResumeContent("");
    setParsedData({}); // Set empty parsed data
    setIsPDFDialogOpen(true);
  };

  const handleCancelOnboarding = async () => {
    try {
      await signOut();
      router.push("/");
    } catch (error) {
      console.error("Error signing out:", error);
      toast.error("Failed to sign out. Please try again.");
    }
  };

  // Show loading spinner while completing onboarding
  if (isCompletingOnboarding) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 dark:from-background dark:via-background dark:to-primary/10">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-muted-foreground">Completing setup...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 dark:from-background dark:via-background dark:to-primary/10 p-4 sm:p-6 lg:p-8 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-48 -right-48 w-64 sm:w-96 h-64 sm:h-96 bg-primary/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-48 -left-48 w-64 sm:w-96 h-64 sm:h-96 bg-chart-1/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>
      
      {/* Hide the card if PDF dialog is open or navigating away to prevent showing welcome screen after save */}
      {!isPDFDialogOpen && !isNavigatingAway && (
        <Card className="w-full max-w-2xl bg-card/80 dark:bg-card/50 backdrop-blur-2xl backdrop-saturate-150 border border-border/50 shadow-2xl rounded-2xl sm:rounded-3xl relative z-10 transition-all duration-300 hover:shadow-3xl">
        <Button
          onClick={handleCancelOnboarding}
          variant="ghost"
          size="icon"
          className="absolute top-6 right-6 text-muted-foreground hover:text-foreground hover:bg-destructive/10 hover:border-destructive/20 border border-transparent transition-all duration-200 rounded-xl"
          title="Cancel and sign out"
        >
          <X className="w-5 h-5" />
        </Button>
        
        <CardHeader className="text-center space-y-4 pb-6 sm:pb-8 pt-10 sm:pt-12">
          <div className="flex justify-center mb-2">
            <Logo size="lg" />
          </div>
          
          <div className="space-y-2 px-4 sm:px-0">
            <CardTitle className="text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Welcome to Job Hacker Bot
            </CardTitle>
            <CardDescription className="text-sm sm:text-base text-muted-foreground max-w-md mx-auto">
              Let's personalize your AI-powered job search experience with your professional profile
            </CardDescription>
          </div>
          
            </CardHeader>
        <CardContent className="space-y-6 px-8 pb-8">
          {!isParsing && !parsedData && (
            <>
              <div
                className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300 group ${
                  dragActive 
                    ? "border-primary bg-gradient-to-br from-primary/10 to-chart-1/10 scale-[1.02] shadow-xl" 
                    : "border-border/50 hover:border-primary/50 hover:bg-gradient-to-br hover:from-primary/5 hover:to-chart-1/5 hover:shadow-lg"
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
                    <div className="space-y-4">
                      <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-chart-1/20 rounded-full blur-xl animate-pulse" />
                        <Loader2 className="w-16 h-16 mx-auto text-primary animate-spin relative z-10" />
                      </div>
                      <div className="space-y-2">
                        <p className="text-base font-semibold text-foreground">Uploading {uploadedFileName}...</p>
                        <div className="w-48 h-1 bg-muted rounded-full mx-auto overflow-hidden">
                          <div className="h-full w-1/2 bg-gradient-to-r from-primary to-chart-1 rounded-full animate-slide" />
                        </div>
                        <p className="text-sm text-muted-foreground">Preparing your document</p>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="relative mx-auto w-16 h-16">
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-chart-1/20 rounded-2xl blur-lg group-hover:blur-xl transition-all duration-300" />
                        <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/10 to-chart-1/10 border border-primary/20 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                          <Upload className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-lg font-semibold text-foreground">Upload your CV/Resume</p>
                        <p className="text-sm text-muted-foreground">
                          Drag & drop your file here or click to browse
                        </p>
                        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground mt-3">
                          <span className="px-2 py-1 bg-muted/50 rounded-lg">PDF</span>
                          <span className="px-2 py-1 bg-muted/50 rounded-lg">DOC</span>
                          <span className="px-2 py-1 bg-muted/50 rounded-lg">DOCX</span>
                          <span className="px-2 py-1 bg-muted/50 rounded-lg">TXT</span>
                          <span className="text-muted-foreground/60">• Max 10MB</span>
                        </div>
                      </div>
                      <Button
                        onClick={() => document.getElementById("cv-upload")?.click()}
                        variant="default"
                        className="bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 text-primary-foreground shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl px-6"
                      >
                        <FileUp className="w-4 h-4 mr-2" />
                        Choose File
                      </Button>
                    </>
                  )}
                </div>
              </div>

              <div className="relative py-4">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full h-px bg-gradient-to-r from-transparent via-border to-transparent" />
                </div>
                <div className="relative flex justify-center">
                  <span className="bg-card px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Or continue with</span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-muted/30 to-muted/10 rounded-2xl p-6 border border-border/50 hover:border-primary/30 transition-all duration-300">
                <div className="text-center space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-center gap-2">
                      <FileText className="w-5 h-5 text-primary" />
                      <p className="text-base font-semibold text-foreground">No CV? No Problem!</p>
                    </div>
                    <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                      Create your professional profile by entering your information manually - we'll help you build it step by step
                    </p>
                  </div>
                  <Button
                    onClick={handleManualEntry}
                    variant="outline"
                    className="border-primary/50 hover:bg-primary/10 hover:border-primary hover:scale-105 transition-all duration-300 rounded-xl shadow-sm hover:shadow-lg group"
                  >
                    <FileText className="w-4 h-4 mr-2 group-hover:rotate-12 transition-transform duration-300" />
                    Enter Information Manually
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
                  </Button>
                </div>
              </div>
            </>
          )}

          {isParsing && (
            <div className="text-center py-16 space-y-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-32 h-32 bg-gradient-to-r from-primary/20 to-chart-1/20 rounded-full blur-2xl animate-pulse" />
                </div>
                <div className="relative space-y-4">
                  <div className="w-20 h-20 mx-auto rounded-3xl bg-gradient-to-br from-primary/20 to-chart-1/20 border border-primary/30 flex items-center justify-center shadow-2xl">
                    <Loader2 className="w-10 h-10 text-primary animate-spin" />
                  </div>
                  
                  {/* Processing steps with animation */}
                  <div className="space-y-3 max-w-sm mx-auto">
                    <div className="flex items-center gap-3 text-sm">
                      <CheckCircle2 className="w-5 h-5 text-green-500 animate-in fade-in duration-500" />
                      <span className="text-muted-foreground">Document uploaded successfully</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                      <span className="text-foreground font-medium">Extracting professional information...</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm opacity-50">
                      <div className="w-5 h-5 rounded-full border-2 border-muted" />
                      <span className="text-muted-foreground">Optimizing for ATS systems</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <p className="text-lg font-semibold text-foreground">Processing your CV</p>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  Our AI is analyzing your professional profile to provide personalized job recommendations
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      )}

      {/* Reuse the existing PDFGenerationDialog with save tracking */}
      <PDFGenerationDialog
        open={isPDFDialogOpen}
        onOpenChange={(open) => {
          console.log("PDFGenerationDialog onOpenChange called with open:", open);
          // Simply update the state - navigation is handled by Save & Proceed button
          setIsPDFDialogOpen(open);
        }}
        contentType="resume"
        initialContent={resumeContent}
        contentId={`onboarding-${Date.now()}`}
        onNavigate={() => setIsNavigatingAway(true)}
      />
    </div>
  );
}