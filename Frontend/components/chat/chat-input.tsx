"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, X, FileText, Image, File, Eye, EyeOff, Download } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@clerk/nextjs';
import { toast } from '@/lib/toast';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onStopGeneration?: () => void;
  isConnected: boolean;
  isLoading: boolean;
  placeholder?: string;
}

export function ChatInput({ 
  onSendMessage, 
  isLoading, 
  placeholder 
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showHelperText, setShowHelperText] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const { getToken } = useAuth();
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Recording timer effect
  useEffect(() => {
    if (isRecording) {
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prevTime => prevTime + 1);
      }, 1000);
    } else {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      setRecordingTime(0);
    }
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, [isRecording]);

  // Mobile detection effect
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Auto-resize textarea function
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;
      const maxHeight = 120; // Max height in pixels (about 4 lines)
      textarea.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  };

  // Handle message change with auto-resize
  const handleMessageChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    adjustTextareaHeight();
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // If there's a selected file, upload it with the message
    if (selectedFile) {
      const textMessage = message.trim();
      await handleSendAttachment(textMessage);
      return;
    }
    
    // Regular message sending
    if (!message.trim() || isLoading) return;

    const messageToSend = message.trim();
    setMessage('');
    
    // Reset textarea height after clearing message
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.focus();
      }
    }, 0);

    onSendMessage(messageToSend);
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Shift+Enter: Allow new line
        return;
      } else {
        // Enter: Send message
        e.preventDefault();
        handleSubmit(e);
      }
    }
  };

  // Handle file selection (show preview before upload)
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      toast.error("File size must be less than 10MB");
      return;
    }

    // Store the selected file for preview
    setSelectedFile(file);
    
    // Reset file input for next selection
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle attachment upload and send
  const handleSendAttachment = async (textMessage: string = '') => {
    if (!selectedFile) return;

    // Check if it's a CV/resume file
    const isCVFile = selectedFile.type === 'application/pdf' || 
                     selectedFile.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                     selectedFile.type === 'application/msword' ||
                     selectedFile.name.toLowerCase().includes('cv') ||
                     selectedFile.name.toLowerCase().includes('resume');

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    
    if (isCVFile) {
      formData.append("name", selectedFile.name);
      formData.append("auto_update_profile", "true");
    }

    try {
      const token = await getToken();
      const endpoint = isCVFile ? '/api/documents/cv-upload' : '/api/upload';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      
      if (!response.ok) {
        let errorMessage = 'Upload failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      
      // Create the combined message
      let combinedMessage = '';
      
      if (isCVFile && result.extracted_info) {
        // Handle CV upload with extraction results - No emoji, clean format
        combinedMessage = `**CV/Resume uploaded successfully!**\n\n`;
        combinedMessage += `**File:** ${result.document.name}\n`;
        
        if (result.profile_updated && result.auto_extracted_fields?.length > 0) {
          combinedMessage += `**Profile Updated:** ✅ Automatically updated ${result.auto_extracted_fields.join(', ')}\n`;
        }
        
        if (result.extracted_info.confidence_score) {
          combinedMessage += `**Extraction Confidence:** ${(result.extracted_info.confidence_score * 100).toFixed(0)}%\n`;
        }
        
        combinedMessage += `\nYour CV has been processed and is now available for job applications and analysis. I can help you with job applications, interview preparation, or answer questions about your background.`;
        
        // Show success toast
        toast.success("CV uploaded successfully!", {
          description: result.profile_updated 
            ? `Profile auto-updated with ${result.auto_extracted_fields?.length || 0} fields`
            : "CV processed and ready for use"
        });
      } else {
        // Handle regular file upload - No emoji, clean format
        combinedMessage = `**File Attached:** ${result.filename || selectedFile.name}`;
        toast.success("File uploaded successfully!");
      }
      
      // Add the text message if provided
      if (textMessage && textMessage.trim()) {
        combinedMessage += `\n\n**Message:** ${textMessage.trim()}`;
      }
      
      // Send the combined message
      onSendMessage(combinedMessage);

      // Clear all state
      setSelectedFile(null);
      setMessage('');
      
      // Reset textarea height
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
          textareaRef.current.focus();
        }
      }, 0);
      
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error("File upload failed", { description: errorMessage });
    } finally {
      setIsUploading(false);
    }
  };

  // Cancel attachment
  const handleCancelAttachment = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Start voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const audioChunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.wav");
        formData.append("api_key", process.env.NEXT_PUBLIC_GOOGLE_TTS_API_KEY || "");
        
        try {
          const response = await fetch('/api/stt', {
            method: 'POST',
            body: formData,
          });
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Transcription failed');
          }
          const result = await response.json();
          onSendMessage(result.transcript);
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : 'Transcription failed';
          toast.error("Transcription failed", { description: errorMessage });
        }
      };
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch {
      toast.error("Microphone access error", { description: "Could not access microphone." });
    }
  };

  // Stop voice recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };
  
  // Cancel voice recording
  const cancelRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.onstop = () => {}; // Prevent processing
      setIsRecording(false);
    }
  };

  // Format recording time
  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = time % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Get file icon based on type
  const getFileIcon = (file: File) => {
    const fileType = file.type;
    const fileName = file.name.toLowerCase();
    
    if (fileType.startsWith('image/')) {
      return <Image className="h-5 w-5" />;
    }
    if (fileType.includes('pdf') || fileType.includes('word') || fileName.includes('.doc')) {
      return <FileText className="h-5 w-5" />;
    }
    return <File className="h-5 w-5" />;
  };

  return (
    <div className="w-full space-y-3">
      {/* Attachment Preview */}
      {selectedFile && (
        <div className={cn(
          "flex items-center gap-3 p-3 rounded-lg border group",
          "bg-muted/30 border-border/20 hover:bg-muted/50",
          "transition-all duration-200 hover:shadow-md"
        )}>
          <div className="flex items-center gap-3 flex-1">
            {/* File icon */}
            <div className="flex items-center justify-center h-10 w-10 shrink-0 rounded-md bg-primary text-primary-foreground">
              {getFileIcon(selectedFile)}
            </div>
            
            {/* File info */}
            <div className="flex-1 min-w-0">
              <p className="font-semibold truncate text-foreground text-sm">
                {selectedFile.name}
              </p>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
                </span>
                <div className="px-2 py-0.5 rounded-md text-xs font-medium bg-secondary text-secondary-foreground">
                  Ready to send
                </div>
              </div>
            </div>
          </div>
          
          {/* Remove button */}
          <button
            type="button"
            onClick={handleCancelAttachment}
            className={cn(
              "p-1.5 text-muted-foreground hover:text-destructive",
              "hover:bg-destructive/10 rounded-md transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-ring"
            )}
            title="Remove attachment"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Chat Input Form */}
      <form onSubmit={handleSubmit} className="w-full">
        <div className={cn(
          "relative flex items-end gap-3 transition-all duration-300",
          "p-3 sm:p-4 rounded-2xl border",
          "bg-card/60 backdrop-blur-sm border-border/30 shadow-xl",
          "focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary/50 focus-within:shadow-2xl",
          "hover:bg-card/75 hover:border-border/50 hover:shadow-2xl",
          "relative overflow-hidden",
          selectedFile && "ring-2 ring-primary/30 border-primary/50"
        )}>
          
          {/* Glassmorphism gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-background/10 via-transparent to-primary/5 rounded-2xl pointer-events-none" />
          
          {isRecording ? (
            // Recording mode
            <div className="flex items-center justify-between w-full relative z-10">
              <button 
                type="button" 
                onClick={cancelRecording} 
                className={cn(
                  "flex items-center justify-center p-2 sm:p-2.5",
                  "text-destructive hover:text-destructive/80",
                  "hover:bg-destructive/10 rounded-xl transition-all duration-200",
                  "hover:scale-105 active:scale-95"
                )}
              >
                <Mic className="h-4 w-4 sm:h-5 sm:w-5 animate-pulse" />
              </button>
              
              <div className="text-sm font-mono text-muted-foreground px-4 py-2 bg-muted/30 rounded-lg backdrop-blur-sm">
                🔴 {formatTime(recordingTime)}
              </div>
              
              <button 
                type="button" 
                onClick={stopRecording} 
                className={cn(
                  "flex items-center justify-center p-2 sm:p-2.5",
                  "bg-gradient-to-br from-blue-500 to-purple-600 text-white",
                  "hover:from-blue-600 hover:to-purple-700 rounded-xl",
                  "transition-all duration-200 hover:scale-105 active:scale-95",
                  "shadow-lg hover:shadow-xl border border-white/20"
                )}
              >
                <Send className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>
            </div>
          ) : (
            // Normal input mode
            <>
              {/* File upload button */}
              <button 
                type="button" 
                onClick={() => fileInputRef.current?.click()} 
                disabled={isUploading}
                className={cn(
                  "flex items-center justify-center p-2 sm:p-2.5 relative z-10",
                  "text-muted-foreground hover:text-foreground",
                  "hover:bg-accent/50 rounded-xl transition-all duration-200",
                  "hover:scale-105 active:scale-95",
                  "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                )}
              >
                <Paperclip className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>
              
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                className="hidden" 
                accept=".pdf,.doc,.docx,.txt,.rtf,.xls,.xlsx,.csv,image/*,video/*,audio/*" 
              />
              
              {/* Text input area */}
              <div className="flex-1 min-w-0 relative z-10">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={handleMessageChange}
                  onKeyDown={handleKeyDown}
                  placeholder={selectedFile 
                    ? `Add a message with "${selectedFile.name}"...`
                    : placeholder || (isMobile 
                      ? "Type a message... (Return for new line)"
                      : "Type a message... (Enter to send, Shift+Enter for new line)")
                  }
                  className={cn(
                    "w-full bg-transparent border-none focus:outline-none resize-none",
                    "text-sm sm:text-base text-foreground placeholder:text-muted-foreground/60",
                    "min-h-[20px] max-h-[120px] overflow-y-auto",
                    "leading-relaxed"
                  )}
                  rows={1}
                  style={{ height: 'auto' }}
                />
              </div>
              
              {/* Send/Mic button */}
              {(message.trim() || selectedFile) ? (
                <button
                  type="submit"
                  disabled={isLoading || isUploading}
                  className={cn(
                    "flex items-center justify-center p-2 sm:p-2.5 relative z-10",
                    "bg-gradient-to-br from-blue-500 to-purple-600 text-white",
                    "hover:from-blue-600 hover:to-purple-700 rounded-xl sm:rounded-2xl",
                    "transition-all duration-200 hover:scale-105 active:scale-95",
                    "shadow-lg hover:shadow-xl border border-white/20",
                    "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100",
                    (isLoading || isUploading) && "animate-pulse"
                  )}
                  title={selectedFile ? `Send${message.trim() ? ' message with attachment' : ' attachment'}` : 'Send message'}
                >
                  {isUploading ? (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                    </div>
                  ) : (
                    <Send className="h-4 w-4 sm:h-5 sm:w-5" />
                  )}
                </button>
              ) : (
                <button 
                  type="button" 
                  onClick={startRecording} 
                  className={cn(
                    "flex items-center justify-center p-2 sm:p-2.5 relative z-10",
                    "text-muted-foreground hover:text-foreground",
                    "hover:bg-accent/50 rounded-xl transition-all duration-200",
                    "hover:scale-105 active:scale-95"
                  )}
                >
                  <Mic className="h-4 w-4 sm:h-5 sm:w-5" />
                </button>
              )}
            </>
          )}
        </div>
      </form>
      
      {/* Enhanced Helper text with mobile-optimized layout */}
      <div className="flex justify-center items-center gap-2">
        {showHelperText && (
          <div className={cn(
            // Mobile-first responsive container
            "flex flex-col sm:inline-flex sm:flex-row items-center gap-1.5 sm:gap-2",
            "px-3 py-2 sm:px-4 sm:py-2 rounded-xl sm:rounded-xl",
            "bg-white/60 dark:bg-gray-800/60 backdrop-blur-md",
            "border border-gray-200/30 dark:border-gray-700/30",
            "shadow-lg shadow-black/5 dark:shadow-black/20",
            "text-xs text-gray-600 dark:text-gray-300",
            "transition-all duration-300 ease-out max-w-xs sm:max-w-none"
          )}>
            
            {/* Mobile Layout - Download instruction only */}
            <div className="flex sm:hidden flex-col items-center gap-1 text-center">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <div className="w-6 h-6 rounded-md bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <Download className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                  </div>
                  <span className="text-gray-600 dark:text-gray-300 font-medium">Click the download icon to download content</span>
                </div>
              </div>
            </div>

            {/* Desktop Layout - Horizontal */}
            <div className="hidden sm:flex items-center gap-2">
              <div className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-600 rounded text-xs font-mono text-gray-700 dark:text-gray-200">
                  Enter
                </kbd>
                <span className="text-gray-500 dark:text-gray-300">to send</span>
              </div>
              <span className="text-gray-400 dark:text-gray-500">•</span>
              <div className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-600 rounded text-xs font-mono text-gray-700 dark:text-gray-200">
                  Shift+Enter
                </kbd>
                <span className="text-gray-500 dark:text-gray-300">for new line</span>
              </div>
              <span className="text-gray-400 dark:text-gray-500">•</span>
              <span className="text-gray-500 dark:text-gray-300">
                Upload CV, ask questions, get help
              </span>
            </div>
          </div>
        )}
        
        {/* Toggle button with mobile optimization */}
        <button
          type="button"
          onClick={() => setShowHelperText(!showHelperText)}
          className={cn(
            "flex items-center justify-center p-2 rounded-lg",
            "text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300",
            "hover:bg-gray-100/50 dark:hover:bg-gray-800/50",
            "transition-all duration-200 hover:scale-105 active:scale-95",
            "border border-gray-200/30 dark:border-gray-700/30",
            "bg-white/30 dark:bg-gray-800/30 backdrop-blur-sm",
            "touch-none select-none" // Prevent text selection on mobile
          )}
          title={showHelperText ? "Hide helper text" : "Show helper text"}
        >
          {showHelperText ? (
            <EyeOff className="h-3 w-3" />
          ) : (
            <Eye className="h-3 w-3" />
          )}
        </button>
      </div>
    </div>
  );
} 