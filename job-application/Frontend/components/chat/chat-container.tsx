"use client";

import React, { useRef, useEffect, useState } from 'react';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { cn } from "@/lib/utils";
import { AlertCircle, Loader2, ChevronDown } from "lucide-react";
import { EmptyScreen } from '../empty-screen';
import { LoadingMessage } from './loading-message';

interface Message {
  id: string;
  content: string | object;
  isUser: boolean;
}

interface ChatContainerProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onDeleteMessage?: (id: string) => void;
  onEditMessage: (id: string, newContent: string) => void;
  onRegenerateMessage: (id: string) => void;
  user?: any;
  onStopGeneration?: () => void;
  isLoading: boolean;
  isHistoryLoading: boolean;
  isConnected: boolean;
  error?: string;
  className?: string;
}

export const ChatContainer = ({ 
  messages, 
  onSendMessage, 
  onDeleteMessage,
  onEditMessage,
  onRegenerateMessage,
  user,
  onStopGeneration,
  isLoading, 
  isHistoryLoading,
  isConnected, 
  error, 
  className 
}: ChatContainerProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Check if user is at the bottom
  const checkIfAtBottom = () => {
    if (!scrollContainerRef.current) return true;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const threshold = 100; // pixels from bottom
    return scrollHeight - scrollTop - clientHeight < threshold;
  };

  // Handle scroll events
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current;
    if (!scrollContainer) return;

    const handleScroll = () => {
      const isAtBottom = checkIfAtBottom();
      setShowScrollToBottom(!isAtBottom && messages.length > 0);
    };

    scrollContainer.addEventListener('scroll', handleScroll, { passive: true });
    
    // Initial check
    handleScroll();

    return () => {
      scrollContainer.removeEventListener('scroll', handleScroll);
    };
  }, [messages]);

  useEffect(() => {
    if (!isHistoryLoading) {
      scrollToBottom();
      // Hide the scroll button when auto-scrolling
      setShowScrollToBottom(false);
    }
  }, [messages, isHistoryLoading]);

  const handleSelectJob = (job: any) => {
    onSendMessage(`I'm interested in the ${job.title} position at ${job.company}.`);
  };

  return (
    <div className={cn(
      "flex flex-col h-full bg-background relative overflow-hidden",
      className
    )}>
      <div 
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden pb-24 sm:pb-32 md:pb-36"
        style={{
          // Enhanced mobile scrolling
          WebkitOverflowScrolling: 'touch',
          overscrollBehavior: 'contain',
          scrollBehavior: 'smooth',
          // Prevent horizontal scroll on mobile
          touchAction: 'pan-y',
          // Better momentum scrolling on iOS
          scrollSnapType: 'none',
        }}
      >
        {isHistoryLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : messages.length > 0 ? (
          <div className="max-w-2xl mx-auto px-1 sm:px-2 md:px-4 lg:px-6 w-full">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                id={message.id}
                content={message.content}
                isUser={message.isUser}
                user={message.isUser ? user : null}
                onDelete={onDeleteMessage || (() => {})}
                onEdit={onEditMessage}
                onRegenerate={onRegenerateMessage}
              />
            ))}
            {isLoading && <LoadingMessage />}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full px-2 sm:px-4">
            <EmptyScreen onSendMessage={onSendMessage} />
          </div>
        )}
      </div>

      {/* Scroll to Bottom Button */}
      {showScrollToBottom && (
        <div className="fixed bottom-20 sm:bottom-24 md:bottom-28 right-4 sm:right-6 z-10">
          <button
            onClick={scrollToBottom}
            className={cn(
              "flex items-center justify-center w-12 h-12 rounded-full shadow-lg transition-all duration-200",
              "bg-blue-600 hover:bg-blue-700 text-white",
              "hover:scale-110 active:scale-95",
              "border border-white/20 backdrop-blur-sm"
            )}
            title="Scroll to latest message"
          >
            <ChevronDown className="w-5 h-5" />
          </button>
        </div>
      )}
      
      <div 
        className="fixed bottom-0 left-0 right-0 bg-transparent p-2 sm:p-3 md:p-4" 
        style={{ 
          paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))',
          // Prevent input from being affected by scrolling
          touchAction: 'none'
        }}
      >
        <div className="max-w-2xl mx-auto">
          {error && (
            <div className="mb-2 sm:mb-3">
              <div className="flex items-center gap-1.5 rounded-xl bg-destructive/10 p-3 text-xs sm:text-sm text-destructive border border-destructive/20 shadow-lg backdrop-blur-sm">
                <AlertCircle className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" />
                <p className="leading-relaxed">{error}</p>
              </div>
            </div>
          )}
          <ChatInput
            onSendMessage={onSendMessage}
            onStopGeneration={onStopGeneration}
            isConnected={isConnected}
            isLoading={isLoading || false}
            placeholder="Send a message..."
          />
        </div>
      </div>
    </div>
  );
}; 