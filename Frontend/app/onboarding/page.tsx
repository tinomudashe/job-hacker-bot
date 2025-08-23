"use client";

import { PDFGenerationDialog } from "@/components/chat/pdf-generation-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@clerk/nextjs";
import { FileUp, Loader2, Upload } from "lucide-react";
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

      const token = await getToken();
      const uploadResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/uploads/cv`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error("Failed to upload CV");
      }

      const uploadData = await uploadResponse.json();
      console.log("Upload successful:", uploadData);

      // Step 2: Parse the CV
      setIsUploading(false);
      setIsParsing(true);
      toast.success("CV uploaded! Processing your information...");

      // Parse the CV content (you might need to adjust this based on your backend)
      const parseResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/cv/parse`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          file_path: uploadData.file_path,
          file_id: uploadData.file_id 
        }),
      });

      if (!parseResponse.ok) {
        throw new Error("Failed to parse CV");
      }

      const parsedResult = await parseResponse.json();
      setParsedData(parsedResult);
      
      // Format the parsed data into resume content
      const formattedResume = formatParsedDataToResume(parsedResult);
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
    // Format the parsed data into a resume string
    // This should match the format expected by PDFGenerationDialog
    let resume = "";
    
    if (data.personal_info) {
      resume += `${data.personal_info.name || ""}\n`;
      resume += `${data.personal_info.email || ""} | ${data.personal_info.phone || ""}\n`;
      resume += `${data.personal_info.location || ""}\n\n`;
    }
    
    if (data.summary) {
      resume += `PROFESSIONAL SUMMARY\n${data.summary}\n\n`;
    }
    
    if (data.experience && data.experience.length > 0) {
      resume += `WORK EXPERIENCE\n`;
      data.experience.forEach((exp: any) => {
        resume += `${exp.title} at ${exp.company}\n`;
        resume += `${exp.dates}\n`;
        resume += `${exp.description}\n\n`;
      });
    }
    
    if (data.education && data.education.length > 0) {
      resume += `EDUCATION\n`;
      data.education.forEach((edu: any) => {
        resume += `${edu.degree} - ${edu.school}\n`;
        resume += `${edu.dates}\n\n`;
      });
    }
    
    if (data.skills && data.skills.length > 0) {
      resume += `SKILLS\n`;
      resume += data.skills.join(", ");
    }
    
    return resume;
  };

  const handlePDFDialogClose = async (saved: boolean) => {
    if (saved) {
      // Mark onboarding as complete
      try {
        const token = await getToken();
        await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/users/onboarding/complete`, {
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
        
        // Metadata is updated server-side, just redirect
        toast.success("Welcome to Job Hacker Bot! Let's find your dream job!");
        
        // Small delay to ensure metadata propagates
        setTimeout(() => {
          router.push("/");
        }, 500);
      } catch (error) {
        console.error("Error completing onboarding:", error);
        toast.error("Failed to complete setup. Please try again.");
      }
    }
    setIsPDFDialogOpen(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-xl">
        <CardHeader className="text-center space-y-1">
          <CardTitle className="text-2xl font-bold">Welcome to Job Hacker Bot! 🚀</CardTitle>
          <CardDescription className="text-base">
            Let's get started by uploading your CV. We'll help you optimize it for your job search.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isParsing && !parsedData && (
            <div
              className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
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
                    <Upload className="w-12 h-12 mx-auto text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">Drop your CV here</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        or click to browse (PDF, DOC, DOCX, TXT - Max 10MB)
                      </p>
                    </div>
                    <Button
                      onClick={() => document.getElementById("cv-upload")?.click()}
                      variant="outline"
                      className="mt-2"
                    >
                      <FileUp className="w-4 h-4 mr-2" />
                      Choose File
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}

          {isParsing && (
            <div className="text-center py-8 space-y-4">
              <Loader2 className="w-12 h-12 mx-auto text-primary animate-spin" />
              <div>
                <p className="text-sm font-medium">Processing your CV...</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Extracting your information and optimizing for ATS
                </p>
              </div>
            </div>
          )}

          <p className="text-xs text-center text-muted-foreground">
            Your CV is required to personalize your job search experience
          </p>
        </CardContent>
      </Card>

      {/* Reuse the existing PDFGenerationDialog */}
      <PDFGenerationDialog
        open={isPDFDialogOpen}
        onOpenChange={(open) => {
          if (!open && !parsedData) {
            // Don't allow closing without action during onboarding
            toast.error("Please save or edit your CV to continue");
            return;
          }
          handlePDFDialogClose(!open);
        }}
        contentType="resume"
        initialContent={resumeContent}
        contentId={`onboarding-${Date.now()}`}
      />
    </div>
  );
}