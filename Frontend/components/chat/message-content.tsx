"use client";

import React from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileText, Image, File } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MessageContentProps {
  content: any;
}

// File icon helper
const getFileIcon = (filename: string) => {
  const extension = filename.split('.').pop()?.toLowerCase() || '';
  const iconClass = "h-4 w-4";
  
  if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'tiff'].includes(extension)) {
    return <Image className={iconClass} />;
  }
  if (['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'].includes(extension)) {
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
    cvUploaded: /\*\*CV\/Resume uploaded successfully!\*\*[\s\S]*?\*\*File:\*\* (.+?)(?:\n|$)/,
    
    // Legacy formats with emojis
    emojiFileAttached: /📎 \*\*File Attached:\*\* (.+?)(?:\n|$)/,
    emojiCvUploaded: /📄 \*\*CV\/Resume uploaded successfully!\*\*[\s\S]*?\*\*File:\*\* (.+?)(?:\n|$)/,
    
    // Old legacy formats
    attachedFile: /📎 Attached file:\s*(.+?)(?:\n|$)/i,
    plainAttachedFile: /Attached file:\s*(.+?)(?:\n|$)/i,
  };

  // Check each pattern
  for (const [type, pattern] of Object.entries(patterns)) {
    const match = text.match(pattern);
    if (match) {
      return {
        type: type.includes('cv') || type.includes('Cv') ? 'cv' : 'file',
        filename: match[1].trim(),
        fullMatch: match[0],
        isLegacy: type.includes('emoji') || type.includes('attached')
      };
    }
  }

  return null;
};

// Attachment renderer component
const AttachmentRenderer = ({ filename, text }: { filename: string; text: string }) => {
  // Extract user message if present
  const messageMatch = text.match(/\*\*Message:\*\* ([\s\S]+?)(?:\n|$)/);
  const userMessage = messageMatch ? messageMatch[1].trim() : '';

  return (
    <div className="space-y-3">
      {/* File attachment display */}
      <div className={cn(
        "flex items-center gap-3 p-3 rounded-lg border",
        "bg-muted/30 border-border/50 hover:bg-muted/40 transition-colors"
      )}>
        <div className="flex items-center justify-center h-8 w-8 shrink-0 rounded-md bg-primary text-primary-foreground">
          {getFileIcon(filename)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-foreground text-sm truncate">
            {filename}
          </p>
          <p className="text-xs text-muted-foreground">
            {filename.split('.').pop()?.toUpperCase() || 'FILE'} file
          </p>
        </div>
      </div>

      {/* User message if present */}
      {userMessage && (
        <div className="text-sm text-foreground">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {userMessage}
          </ReactMarkdown>
        </div>
      )}

      {/* CV upload success details */}
      {text.includes('CV/Resume uploaded successfully') && (
        <div className="text-sm text-muted-foreground mt-2 space-y-1">
          {text.includes('Profile Updated') && (
            <p className="text-green-600 dark:text-green-400 font-medium">
              ✅ Profile automatically updated
            </p>
          )}
          <p className="text-xs">
            CV processed and ready for job applications
          </p>
        </div>
      )}
    </div>
  );
};

// Main content dispatcher
export function MessageContent({ content }: MessageContentProps) {
  if (!content) return null;

  const text = typeof content === 'string' ? content : content.message || '';
  if (typeof text !== 'string') return null;

  // Detect if this is an attachment message
  const attachmentInfo = detectContentType(text);
  
  if (attachmentInfo) {
    return <AttachmentRenderer filename={attachmentInfo.filename} text={text} />;
  }

  // Regular message content
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]}>
      {text}
    </ReactMarkdown>
  );
} 