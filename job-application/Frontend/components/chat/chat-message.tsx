"use client";

import React, { useState, useEffect, useRef } from 'react';

// Safari compatibility polyfills
const isSafari = () => {
  if (typeof window === 'undefined') return false;
  return /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
};

// Safe property access for Safari
const safeGet = (obj: any, path: string[], defaultValue: any = undefined) => {
  try {
    return path.reduce((current, key) => current && current[key], obj) || defaultValue;
  } catch {
    return defaultValue;
  }
};
import { Clipboard, Pencil, Trash2, Check, X, Bot, User, Volume2, VolumeX, Play, Pause, RefreshCw, Download, FileText, ChevronDown, Loader2, MoreHorizontal, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MessageContent } from './message-content';
import { ConfirmationDialog } from '../ui/confirmation-dialog';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { PDFGenerationDialog } from './pdf-generation-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@clerk/nextjs";
import { toast } from "@/lib/toast";

interface ChatMessageProps {
  id: string;
  content: string | object;
  isUser: boolean;
  className?: string;
  onDelete: (id: string) => void;
  onEdit: (id: string, newContent: string) => void;
  onRegenerate: (id: string) => void;
  user?: any;
}

const PDF_STYLES = [
  {
    key: "modern",
    name: "Modern",
    description: "Clean design with blue accents",
    icon: "🎨"
  },
  {
    key: "classic", 
    name: "Classic",
    description: "Traditional serif format",
    icon: "📜"
  },
  {
    key: "minimal",
    name: "Minimal", 
    description: "Simple, clean layout",
    icon: "✨"
  }
]

// Intelligent content detection based on AI agent patterns and content structure
const detectContentType = (content: string): { type: "cover_letter" | "resume" | null; companyName?: string; jobTitle?: string } => {
  const lowerContent = content.toLowerCase();
  
  // Skip if it's clearly a question or request
  const questionPatterns = [
    /can you/i,
    /could you/i,
    /please/i,
    /help me/i,
    /how to/i,
    /what/i,
    /why/i,
    /when/i,
    /where/i,
    /generate.*cover letter/i,
    /create.*cover letter/i,
    /write.*cover letter/i,
    /generate.*resume/i,
    /create.*resume/i,
    /write.*resume/i,
    /\?/
  ];
  
  // Skip if it contains question patterns
  // Check if it contains question patterns (Safari compatible)
  let hasQuestionPattern = false;
  for (let i = 0; i < questionPatterns.length; i++) {
    if (questionPatterns[i].test(content)) {
      hasQuestionPattern = true;
      break;
    }
  }
  
  if (hasQuestionPattern) {
    return { type: null };
  }
  
  // Agent-generated content indicators
  const agentIndicators = [
    /your.*is ready/i,
    /📄/,
    /here.*your/i,
    /i.*generated/i,
    /i.*created/i,
    /i.*prepared/i,
    /download.*pdf/i,
    /## /,
    /\*\*/
  ];
  
  // Must be substantial content from the agent (Safari compatible)
  let hasAgentIndicators = false;
  for (let i = 0; i < agentIndicators.length; i++) {
    if (agentIndicators[i].test(content)) {
      hasAgentIndicators = true;
      break;
    }
  }
  const isSubstantialContent = content.length > 200;
  
  if (!hasAgentIndicators || !isSubstantialContent) {
    return { type: null };
  }
  
  // Enhanced cover letter detection patterns
  const coverLetterPatterns = [
    /dear (hiring manager|recruiter|sir|madam|mr\.|ms\.|mrs\.)/i,
    /i am writing to express/i,
    /sincerely,/i,
    /best regards,/i,
    /yours faithfully,/i,
    /yours sincerely,/i,
    /thank you for considering/i,
    /i look forward to hearing/i,
    /## 📄 Cover Letter/i,
    /cover letter.*ready/i,
    /cover letter.*position/i,
    /express.*enthusiasm/i,
    /excited to apply/i,
    /position.*at/i,
    /applying.*role/i
  ];
  
  // Enhanced resume/CV detection patterns
  const resumePatterns = [
    /professional summary/i,
    /work experience/i,
    /education/i,
    /skills/i,
    /certifications/i,
    /## 📄 Resume/i,
    /## 📄 CV/i,
    /resume.*ready/i,
    /cv.*ready/i,
    /curriculum vitae/i,
    /contact information/i,
    /personal information/i,
    /technical skills/i,
    /projects/i,
    /employment history/i,
    /academic background/i,
    /core competencies/i
  ];

  // Count pattern matches (Safari compatible)
  let coverLetterScore = 0;
  for (let i = 0; i < coverLetterPatterns.length; i++) {
    if (coverLetterPatterns[i].test(content)) {
      coverLetterScore++;
    }
  }
  
  let resumeScore = 0;
  for (let i = 0; i < resumePatterns.length; i++) {
    if (resumePatterns[i].test(content)) {
      resumeScore++;
    }
  }
  
  // Determine content type based on higher score and minimum threshold
  if (coverLetterScore >= 2 && coverLetterScore > resumeScore) {
    // Extract company name and job title (Safari compatible)
    const companyMatch = content.match(/(?:at\s+|for\s+|with\s+|Cover Letter.*at\s+)([\w\s&,.-]+?)(?:\s+(?:hiring|team)|[.,]|$|\s+is\s+ready)/i);
    const jobMatch = content.match(/(?:for.*|as.*|position.*|role.*|Cover Letter for\s+)([\w\s-]+?)(?:\s+(?:position|role|at)|[.,]|$|\s+at\s+)/i);
    
    return {
      type: "cover_letter" as const,
      companyName: companyMatch && companyMatch[1] ? companyMatch[1].trim() : undefined,
      jobTitle: jobMatch && jobMatch[1] ? jobMatch[1].trim() : undefined
    };
  }
  
  if (resumeScore >= 3) {
    return { type: "resume" as const };
  }
  
  return { type: null };
};

