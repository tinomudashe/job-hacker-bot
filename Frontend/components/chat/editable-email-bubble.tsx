"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Mail, Edit3, Check, X, Copy, Sparkles } from "lucide-react";
import { toast } from "sonner";

interface EmailData {
  subject: string;
  to: string;
  body: string;
  signature?: string;
}

interface EditableEmailBubbleProps {
  content: string;
  className?: string;
  onEmailUpdate?: (emailData: EmailData) => void;
}

export function EditableEmailBubble({ 
  content, 
  className,
  onEmailUpdate 
}: EditableEmailBubbleProps) {
  const [isEditing, setIsEditing] = React.useState(false);
  const [emailData, setEmailData] = React.useState<EmailData>(() => {
    // Parse the email content from the markdown format
    const lines = content.split('\n');
    let subject = '';
    let to = '';
    let body = '';
    let signature = '';
    let inBody = false;
    let inSignature = false;
    
    for (const line of lines) {
      if (line.startsWith('**Subject:**')) {
        subject = line.replace('**Subject:**', '').trim();
      } else if (line.startsWith('**To:**')) {
        to = line.replace('**To:**', '').trim();
      } else if (line.startsWith('**Email Body:**')) {
        inBody = true;
        continue;
      } else if (line.includes('---')) {
        inBody = false;
        inSignature = false;
      } else if (inBody && !line.startsWith('**') && !line.startsWith('✅') && !line.startsWith('💡') && !line.startsWith('📊')) {
        if (line.trim() !== '') {
          body += line + '\n';
        }
      }
    }
    
    // Clean up body - remove extra newlines
    body = body.trim();
    
    return { subject, to, body, signature };
  });
  
  const [editedData, setEditedData] = React.useState<EmailData>(emailData);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  
  React.useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      // Adjust height to fit content
      adjustTextareaHeight();
    }
  }, [isEditing]);
  
  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };
  
  const handleSave = () => {
    setEmailData(editedData);
    setIsEditing(false);
    if (onEmailUpdate) {
      onEmailUpdate(editedData);
    }
    toast.success("Email updated successfully");
  };
  
  const handleCancel = () => {
    setEditedData(emailData);
    setIsEditing(false);
  };
  
  const handleCopy = () => {
    const fullEmail = `Subject: ${emailData.subject}\nTo: ${emailData.to}\n\n${emailData.body}${emailData.signature ? '\n\n' + emailData.signature : ''}`;
    navigator.clipboard.writeText(fullEmail);
    toast.success("Email copied to clipboard");
  };
  
  const createMailtoLink = () => {
    const subject = encodeURIComponent(emailData.subject);
    const body = encodeURIComponent(emailData.body + (emailData.signature ? '\n\n' + emailData.signature : ''));
    return `mailto:${emailData.to}?subject=${subject}&body=${body}`;
  };
  
  return (
    <div className={cn(
      "relative group rounded-xl border transition-all duration-300",
      "bg-card hover:bg-accent/5",
      "border-border hover:border-primary/20",
      "hover:shadow-lg hover:shadow-primary/5",
      isEditing && "ring-2 ring-primary ring-offset-2 ring-offset-background",
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Mail className="w-4 h-4 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">
              Professional Email
            </h3>
            <p className="text-xs text-muted-foreground">
              {isEditing ? "Editing mode" : "Click edit to personalize"}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {!isEditing ? (
            <>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setIsEditing(true)}
                className="h-8 px-3 text-xs hover:bg-primary/10"
              >
                <Edit3 className="w-3 h-3 mr-1" />
                Edit
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleCopy}
                className="h-8 w-8 p-0 hover:bg-primary/10"
              >
                <Copy className="w-3 h-3" />
              </Button>
            </>
          ) : (
            <>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleSave}
                className="h-8 px-3 text-xs text-green-600 hover:text-green-700 hover:bg-green-100 dark:hover:bg-green-900/30"
              >
                <Check className="w-3 h-3 mr-1" />
                Save
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleCancel}
                className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-100 dark:hover:bg-red-900/30"
              >
                <X className="w-3 h-3" />
              </Button>
            </>
          )}
        </div>
      </div>
      
      {/* Email Content */}
      <div className="p-4 space-y-4">
        {/* Subject Field */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground">Subject</label>
          {isEditing ? (
            <input
              type="text"
              value={editedData.subject}
              onChange={(e) => setEditedData({ ...editedData, subject: e.target.value })}
              className="w-full px-3 py-2 text-sm rounded-lg border border-input bg-background focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
              placeholder="Email subject..."
            />
          ) : (
            <p className="text-sm font-medium text-foreground">
              {emailData.subject}
            </p>
          )}
        </div>
        
        {/* To Field */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground">To</label>
          {isEditing ? (
            <input
              type="email"
              value={editedData.to}
              onChange={(e) => setEditedData({ ...editedData, to: e.target.value })}
              className="w-full px-3 py-2 text-sm rounded-lg border border-input bg-background focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
              placeholder="recipient@email.com"
            />
          ) : (
            <p className="text-sm text-foreground/80">
              {emailData.to || '[Add recipient email]'}
            </p>
          )}
        </div>
        
        {/* Body Field */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground">Message</label>
          {isEditing ? (
            <textarea
              ref={textareaRef}
              value={editedData.body}
              onChange={(e) => {
                setEditedData({ ...editedData, body: e.target.value });
                adjustTextareaHeight();
              }}
              className="w-full px-3 py-2 text-sm rounded-lg border border-input bg-background focus:ring-2 focus:ring-primary focus:border-transparent resize-none transition-colors"
              placeholder="Email body..."
              rows={8}
            />
          ) : (
            <div className="p-3 rounded-lg bg-muted/30 border border-border">
              <p className="text-sm text-foreground/80 whitespace-pre-wrap">
                {emailData.body}
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Footer with Tips */}
      <div className="px-4 pb-4">
        <div className="flex items-center gap-2 p-3 rounded-lg bg-primary/5 border border-primary/10">
          <Sparkles className="w-4 h-4 text-primary flex-shrink-0" />
          <p className="text-xs text-muted-foreground">
            {isEditing 
              ? "Personalize the email with specific details about your experience"
              : "Click 'Edit' to customize this email before sending"}
          </p>
        </div>
      </div>
      
      {/* Hidden mailto link for external use */}
      <a 
        id={`mailto-link-${emailData.subject}`}
        href={createMailtoLink()}
        className="hidden"
        aria-hidden="true"
      >
        Send Email
      </a>
    </div>
  );
}