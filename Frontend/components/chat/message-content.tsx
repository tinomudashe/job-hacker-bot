"use client";

import { cn } from "@/lib/utils";
import { ExternalLink, File, FileText, Image, Send, MapPin, Calendar, Link2, Target, Sparkles } from "lucide-react";
import React, { MouseEvent } from "react";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";

interface MessageContentProps {
  content: any;
  isUser?: boolean;
}

interface CodeProps {
  inline?: boolean;
  className?: string;
  children: React.ReactNode;
}

// Custom link component for ReactMarkdown
const LinkComponent = ({ href, children, isUser, ...props }: any) => {
  if (!href) return <span>{children}</span>;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Open external links in new tab
    if (href.startsWith("http") || href.startsWith("https")) {
      window.open(href, "_blank", "noopener,noreferrer");
    } else if (href.startsWith("mailto:")) {
      window.location.href = href;
    } else {
      // For relative links or other protocols
      window.open(href, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <a
      href={href}
      onClick={handleClick}
      className={cn(
        // Conditional styling based on message type
        isUser
          ? "text-white hover:text-yellow-200"
          : "text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200",
        "underline hover:no-underline cursor-pointer transition-colors duration-200",
        "inline-flex items-center gap-1 break-all font-medium"
      )}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
      {(href.startsWith("http") || href.startsWith("https")) && (
        <ExternalLink className="h-3 w-3 opacity-70" />
      )}
    </a>
  );
};

// File icon helper
const getFileIcon = (filename: string) => {
  const extension = filename.split(".").pop()?.toLowerCase() || "";
  const iconClass = "h-4 w-4";

  if (
    ["jpg", "jpeg", "png", "gif", "svg", "webp", "bmp", "tiff"].includes(
      extension
    )
  ) {
    return <Image className={iconClass} />;
  }
  if (["pdf", "doc", "docx", "txt", "rtf", "odt"].includes(extension)) {
    return <FileText className={iconClass} />;
  }
  return <File className={iconClass} />;
};

// **REVISED** Content type detector to handle the specific message format
const detectContentType = (text: string) => {
  // Pattern to handle 'File Attached: [file]\n\nMessage: [msg]'
  const specificPattern =
    /^(?:File Attached|📎 Attached file):\s*([\s\S]*?)(?:\n\nMessage:\s*([\s\S]*))?$/i;
  const specificMatch = text.match(specificPattern);

  if (specificMatch) {
    return {
      type: "file",
      filename: specificMatch[1].trim(),
      userMessage: specificMatch[2] ? specificMatch[2].trim() : "",
      fullMatch: text,
    };
  }

  // Fallback for other existing formats
  const fallbackPatterns = {
    fileAttached: /\*\*File Attached:\*\* (.+?)(?:\n|$)/,
    cvUploaded:
      /\*\*CV\/Resume uploaded successfully!\*\*[\s\S]*?\*\*File:\*\* (.+?)(?:\n|$)/,
    emojiFileAttached: /📎 \*\*File Attached:\*\* (.+?)(?:\n|$)/,
  };

  for (const [type, pattern] of Object.entries(fallbackPatterns)) {
    const match = text.match(pattern);
    if (match) {
      const userMessage = text.replace(match[0], "").trim();
      return {
        type: type.includes("cv") ? "cv" : "file",
        filename: match[1].trim(),
        userMessage: userMessage,
        fullMatch: match[0],
      };
    }
  }

  return null;
};

// **REVISED** Attachment renderer component to be simpler
const AttachmentRenderer = ({
  filename,
  userMessage,
  text, // Keep for legacy CV upload details
  isUser,
}: {
  filename: string;
  userMessage?: string;
  text: string;
  isUser?: boolean;
}) => {
  return (
    <div className="space-y-3">
      {/* Render the user's message first if it exists */}
      {userMessage && (
        <div className="text-sm text-foreground">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: (props: any) => <LinkComponent {...props} isUser={isUser} />,
            }}
          >
            {userMessage}
          </ReactMarkdown>
        </div>
      )}

      {/* File attachment display */}
      <div
        className={cn(
          "flex items-center gap-3 p-3 rounded-lg border",
          "bg-muted/30 border-border/50 hover:bg-muted/40 transition-colors"
        )}
      >
        <div className="flex items-center justify-center h-8 w-8 shrink-0 rounded-md bg-primary text-primary-foreground">
          {getFileIcon(filename)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-foreground text-sm truncate">
            {filename}
          </p>
          <p className="text-xs text-muted-foreground">
            {filename.split(".").pop()?.toUpperCase() || "FILE"} file
          </p>
        </div>
      </div>

      {/* CV upload success details */}
      {text.includes("CV/Resume uploaded successfully") && (
        <div className="text-sm text-muted-foreground mt-2 space-y-1">
          {text.includes("Profile Updated") && (
            <p className="text-green-600 dark:text-green-400 font-medium">
              ✅ Profile automatically updated
            </p>
          )}
          <p className="text-xs">CV processed and ready for job applications</p>
        </div>
      )}
    </div>
  );
};

