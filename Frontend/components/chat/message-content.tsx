"use client";

import { cn } from "@/lib/utils";
import { ExternalLink, File, FileText, Image } from "lucide-react";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MessageContentProps {
  content: any;
  isUser?: boolean;
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

// Content type detector
const detectContentType = (text: string) => {
  // All possible attachment patterns (covers current and legacy formats)
  const patterns = {
    // Current clean formats
    fileAttached: /\*\*File Attached:\*\* (.+?)(?:\n|$)/,
    cvUploaded:
      /\*\*CV\/Resume uploaded successfully!\*\*[\s\S]*?\*\*File:\*\* (.+?)(?:\n|$)/,

    // Legacy formats with emojis
    emojiFileAttached: /📎 \*\*File Attached:\*\* (.+?)(?:\n|$)/,
    emojiCvUploaded:
      /📄 \*\*CV\/Resume uploaded successfully!\*\*[\s\S]*?\*\*File:\*\* (.+?)(?:\n|$)/,

    // Old legacy formats
    attachedFile: /📎 Attached file:\s*(.+?)(?:\n|$)/i,
    plainAttachedFile: /Attached file:\s*(.+?)(?:\n|$)/i,
  };

  // Check each pattern
  for (const [type, pattern] of Object.entries(patterns)) {
    const match = text.match(pattern);
    if (match) {
      return {
        type: type.includes("cv") || type.includes("Cv") ? "cv" : "file",
        filename: match[1].trim(),
        fullMatch: match[0],
        isLegacy: type.includes("emoji") || type.includes("attached"),
      };
    }
  }

  return null;
};

// Attachment renderer component
const AttachmentRenderer = ({
  filename,
  text,
  isUser,
}: {
  filename: string;
  text: string;
  isUser?: boolean;
}) => {
  // Extract user message if present
  const messageMatch = text.match(/\*\*Message:\*\* ([\s\S]+?)(?:\n|$)/);
  const userMessage = messageMatch ? messageMatch[1].trim() : "";

  return (
    <div className="space-y-3">
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

      {/* User message if present */}
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

// Main content dispatcher
export function MessageContent({ content, isUser }: MessageContentProps) {
  if (!content) return null;

  const text = typeof content === "string" ? content : content.message || "";
  if (typeof text !== "string") return null;

  // Detect if this is an attachment message
  const attachmentInfo = detectContentType(text);

  if (attachmentInfo) {
    return (
      <AttachmentRenderer
        filename={attachmentInfo.filename}
        text={text}
        isUser={isUser}
      />
    );
  }

  // Regular message content with enhanced link handling
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: (props: any) => <LinkComponent {...props} isUser={isUser} />,
        // Enhanced paragraph styling
        p: ({ children, ...props }) => (
          <p className="mb-2 last:mb-0" {...props}>
            {children}
          </p>
        ),
        // Enhanced list styling
        ul: ({ children, ...props }) => (
          <ul className="list-disc list-inside space-y-1 mb-2" {...props}>
            {children}
          </ul>
        ),
        ol: ({ children, ...props }) => (
          <ol className="list-decimal list-inside space-y-1 mb-2" {...props}>
            {children}
          </ol>
        ),
        // Enhanced code styling
        code: ({ inline, children, ...props }: any) =>
          inline ? (
            <code
              className="bg-muted px-1 py-0.5 rounded text-sm font-mono"
              {...props}
            >
              {children}
            </code>
          ) : (
            <code
              className="block bg-muted p-2 rounded text-sm font-mono overflow-x-auto"
              {...props}
            >
              {children}
            </code>
          ),
      }}
    >
      {text}
    </ReactMarkdown>
  );
}
