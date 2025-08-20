"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  Send,
  Sparkles,
  Clock,
  Link2,
  Copy,
  Download,
  Mail,
  User,
  Building,
  Briefcase,
  Target,
  FileText,
  Calendar,
  ChevronRight,
  Loader2,
  Check,
  X,
  RefreshCw,
  Wand2,
  Plus,
} from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";

interface EmailContext {
  recipientName?: string;
  recipientTitle?: string;
  companyName?: string;
  jobTitle?: string;
  jobUrl?: string;
  previousInteraction?: string;
  userName: string;
  userBackground?: string;
  purpose: string;
  tone: string;
  additionalContext?: string;
}

interface EmailTemplate {
  subject: string;
  body: string;
  signature?: string;
  attachments?: string[];
  followUpSchedule?: any;
}

interface EmailComposerProps {
  onSendMessage?: (message: string) => void;
  initialContext?: Partial<EmailContext>;
  mode?: "compose" | "follow-up" | "improve";
  existingEmail?: string;
  className?: string;
}

export function EmailComposer({
  onSendMessage,
  initialContext = {},
  mode = "compose",
  existingEmail = "",
  className,
}: EmailComposerProps) {
  // Form state
  const [context, setContext] = useState<EmailContext>({
    userName: "",
    purpose: "job_application",
    tone: "professional",
    ...initialContext,
  });
  
  const [emailTemplate, setEmailTemplate] = useState<EmailTemplate>({
    subject: "",
    body: "",
    signature: "",
  });
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [copiedToClipboard, setCopiedToClipboard] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState("custom");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [isExtractingUrl, setIsExtractingUrl] = useState(false);

  // Email templates
  const emailTemplates = [
    { value: "custom", label: "Custom Email" },
    { value: "initial_application", label: "Job Application" },
    { value: "follow_up_after_application", label: "Application Follow-up" },
    { value: "thank_you_after_interview", label: "Thank You Note" },
    { value: "networking", label: "Networking Outreach" },
    { value: "informational_interview", label: "Informational Interview Request" },
  ];

  const toneOptions = [
    { value: "professional", label: "Professional" },
    { value: "friendly", label: "Friendly" },
    { value: "formal", label: "Formal" },
    { value: "casual", label: "Casual" },
    { value: "enthusiastic", label: "Enthusiastic" },
  ];

  const purposeOptions = [
    { value: "job_application", label: "Job Application" },
    { value: "follow_up", label: "Follow-up" },
    { value: "networking", label: "Networking" },
    { value: "thank_you", label: "Thank You" },
    { value: "introduction", label: "Introduction" },
    { value: "request_meeting", label: "Request Meeting" },
  ];

  // Extract job info from URL
  const handleExtractFromUrl = async () => {
    if (!urlInput) {
      toast.error("Please enter a URL");
      return;
    }

    setIsExtractingUrl(true);
    
    // Send message to extract job info
    if (onSendMessage) {
      const message = `Extract job information from this URL and prepare an email context: ${urlInput}`;
      onSendMessage(message);
      
      // Simulate extraction (in real app, this would come from backend)
      setTimeout(() => {
        setContext({
          ...context,
          jobUrl: urlInput,
          companyName: "Extracted Company",
          jobTitle: "Extracted Position",
        });
        setIsExtractingUrl(false);
        toast.success("Job information extracted from URL");
      }, 2000);
    }
  };

  // Generate email
  const handleGenerateEmail = async () => {
    setIsGenerating(true);
    
    try {
      // Create the request message
      const requestMessage = `Generate a ${context.tone} email for ${context.purpose}:
      
      Recipient: ${context.recipientName || "Hiring Manager"} ${context.recipientTitle ? `(${context.recipientTitle})` : ""}
      Company: ${context.companyName || "the company"}
      Position: ${context.jobTitle || "the position"}
      ${context.jobUrl ? `Job URL: ${context.jobUrl}` : ""}
      
      Sender: ${context.userName}
      ${context.userBackground ? `Background: ${context.userBackground}` : ""}
      
      ${context.additionalContext ? `Additional Context: ${context.additionalContext}` : ""}
      
      Template Type: ${selectedTemplate}`;
      
      if (onSendMessage) {
        onSendMessage(requestMessage);
      }
      
      // Simulate email generation (in production, this would come from backend)
      setTimeout(() => {
        setEmailTemplate({
          subject: `Application for ${context.jobTitle || "Position"} at ${context.companyName || "Your Company"}`,
          body: `Dear ${context.recipientName || "Hiring Manager"},

I am writing to express my strong interest in the ${context.jobTitle || "position"} at ${context.companyName || "your company"}.

[Your generated email content will appear here based on the context provided]

Best regards,
${context.userName}`,
          signature: `${context.userName}
[Your contact information]`,
        });
        setIsGenerating(false);
        toast.success("Email generated successfully!");
      }, 2000);
      
    } catch (error) {
      setIsGenerating(false);
      toast.error("Failed to generate email");
    }
  };

  // Improve existing email
  const handleImproveEmail = async () => {
    if (!emailTemplate.body && !existingEmail) {
      toast.error("Please write or generate an email first");
      return;
    }
    
    setIsImproving(true);
    
    const emailToImprove = emailTemplate.body || existingEmail;
    
    if (onSendMessage) {
      onSendMessage(`Improve this email and make it more ${context.tone}:

${emailToImprove}`);
    }
    
    // Simulate improvement
    setTimeout(() => {
      setEmailTemplate({
        ...emailTemplate,
        body: emailToImprove + "\n\n[Improved version will appear here]",
      });
      setIsImproving(false);
      toast.success("Email improved!");
    }, 2000);
  };

  // Copy to clipboard
  const handleCopyToClipboard = () => {
    const fullEmail = `Subject: ${emailTemplate.subject}

${emailTemplate.body}

${emailTemplate.signature}`;
    
    navigator.clipboard.writeText(fullEmail);
    setCopiedToClipboard(true);
    toast.success("Email copied to clipboard!");
    
    setTimeout(() => setCopiedToClipboard(false), 2000);
  };

  // Send as message
  const handleSendAsMessage = () => {
    if (!emailTemplate.body) {
      toast.error("Please generate an email first");
      return;
    }
    
    if (onSendMessage) {
      onSendMessage(`Send this email:

Subject: ${emailTemplate.subject}

${emailTemplate.body}

${emailTemplate.signature}`);
      toast.success("Email sent to chat!");
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Mail className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">
            {mode === "compose" && "Compose Email"}
            {mode === "follow-up" && "Generate Follow-up"}
            {mode === "improve" && "Improve Email"}
          </h3>
        </div>
        
        <Badge variant="outline" className="gap-1">
          <Sparkles className="h-3 w-3" />
          AI-Powered
        </Badge>
      </div>

      {/* URL Extractor */}
      <div className="space-y-2">
        <Label>Extract from Job URL (Optional)</Label>
        <div className="flex gap-2">
          <Input
            placeholder="https://example.com/job-posting"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            className="flex-1"
          />
          <Button
            onClick={handleExtractFromUrl}
            disabled={isExtractingUrl || !urlInput}
            size="sm"
          >
            {isExtractingUrl ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Link2 className="h-4 w-4" />
            )}
            Extract
          </Button>
        </div>
      </div>

      {/* Template Selection */}
      <div className="space-y-2">
        <Label>Email Template</Label>
        <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {emailTemplates.map((template) => (
              <SelectItem key={template.value} value={template.value}>
                {template.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Basic Context */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Your Name *</Label>
          <Input
            placeholder="John Doe"
            value={context.userName}
            onChange={(e) => setContext({ ...context, userName: e.target.value })}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Recipient Name</Label>
          <Input
            placeholder="Hiring Manager"
            value={context.recipientName}
            onChange={(e) => setContext({ ...context, recipientName: e.target.value })}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Company Name</Label>
          <Input
            placeholder="Tech Corp"
            value={context.companyName}
            onChange={(e) => setContext({ ...context, companyName: e.target.value })}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Job Title</Label>
          <Input
            placeholder="Software Engineer"
            value={context.jobTitle}
            onChange={(e) => setContext({ ...context, jobTitle: e.target.value })}
          />
        </div>
      </div>

      {/* Tone and Purpose */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Email Purpose</Label>
          <Select value={context.purpose} onValueChange={(v) => setContext({ ...context, purpose: v })}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {purposeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div className="space-y-2">
          <Label>Tone</Label>
          <Select value={context.tone} onValueChange={(v) => setContext({ ...context, tone: v })}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {toneOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Advanced Options */}
      <div className="space-y-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="gap-1"
        >
          <ChevronRight className={cn("h-4 w-4 transition-transform", showAdvanced && "rotate-90")} />
          Advanced Options
        </Button>
        
        {showAdvanced && (
          <div className="space-y-4 pl-6">
            <div className="space-y-2">
              <Label>Recipient Title</Label>
              <Input
                placeholder="Senior Recruiter"
                value={context.recipientTitle}
                onChange={(e) => setContext({ ...context, recipientTitle: e.target.value })}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Your Background (Brief Summary)</Label>
              <Textarea
                placeholder="5+ years of experience in software development..."
                value={context.userBackground}
                onChange={(e) => setContext({ ...context, userBackground: e.target.value })}
                rows={3}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Additional Context</Label>
              <Textarea
                placeholder="Any specific points you want to mention..."
                value={context.additionalContext}
                onChange={(e) => setContext({ ...context, additionalContext: e.target.value })}
                rows={3}
              />
            </div>
          </div>
        )}
      </div>

      {/* Email Preview/Editor */}
      {(emailTemplate.subject || emailTemplate.body) && (
        <div className="space-y-4 p-4 bg-muted/30 rounded-lg border">
          <div className="space-y-2">
            <Label>Subject</Label>
            <Input
              value={emailTemplate.subject}
              onChange={(e) => setEmailTemplate({ ...emailTemplate, subject: e.target.value })}
              className="font-medium"
            />
          </div>
          
          <div className="space-y-2">
            <Label>Email Body</Label>
            <Textarea
              value={emailTemplate.body}
              onChange={(e) => setEmailTemplate({ ...emailTemplate, body: e.target.value })}
              rows={10}
              className="font-mono text-sm"
            />
          </div>
          
          <div className="space-y-2">
            <Label>Signature</Label>
            <Textarea
              value={emailTemplate.signature}
              onChange={(e) => setEmailTemplate({ ...emailTemplate, signature: e.target.value })}
              rows={3}
              className="font-mono text-sm"
            />
          </div>
          
          {/* Email Actions */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyToClipboard}
              disabled={!emailTemplate.body}
            >
              {copiedToClipboard ? (
                <>
                  <Check className="h-4 w-4 mr-1" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-1" />
                  Copy
                </>
              )}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleImproveEmail}
              disabled={isImproving || !emailTemplate.body}
            >
              {isImproving ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Wand2 className="h-4 w-4 mr-1" />
              )}
              Improve
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleSendAsMessage}
              disabled={!emailTemplate.body}
            >
              <Send className="h-4 w-4 mr-1" />
              Send to Chat
            </Button>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {mode === "compose" && "Fill in the details above to generate your email"}
          {mode === "follow-up" && "Generate a follow-up based on previous interaction"}
          {mode === "improve" && "Paste your email above for AI improvements"}
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              setEmailTemplate({ subject: "", body: "", signature: "" });
              setContext({
                ...context,
                recipientName: "",
                companyName: "",
                jobTitle: "",
              });
            }}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Reset
          </Button>
          
          <Button
            onClick={handleGenerateEmail}
            disabled={isGenerating || !context.userName}
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-1" />
                Generate Email
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}