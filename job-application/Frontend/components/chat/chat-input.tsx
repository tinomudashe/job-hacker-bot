"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip } from 'lucide-react';
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

  // Handle file upload
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      toast.error("File size must be less than 10MB");
      return;
    }

    // Check if it's a CV/resume file
    const isCVFile = file.type === 'application/pdf' || 
                     file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                     file.type === 'application/msword' ||
                     file.name.toLowerCase().includes('cv') ||
                     file.name.toLowerCase().includes('resume');

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    
    if (isCVFile) {
      formData.append("name", file.name);
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
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      
      const result = await response.json();
      
      if (isCVFile && result.extracted_info) {
        // Handle CV upload with extraction results
        let message = `📄 **CV/Resume uploaded successfully!**\n\n`;
        message += `**File:** ${result.document.name}\n`;
        
        if (result.profile_updated && result.auto_extracted_fields.length > 0) {
          message += `**Profile Updated:** ✅ Automatically updated ${result.auto_extracted_fields.join(', ')}\n`;
        }
        
        if (result.extracted_info.confidence_score) {
          message += `**Extraction Confidence:** ${(result.extracted_info.confidence_score * 100).toFixed(0)}%\n`;
        }
        
        message += `\nYour CV has been processed and is now available for job applications and analysis. I can help you with job applications, interview preparation, or answer questions about your background.`;
        
        onSendMessage(message);
        
        // Show success toast
        toast.success("CV uploaded successfully!", {
          description: result.profile_updated 
            ? `Profile auto-updated with ${result.auto_extracted_fields.length} fields`
            : "CV processed and ready for use"
        });
      } else {
        // Handle regular file upload
        onSendMessage(`📎 Attached file: ${result.filename || file.name}`);
        toast.success("File uploaded successfully!");
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error("File upload failed", { description: errorMessage });
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
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

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className={cn(
        "relative flex items-end gap-2 sm:gap-3 transition-all duration-200",
        // Match the sophisticated theme styling from chat messages
        "p-2 sm:p-3 rounded-xl sm:rounded-2xl",
        "bg-card/80 backdrop-blur-sm border border-border/50 shadow-lg",
        "focus-within:ring-2 focus-within:ring-ring/30 focus-within:border-ring/50 focus-within:shadow-xl",
        "hover:bg-card/90 hover:border-border/70 hover:shadow-xl",
        // Add subtle gradient overlay like chat messages
        "relative overflow-hidden"
      )}>
        
        {/* Subtle gradient overlay to match theme */}
        <div className="absolute inset-0 bg-gradient-to-br from-background/5 to-transparent rounded-xl sm:rounded-2xl pointer-events-none" />
        
        {isRecording ? (
          // Recording mode with enhanced styling
          <div className="flex items-center justify-between w-full relative z-10">
            <button 
              type="button" 
              onClick={cancelRecording} 
              className={cn(
                "flex items-center justify-center p-2 sm:p-2.5",
                "text-destructive hover:text-destructive/80",
                "hover:bg-destructive/10 rounded-xl transition-all duration-200",
                "hover:scale-105 active:scale-95 touch-manipulation"
              )}
            >
              <Mic className="h-4 w-4 sm:h-5 sm:w-5 animate-pulse" />
            </button>
            
            <div className="text-xs sm:text-sm font-mono text-muted-foreground">
              {formatTime(recordingTime)}
            </div>
            
            <button 
              type="button" 
              onClick={stopRecording} 
              className={cn(
                "flex items-center justify-center p-2 sm:p-2.5",
                "bg-gradient-to-br from-blue-500 to-purple-600 text-primary-foreground",
                "hover:from-blue-600 hover:to-purple-700 rounded-xl sm:rounded-2xl",
                "transition-all duration-200 hover:scale-105 active:scale-95 touch-manipulation",
                "shadow-lg hover:shadow-xl"
              )}
            >
              <Send className="h-4 w-4 sm:h-5 sm:w-5" />
            </button>
          </div>
        ) : (
          // Normal input mode with enhanced styling
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
                "hover:scale-105 active:scale-95 touch-manipulation",
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
              accept=".pdf,.doc,.docx,.txt,.rtf,.xls,.xlsx,.csv,image/*" 
            />
            
            {/* Text input area with enhanced styling */}
            <div className="flex-1 min-w-0 relative z-10">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={handleMessageChange}
                onKeyDown={handleKeyDown}
                placeholder={placeholder || "Type a message... (Enter to send, Shift+Enter for new line)"}
                className={cn(
                  "w-full bg-transparent border-none focus:outline-none resize-none",
                  "text-sm sm:text-base text-foreground",
                  "placeholder:text-muted-foreground/60",
                  "min-h-[20px] max-h-[120px] overflow-y-auto",
                  // Better text rendering
                  "leading-relaxed tracking-wide"
                )}
                rows={1}
                style={{ height: 'auto' }}
              />
            </div>
            
            {/* Send/Mic button with enhanced styling */}
            {message.trim() ? (
              <button
                type="submit"
                disabled={isLoading}
                className={cn(
                  "flex items-center justify-center p-2 sm:p-2.5 relative z-10",
                  "bg-gradient-to-br from-blue-500 to-purple-600 text-primary-foreground",
                  "hover:from-blue-600 hover:to-purple-700 rounded-xl sm:rounded-2xl",
                  "transition-all duration-200 hover:scale-105 active:scale-95 touch-manipulation",
                  "shadow-lg hover:shadow-xl border border-white/20",
                  "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100",
                  isLoading && "animate-pulse"
                )}
              >
                <Send className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>
            ) : (
              <button 
                type="button" 
                onClick={startRecording} 
                className={cn(
                  "flex items-center justify-center p-2 sm:p-2.5 relative z-10",
                  "text-muted-foreground hover:text-foreground",
                  "hover:bg-accent/50 rounded-xl transition-all duration-200",
                  "hover:scale-105 active:scale-95 touch-manipulation"
                )}
              >
                <Mic className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>
            )}
          </>
        )}
      </div>
      
      {/* Helper text for mobile with theme colors */}
      <div className="mt-2 text-xs text-muted-foreground/70 text-center sm:hidden">
        Press Enter to send • Shift+Enter for new line
      </div>
    </form>
  );
} 