export function ChatMessage({ 
  id,
  content, 
  isUser, 
  className,
  onDelete,
  onEdit,
  onRegenerate,
  user,
}: ChatMessageProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isFetchingAudio, setIsFetchingAudio] = useState(false);
  const [audioProgress, setAudioProgress] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [isPDFDialogOpen, setIsPDFDialogOpen] = useState(false);
  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false);
  const [downloadingStyle, setDownloadingStyle] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [originalWidth, setOriginalWidth] = useState<number | null>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const messageRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const { getToken } = useAuth();

  const isStructured = typeof content === 'object' && content !== null;
  const messageContent = isStructured ? content : { message: content as string };
  const plainTextContent = (messageContent as any).message || "";

  // Constants for message truncation
  const MAX_MOBILE_LENGTH = 400;
  const MAX_DESKTOP_LENGTH = 800;
  
  // Check if message should be truncated
  const [isMobile, setIsMobile] = useState(false);
  const [shouldTruncate, setShouldTruncate] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Check if content needs truncation
  useEffect(() => {
    const checkTruncation = () => {
      if (!contentRef.current) return;
      
      const maxLength = isMobile ? MAX_MOBILE_LENGTH : MAX_DESKTOP_LENGTH;
      const needsTruncation = plainTextContent.length > maxLength;
      setShouldTruncate(needsTruncation);
    };

    checkTruncation();
  }, [plainTextContent, isMobile]);
  
  const maxLength = isMobile ? MAX_MOBILE_LENGTH : MAX_DESKTOP_LENGTH;
  
  // Get display content based on expansion state
  const getDisplayContent = () => {
    if (!shouldTruncate || isExpanded) {
      return messageContent;
    }
    
    const truncatedText = plainTextContent.slice(0, maxLength) + '...';
    return isStructured ? { ...messageContent, message: truncatedText } : { message: truncatedText };
  };

  const displayContent = getDisplayContent();
  
  // Detect content type for PDF generation
  const contentDetection = detectContentType(plainTextContent);
  const showPDFButton = !isUser && contentDetection.type !== null;

  useEffect(() => {
    if (isEditing) {
      setEditedContent(plainTextContent);
    }
  }, [isEditing, plainTextContent]);

  // Cleanup audio on unmount or content change (Safari compatible)
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        try {
          audioRef.current.pause();
          if (audioRef.current.src) {
            const oldSrc = audioRef.current.src;
            audioRef.current.src = '';
            audioRef.current.load(); // Force Safari to release resources
            if (oldSrc.startsWith('blob:')) {
              URL.revokeObjectURL(oldSrc);
            }
          }
        } catch (error) {
          console.warn('Audio cleanup failed:', error);
        }
      }
      setIsSpeaking(false);
      setAudioProgress(0);
      setAudioError(null);
    };
  }, []);

  // Reset audio state when message content changes
  useEffect(() => {
    if (audioRef.current && isSpeaking) {
      audioRef.current.pause();
      setIsSpeaking(false);
      setAudioProgress(0);
    }
  }, [plainTextContent]);

  const handleCopy = async () => {
    try {
      // Safari-compatible clipboard handling
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(plainTextContent);
      } else {
        // Fallback for older Safari versions
        const textArea = document.createElement('textarea');
        textArea.value = plainTextContent;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setIsCopied(true);
      toast.success("Copied to clipboard!");
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('Copy failed:', error);
      toast.error("Failed to copy to clipboard");
    }
  };

  const handleDelete = () => setIsConfirmOpen(true);
  const handleConfirmDelete = () => {
    onDelete(id);
    setIsConfirmOpen(false);
  };

  const handleEdit = () => {
    // Capture original width before entering edit mode
    if (messageRef.current) {
      const rect = messageRef.current.getBoundingClientRect();
      setOriginalWidth(rect.width);
    }
    setIsEditing(true);
    setEditedContent(plainTextContent);
  };
  
  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedContent("");
    setOriginalWidth(null);
  };
  
  const handleSaveEdit = () => {
    if (editedContent.trim() !== plainTextContent && editedContent.trim() !== "") {
      onEdit(id, editedContent.trim());
      toast.success("Message updated!");
    }
    setIsEditing(false);
    setEditedContent("");
    setOriginalWidth(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isEditing) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSaveEdit();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        handleCancelEdit();
      }
    }
  };

  const handlePDFDownload = () => {
    setIsPDFDialogOpen(true);
  };

  const handleQuickPDFDownload = async (style: string) => {
    console.log('PDF Download clicked:', style);
    setIsDownloadingPDF(true);
    setDownloadingStyle(style);
    
    try {
      const token = await getToken();
      if (!token) {
        toast.error("Authentication required");
        return;
      }

      const requestBody: any = {
        content_type: contentDetection.type,
        style: style,
        content_text: plainTextContent
      };

      if (contentDetection.type === "cover_letter") {
        requestBody.company_name = contentDetection.companyName || "";
        requestBody.job_title = contentDetection.jobTitle || "";
      }

      const response = await fetch('/api/pdf/generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        
        const filename = contentDetection.type === "cover_letter" 
          ? `cover_letter_${contentDetection.companyName || 'document'}_${style}.pdf`
          : `resume_${style}.pdf`;
        
        a.download = filename.replace(/\s+/g, '_');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        toast.success(`${style.charAt(0).toUpperCase() + style.slice(1)} PDF downloaded!`, {
          description: `Saved as ${filename.replace(/\s+/g, '_')}`
        });
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to generate PDF");
      }
    } catch (error) {
      console.error('Error generating PDF:', error);
      toast.error("Failed to generate PDF");
    } finally {
      setIsDownloadingPDF(false);
      setDownloadingStyle(null);
    }
  };

  const handleReadAloud = async () => {
    // Stop current audio if playing
    if (isSpeaking && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsSpeaking(false);
      setAudioProgress(0);
      toast.success("Audio stopped");
      return;
    }

    // Clear any previous errors
    setAudioError(null);
    setIsFetchingAudio(true);
    
    try {
      // Validate content length
      if (plainTextContent.length > 5000) {
        throw new Error('Text too long for audio conversion (max 5000 characters)');
      }

      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: plainTextContent.slice(0, 5000), // Limit text length
          api_key: process.env.NEXT_PUBLIC_GOOGLE_TTS_API_KEY 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Audio generation failed (${response.status})`);
      }

      const blob = await response.blob();
      if (blob.size === 0) {
        throw new Error('Empty audio response received');
      }

      const url = URL.createObjectURL(blob);
      
      if (audioRef.current) {
        audioRef.current.src = url;
        
        // Set up audio event listeners for better tracking (Safari compatible)
        audioRef.current.onloadedmetadata = () => {
          if (audioRef.current && audioRef.current.duration) {
            setAudioDuration(audioRef.current.duration);
          } else {
            setAudioDuration(0);
          }
        };
        
        audioRef.current.ontimeupdate = () => {
          if (audioRef.current && audioRef.current.duration && audioRef.current.currentTime !== undefined) {
            const progress = (audioRef.current.currentTime / audioRef.current.duration) * 100;
            setAudioProgress(isNaN(progress) ? 0 : progress);
          }
        };
        
        audioRef.current.onended = () => {
          setIsSpeaking(false);
          setAudioProgress(0);
          toast.success("Audio finished");
          // Clean up blob URL
          URL.revokeObjectURL(url);
        };
        
        audioRef.current.onerror = () => {
          setIsSpeaking(false);
          setAudioProgress(0);
          setAudioError('Failed to play audio');
          toast.error("Audio playback failed");
          URL.revokeObjectURL(url);
        };

        // Start playing (Safari requires user interaction)
        try {
          await audioRef.current.play();
          setIsSpeaking(true);
          toast.success("Playing audio...", {
            description: `${Math.round(plainTextContent.length / 150)} seconds estimated`
          });
        } catch (playError) {
          console.error('Audio play failed:', playError);
          setAudioError('Audio playback failed - user interaction required');
          toast.error("Audio playback failed", { 
            description: "Safari requires user interaction to play audio"
          });
          URL.revokeObjectURL(url);
        }
      }
    } catch (error) {
      console.error("TTS error:", error);
      const errorMessage = error instanceof Error ? error.message : 'Text-to-speech failed';
      setAudioError(errorMessage);
      toast.error("Audio generation failed", { 
        description: errorMessage 
      });
    } finally {
      setIsFetchingAudio(false);
    }
  };
  
  const isAttachment = typeof messageContent === 'object' && 'message' in messageContent && typeof (messageContent as any).message === 'string' && (messageContent as any).message.startsWith('📄 **CV/Resume uploaded successfully!**') || (messageContent as any).message.startsWith('📎 Attached file:');

  return (
    <>
      <audio ref={audioRef} className="hidden" />
      <div 
        data-chat-message="true"
        className={cn(
          "group relative flex items-start transition-all duration-300 ease-out",
          "gap-2 sm:gap-3 md:gap-4 py-4 sm:py-5 md:py-6 px-3 sm:px-4 md:px-6",
          isUser ? "justify-end" : "justify-start",
          "rounded-2xl mx-1 sm:mx-2"
        )}
        onMouseEnter={() => {
          setIsHovered(true);
          setShowActions(true);
        }}
        onMouseLeave={() => {
          setIsHovered(false);
          setTimeout(() => setShowActions(false), 150);
        }}
      >
        {!isUser && (
          <div className="flex h-8 w-8 sm:h-10 sm:w-10 lg:h-12 lg:w-12 shrink-0 select-none items-center justify-center rounded-xl sm:rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-blue-600 shadow-lg shadow-blue-500/25 ring-2 ring-white/20 dark:ring-black/20 transition-all duration-300 group-hover:shadow-xl group-hover:shadow-blue-500/30 group-hover:scale-105">
            <Bot className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 text-white drop-shadow-sm" />
            <div className="absolute inset-0 rounded-xl sm:rounded-2xl bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
        )}

        <div className={cn(
          "flex flex-col relative", 
          "w-auto min-w-[120px] max-w-[85%] sm:max-w-[80%] md:max-w-[75%] lg:max-w-[70%] xl:max-w-[65%] 2xl:max-w-[60%]",
          isUser ? "items-end" : "items-start"
        )}>
          <div 
            ref={messageRef}
            className={cn(
              "relative rounded-2xl sm:rounded-3xl shadow-xl backdrop-blur-sm border transition-all duration-300 ease-out",
              isEditing ? "min-w-[300px] max-w-full" : "w-fit min-w-[100px] max-w-full",
              "px-4 py-3 sm:px-5 sm:py-4 md:px-6 md:py-5 lg:px-7 lg:py-6",
              isUser 
                ? cn(
                    "bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 text-white border-white/30 shadow-blue-500/30",
                    "hover:from-blue-600 hover:via-blue-700 hover:to-purple-700 hover:shadow-2xl hover:shadow-blue-500/40",
                    "dark:border-white/20"
                  )
                : cn(
                    "bg-gradient-to-br from-white via-gray-50/80 to-blue-50/50 text-foreground border-gray-200/60 shadow-gray-900/10",
                    "hover:from-white hover:via-blue-50/90 hover:to-purple-50/60 hover:shadow-2xl hover:shadow-gray-900/15 hover:border-gray-300/80",
                    "dark:from-gray-800/80 dark:via-gray-800/60 dark:to-blue-900/20 dark:border-gray-700/50 dark:shadow-white/5",
                    "dark:hover:from-gray-800/90 dark:hover:via-gray-700/80 dark:hover:to-blue-900/30 dark:hover:border-gray-600/60 dark:hover:shadow-white/10"
                  ),
              isEditing && "ring-2 ring-blue-500/50 shadow-blue-500/25",
              "hover:scale-[1.01] active:scale-[0.99] transform-gpu"
            )}
            style={isEditing && originalWidth ? { width: `${originalWidth}px` } : undefined}
          >
            {/* Subtle gradient overlay for enhanced depth */}
            <div className={cn(
              "absolute inset-0 rounded-2xl sm:rounded-3xl pointer-events-none transition-opacity duration-300",
              isUser 
                ? "bg-gradient-to-br from-white/10 via-transparent to-black/5 opacity-60 group-hover:opacity-80" 
                : "bg-gradient-to-br from-white/60 via-white/20 to-transparent opacity-40 group-hover:opacity-60 dark:from-white/5 dark:via-white/2 dark:to-transparent dark:opacity-20 dark:group-hover:opacity-30"
            )} />
            
            {isEditing ? (
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                onKeyDown={handleKeyDown}
                className={cn(
                  "relative z-10 w-full min-h-[4rem] bg-transparent border-none outline-none resize-none text-inherit font-inherit leading-relaxed",
                  "focus:ring-0 focus:outline-none placeholder:text-current/50",
                  "scrollbar-thin scrollbar-thumb-current/20 scrollbar-track-transparent"
                )}
                style={{ 
                  fontSize: 'inherit', 
                  lineHeight: 'inherit',
                  fontFamily: 'inherit',
                  color: 'inherit',
                  minWidth: '250px',
                  width: '100%'
                }}
                autoFocus
                rows={Math.max(3, editedContent.split('\n').length)}
                placeholder="Edit your message..."
              />
            ) : (
              <div 
                ref={contentRef}
                className={cn(
                  "prose prose-sm dark:prose-invert max-w-none relative z-10 break-words",
                  isUser ? "prose-invert" : "",
                  // Enhanced mobile typography
                  "text-sm leading-[1.5] prose-p:text-sm prose-p:leading-[1.5] prose-p:mb-3 prose-p:break-words",
                  "prose-headings:text-base prose-headings:mb-3 prose-headings:mt-0 prose-headings:font-semibold prose-headings:break-words prose-headings:leading-[1.4]",
                  "prose-ul:text-sm prose-ul:mb-3 prose-ol:text-sm prose-ol:mb-3 prose-ul:mt-1 prose-ol:mt-1",
                  "prose-li:text-sm prose-li:mb-1 prose-li:leading-[1.5] prose-li:break-words",
                  "prose-strong:text-sm prose-em:text-sm prose-code:text-xs",
                  // Enhanced desktop typography
                  "sm:text-base sm:leading-7 sm:prose-p:text-base sm:prose-p:leading-7 sm:prose-p:mb-4",
                  "sm:prose-headings:text-lg sm:prose-headings:mb-4 sm:prose-headings:leading-8",
                  "sm:prose-ul:text-base sm:prose-ul:mb-4 sm:prose-ol:text-base sm:prose-ol:mb-4 sm:prose-ul:mt-2 sm:prose-ol:mt-2",
                  "sm:prose-li:text-base sm:prose-li:mb-2 sm:prose-li:leading-7",
                  "sm:prose-strong:text-base sm:prose-em:text-base sm:prose-code:text-sm",
                  "prose-strong:font-semibold prose-em:italic",
                  "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
                  "prose-ul:space-y-1 prose-ol:space-y-1 sm:prose-ul:space-y-2 sm:prose-ol:space-y-2",
                  "[&>*+*]:mt-2 sm:[&>*+*]:mt-4",
                  "overflow-wrap-anywhere hyphens-auto word-break-break-word",
                  "w-auto min-w-0 max-w-full",
                  // Enhanced link styling
                  "prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline prose-a:font-medium hover:prose-a:underline",
                  // Enhanced code styling
                  "prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:font-mono"
                )}
              >
                <MessageContent content={displayContent} />
                
                {/* Enhanced Show More/Less Button */}
                {shouldTruncate && (
                  <span className="inline">
                    {!isExpanded && "... "}
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setIsExpanded(!isExpanded);
                        toast.success(isExpanded ? "Collapsed message" : "Expanded message");
                      }}
                      className={cn(
                        "text-sm sm:text-base font-medium transition-all duration-200 cursor-pointer bg-transparent border-none p-0 ml-1",
                        "inline-flex items-center gap-1 hover:gap-2",
                        "rounded-lg px-2 py-1 hover:bg-black/10 dark:hover:bg-white/10",
                        isUser 
                          ? "text-white/80 hover:text-white hover:bg-white/20" 
                          : "text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                      )}
                      type="button"
                    >
                      <Sparkles className="h-3 w-3 opacity-70" />
                      {isExpanded 
                        ? "Show less" 
                        : `Show more (+${plainTextContent.length - maxLength} chars)`
                      }
                    </button>
                  </span>
                )}
              </div>
            )}

            {/* Enhanced PDF Download Badge */}
            {showPDFButton && (
              <div className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 z-20 pointer-events-auto">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      className={cn(
                        "group/pdf flex items-center gap-1.5 px-3 py-2 bg-gradient-to-r from-emerald-500 to-blue-600 hover:from-emerald-600 hover:to-blue-700 text-white text-xs font-medium rounded-xl shadow-lg backdrop-blur-sm transition-all duration-300 hover:scale-110 hover:shadow-xl active:scale-95 border border-white/30 cursor-pointer pointer-events-auto touch-manipulation",
                        "hover:shadow-emerald-500/25 hover:border-white/50",
                        isDownloadingPDF && "animate-pulse"
                      )}
                      title={`Download ${contentDetection.type === 'cover_letter' ? 'Cover Letter' : 'Resume'} as PDF`}
                      disabled={isDownloadingPDF}
                      type="button"
                    >
                      {isDownloadingPDF ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <>
                          <FileText className="h-3 w-3 group-hover/pdf:scale-110 transition-transform" />
                          <Download className="h-3 w-3 group-hover/pdf:scale-110 transition-transform" />
                        </>
                      )}
                      <span className="font-semibold">
                        {isDownloadingPDF ? "Generating..." : "PDF"}
                      </span>
                      <ChevronDown className="h-2.5 w-2.5 group-hover/pdf:scale-110 transition-transform" />
                      <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 opacity-0 group-hover/pdf:opacity-100 transition-opacity rounded-xl" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 shadow-2xl">
                    <div className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200/50 dark:border-gray-700/50">
                      Choose PDF Style
                    </div>
                    {PDF_STYLES.map((style) => (
                      <DropdownMenuItem
                        key={style.key}
                        onClick={() => handleQuickPDFDownload(style.key)}
                        disabled={isDownloadingPDF}
                        className={cn(
                          "cursor-pointer transition-colors duration-200 hover:bg-blue-50 dark:hover:bg-blue-950/50",
                          downloadingStyle === style.key && "bg-blue-100 dark:bg-blue-900/30"
                        )}
                      >
                        <div className="flex items-center gap-3 w-full">
                          <span className="text-lg">{style.icon}</span>
                          <div className="flex-1">
                            <div className="font-medium">{style.name}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">{style.description}</div>
                          </div>
                          {downloadingStyle === style.key && (
                            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                          )}
                        </div>
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            )}
          </div>
          
          {/* Enhanced Action Buttons */}
          <div className={cn(
            "flex items-center gap-1 mt-2 px-2 transition-all duration-300 ease-out",
            isUser ? "justify-end" : "justify-start",
            "transform",
            showActions || isEditing ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
          )}>
            {isEditing ? (
              <div className="flex items-center gap-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-xl px-3 py-2 shadow-lg border border-gray-200/50 dark:border-gray-700/50">
                <Button 
                  onClick={handleSaveEdit}
                  size="sm"
                  className="h-8 px-3 bg-green-600 hover:bg-green-700 text-white text-xs font-medium shadow-sm"
                >
                  <Check className="h-3 w-3 mr-1" />
                  Save
                </Button>
                <Button 
                  onClick={handleCancelEdit}
                  variant="outline"
                  size="sm"
                  className="h-8 px-3 text-xs font-medium"
                >
                  <X className="h-3 w-3 mr-1" />
                  Cancel
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-1 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl px-2 py-1.5 shadow-lg border border-gray-200/50 dark:border-gray-700/50">
                {!isUser && (
                  <div className="relative group/audio">
                    <button 
                      onClick={handleReadAloud}
                      className={cn(
                        "relative p-2 rounded-lg transition-all duration-200 hover:scale-110 active:scale-95 touch-manipulation overflow-hidden",
                        isFetchingAudio && "cursor-not-allowed opacity-70",
                        isSpeaking ? "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 shadow-md" : 
                        audioError ? "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400" :
                        "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                      )}
                      disabled={isFetchingAudio}
                      title={
                        isFetchingAudio ? "Generating audio..." :
                        isSpeaking ? `Stop audio (${Math.round(audioProgress)}% complete)` : 
                        audioError ? `Audio error: ${audioError}` :
                        `Read aloud (${Math.round(plainTextContent.length / 150)}s estimated)`
                      }
                    >
                      {/* Progress bar for speaking */}
                      {isSpeaking && (
                        <div 
                          className="absolute bottom-0 left-0 h-0.5 bg-blue-500 transition-all duration-100 ease-linear"
                          style={{ width: `${audioProgress}%` }}
                        />
                      )}
                      
                      {/* Icon with enhanced states */}
                      {isFetchingAudio ? (
                        <div className="flex items-center justify-center">
                          <Loader2 className="h-4 w-4 animate-spin" />
                        </div>
                      ) : isSpeaking ? (
                        <div className="flex items-center justify-center">
                          <Pause className="h-4 w-4" />
                        </div>
                      ) : audioError ? (
                        <div className="flex items-center justify-center">
                          <VolumeX className="h-4 w-4" />
                        </div>
                      ) : (
                        <div className="flex items-center justify-center group-hover/audio:scale-110 transition-transform">
                          <Volume2 className="h-4 w-4" />
                        </div>
                      )}
                    </button>
                    
                    {/* Enhanced tooltip for audio progress */}
                    {isSpeaking && audioDuration > 0 && (
                      <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 px-2 py-1 bg-black/80 text-white text-xs rounded opacity-0 group-hover/audio:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                        {Math.round((audioProgress / 100) * audioDuration)}s / {Math.round(audioDuration)}s
                      </div>
                    )}
                  </div>
                )}
                
                {!isAttachment && (
                  <button 
                    onClick={handleCopy}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 hover:scale-110 active:scale-95 touch-manipulation"
                    title="Copy message"
                  >
                    {isCopied ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <Clipboard className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    )}
                  </button>
                )}
                
                {isUser && !isAttachment && (
                  <button 
                    onClick={handleEdit}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 hover:scale-110 active:scale-95 touch-manipulation"
                    title="Edit message"
                  >
                    <Pencil className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                  </button>
                )}
                
                {!isUser && (
                  <button 
                    onClick={() => onRegenerate(id)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 hover:scale-110 active:scale-95 touch-manipulation"
                    title="Regenerate response"
                  >
                    <RefreshCw className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                  </button>
                )}
                
                <button 
                  onClick={handleDelete}
                  className="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400 transition-all duration-200 hover:scale-110 active:scale-95 touch-manipulation"
                  title="Delete message"
                >
                  <Trash2 className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                </button>
              </div>
            )}
          </div>
        </div>

        {isUser && (
          <div className="flex h-8 w-8 sm:h-10 sm:w-10 lg:h-12 lg:w-12 shrink-0 select-none items-center justify-center rounded-xl sm:rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 shadow-lg ring-2 ring-white/20 dark:ring-black/20 overflow-hidden transition-all duration-300 group-hover:shadow-xl group-hover:scale-105">
            {user && user.imageUrl ? (
              <img src={user.imageUrl} alt="User" className="h-full w-full object-cover" />
            ) : (
              <User className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 text-gray-600 dark:text-gray-300" strokeWidth={1.5} />
            )}
            <div className="absolute inset-0 rounded-xl sm:rounded-2xl bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
        )}
      </div>
      
      <ConfirmationDialog
        open={isConfirmOpen}
        onOpenChange={setIsConfirmOpen}
        onConfirm={handleConfirmDelete}
        title="Delete message?"
        description="This will delete the message and all subsequent messages in the conversation. This action cannot be undone."
      />

      {/* PDF Generation Dialog */}
      {showPDFButton && (
        <PDFGenerationDialog
          open={isPDFDialogOpen}
          onOpenChange={setIsPDFDialogOpen}
          contentType={contentDetection.type!}
          initialContent={plainTextContent}
          companyName={contentDetection.companyName}
          jobTitle={contentDetection.jobTitle}
        />
      )}
    </>
  );
} 

 