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
  // New pattern for CV uploads: [CV_UPLOAD:filename]\nmessage
  const cvUploadPattern = /^\[CV_UPLOAD:(.+?)\]\n([\s\S]+)$/;
  const cvMatch = text.match(cvUploadPattern);
  
  if (cvMatch) {
    return {
      type: "cv",
      filename: cvMatch[1].trim(),
      userMessage: cvMatch[2].trim(),
      fullMatch: text,
    };
  }

  // New pattern for file uploads: [FILE_UPLOAD:filename]\nmessage
  const fileUploadPattern = /^\[FILE_UPLOAD:(.+?)\]\n([\s\S]+)$/;
  const fileMatch = text.match(fileUploadPattern);
  
  if (fileMatch) {
    return {
      type: "file",
      filename: fileMatch[1].trim(),
      userMessage: fileMatch[2].trim(),
      fullMatch: text,
    };
  }

  // DO NOT DISPLAY CV upload success messages - they are handled by toasts
  // Just ignore them completely
  if (text.startsWith("CV/Resume uploaded successfully!")) {
    return null; // Don't display this as an attachment - toast handles it
  }

  // Updated pattern to handle 'Attached file: [filename]\n\n[message]'
  const attachedFilePattern = /^Attached file:\s*(.+?)(?:\n\n([\s\S]+))?$/;
  const attachedMatch = text.match(attachedFilePattern);
  
  if (attachedMatch) {
    return {
      type: "file",
      filename: attachedMatch[1].trim(),
      userMessage: attachedMatch[2] ? attachedMatch[2].trim() : "",
      fullMatch: text,
    };
  }

  // Legacy pattern to handle 'File Attached: [file]\n\nMessage: [msg]'
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

// **REVISED** Attachment renderer component - with glass effect from chat-message.tsx
const AttachmentRenderer = ({
  filename,
  userMessage,
  isUser,
  type,
}: {
  filename: string;
  userMessage?: string;
  isUser?: boolean;
  type?: string;
}) => {
  
  return (
    <div className="space-y-3">
      {/* Attachment Card with glass effect */}
      <div
        className={cn(
          "flex items-center gap-3 p-2.5 rounded-xl transition-all duration-200",
          isUser
            ? "bg-white/10 hover:bg-white/15"
            : "bg-gray-100/50 hover:bg-gray-100/70 dark:bg-gray-700/50 dark:hover:bg-gray-700/70"
        )}
      >
        {/* Smart File Icon */}
        <div
          className={cn(
            "flex items-center justify-center w-9 h-9 rounded-xl transition-all duration-200 group-hover:scale-105",
            isUser
              ? "bg-white/20"
              : "bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/25"
          )}
        >
          {getFileIcon(filename)}
        </div>

        {/* File Details */}
        <div className="flex-1 min-w-0">
          <p
            className={cn(
              "font-medium text-sm truncate",
              isUser
                ? "text-white"
                : "text-gray-900 dark:text-gray-100"
            )}
          >
            {filename}
          </p>
          <p
            className={cn(
              "text-xs mt-0.5",
              isUser
                ? "text-white/70"
                : "text-gray-500 dark:text-gray-400"
            )}
          >
            Attached file
          </p>
        </div>

        {/* Quick Action Download Button */}
        <button
          type="button"
          className={cn(
            "p-1.5 rounded-lg transition-all duration-200 hover:scale-110 active:scale-95",
            isUser
              ? "hover:bg-white/20 text-white/80 hover:text-white"
              : "hover:bg-gray-100 text-gray-400 hover:text-gray-600 dark:hover:bg-gray-700 dark:text-gray-500 dark:hover:text-gray-300"
          )}
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </button>
      </div>

      {/* Render the user's message if it exists */}
      {userMessage && (
        <div
          className={cn(
            "px-4 py-3 rounded-2xl",
            isUser
              ? "bg-white/10 text-white border border-white/20"
              : "bg-white/60 text-gray-800 border border-gray-200/40 dark:bg-gray-800/40 dark:text-gray-200 dark:border-gray-700/40"
          )}
        >
          <p className="text-sm leading-relaxed">
            {userMessage}
          </p>
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

  // Handle attachments with the glass effect component
  const attachmentInfo = detectContentType(text);
  if (attachmentInfo) {
    return (
      <AttachmentRenderer
        filename={attachmentInfo.filename}
        userMessage={attachmentInfo.userMessage}
        isUser={isUser}
        type={attachmentInfo.type}
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