// Badge component for triggers
const TriggerBadge: React.FC<{ type: string }> = ({ type }) => {
  const getBadgeInfo = (triggerType: string) => {
    switch (triggerType) {
      case "RESUME":
        return { label: "📄 Resume Ready", color: "blue" };
      case "COVER_LETTER":
        return { label: "📝 Cover Letter Ready", color: "green" };
      case "CV":
        return { label: "📋 CV Ready", color: "purple" };
      default:
        return { label: "📥 Download Ready", color: "gray" };
    }
  };

  const { label, color } = getBadgeInfo(type);
  
  const colorClasses = {
    blue: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30",
    green: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/30",
    purple: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30",
    gray: "bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/30"
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-sm font-medium",
        "border",
        colorClasses[color as keyof typeof colorClasses]
      )}
    >
      {label}
    </span>
  );
};

// Function to replace job listing emojis with clean text formatting
const processJobListings = (text: string) => {
  // Check if this is a job listing format
  if (!text.includes('📍') && !text.includes('📅') && !text.includes('🔗') && !text.includes('🎯')) {
    return text;
  }
  
  // Replace emojis with clean markdown formatting
  let processed = text
    .replace(/🎯\s*\*\*/g, '## ')  // Replace target with heading
    .replace(/📍\s*\*\*/g, '**')  // Remove location emoji, keep bold
    .replace(/📅\s*\*\*/g, '**')  // Remove calendar emoji, keep bold  
    .replace(/🔗\s*\*\*/g, '**')  // Remove link emoji, keep bold
    .replace(/✨\s*/g, '### ')  // Replace sparkles with smaller heading
    .replace(/💡\s*/g, '> ');  // Replace lightbulb with blockquote
    
  return processed;
};

// Function to clean markdown formatting from cover letters
const cleanCoverLetterFormatting = (text: string) => {
  // Check if this appears to be a cover letter
  const isCoverLetter = text.includes('cover letter') || 
                        text.includes('Cover Letter') || 
                        text.includes('[DOWNLOADABLE_COVER_LETTER]') ||
                        text.includes('Dear Hiring') ||
                        text.includes('position') && text.includes('excited') ||
                        text.includes('JavaScript') && text.includes('experience');
  
  if (!isCoverLetter) {
    return text;
  }
  
  // Remove triple asterisks but keep the text
  let cleaned = text
    .replace(/\*\*\*([^*]+)\*\*\*/g, '$1')  // Remove *** formatting
    .replace(/\*\*([^*]+)\*\*/g, '$1')      // Remove ** formatting  
    .replace(/\*([^*]+)\*/g, '$1');          // Remove * formatting
    
  return cleaned;
};

// Function to process text and replace triggers with badges
const processTextWithBadges = (text: string) => {
  // Pattern to match triggers
  const triggerPattern = /\[(DOWNLOADABLE_RESUME|DOWNLOADABLE_COVER_LETTER|DOWNLOADABLE_CV)\]/g;
  
  // Debug logging
  if (text.includes("[DOWNLOADABLE_")) {
    console.log("🔍 processTextWithBadges - Processing text with trigger:", text.substring(0, 200));
  }
  
  const parts: (string | React.ReactElement)[] = [];
  let lastIndex = 0;
  let match;
  let keyIndex = 0;
  
  while ((match = triggerPattern.exec(text)) !== null) {
    console.log("✅ Found trigger match:", match[0], "Type:", match[1]);
    // Add text before the trigger
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    
    // Add the badge component
    const triggerType = match[1].replace('DOWNLOADABLE_', '');
    parts.push(<TriggerBadge key={`badge-${keyIndex++}`} type={triggerType} />);
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  
  // If no triggers found, return null to let markdown handle it
  return parts.length > 1 ? parts : null;
};

// Main content dispatcher
export function MessageContent({ content, isUser }: MessageContentProps) {
  if (!content) return null;

  const text = typeof content === "string" ? content : content.message || "";
  if (typeof text !== "string") return null;
  
  // Debug logging for trigger detection
  if (text.includes("[DOWNLOADABLE_")) {
    console.log("🎯 MessageContent - Found DOWNLOADABLE trigger in text:", text.substring(0, 200));
  }

  // Detect if this is an attachment message
  const attachmentInfo = detectContentType(text);

  if (attachmentInfo) {
    return (
      <AttachmentRenderer
        filename={attachmentInfo.filename}
        userMessage={attachmentInfo.userMessage}
        text={text}
        isUser={isUser}
      />
    );
  }
  
  // Define markdown components with proper typing
  const components: Components = {
    a: ({ href, children }) => {
      // Check if this is a cover letter generation link
      const isCoverLetterButton = children
        ?.toString()
        .includes("Generate Cover Letter");

      if (isCoverLetterButton) {
        return (
          <button
            onClick={(e: MouseEvent<HTMLButtonElement>) => {
              e.preventDefault();
              // The parent message will handle sending the cover letter request
              const message = `Please generate a cover letter for this role`;
              // You can dispatch this message to your chat handler
              // For now, we'll just log it
              console.log("Generate cover letter requested:", message);
            }}
            className={cn(
              "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200",
              "bg-blue-500 text-white hover:bg-blue-600 active:bg-blue-700",
              "dark:bg-blue-600 dark:hover:bg-blue-700 dark:active:bg-blue-800",
              "shadow-sm hover:shadow-md"
            )}
            type="button"
          >
            <Send className="h-3.5 w-3.5" />
            Generate Cover Letter
          </button>
        );
      }

      // Regular link with enhanced styling
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            "inline-flex items-center gap-1.5 hover:gap-2 transition-all duration-200",
            isUser
              ? "text-white/90 hover:text-white underline decoration-white/30 hover:decoration-white/70"
              : "text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 underline decoration-blue-400/30 hover:decoration-blue-400/70"
          )}
        >
          {children}
          <ExternalLink className="h-3.5 w-3.5 opacity-70" />
        </a>
      );
    },
    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
    ul: ({ children }) => (
      <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>
    ),
    code: ({ children }) => (
      <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    ),
  };

  // Check if text contains triggers and process them
  const badgeContent = processTextWithBadges(text);
  if (badgeContent) {
    return (
      <div className="inline-flex flex-wrap items-center gap-2">
        {badgeContent.map((part, index) => {
          if (typeof part === 'string') {
            // Process job listings for string parts
            const processedPart = processJobListings(part);
            // Render string parts with markdown
            return (
              <ReactMarkdown 
                key={`text-${index}`}
                remarkPlugins={[remarkGfm]} 
                components={components}
              >
                {processedPart}
              </ReactMarkdown>
            );
          }
          return part; // Return badge components as-is
        })}
      </div>
    );
  }

  // Regular message content with enhanced link handling (process job listings and clean cover letters)
  let processedText = processJobListings(text);
  processedText = cleanCoverLetterFormatting(processedText);
  
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {processedText}
    </ReactMarkdown>
  );
}
