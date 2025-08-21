"use client";

import { cn } from "@/lib/utils";
import { UserResource } from "@clerk/types";
import { AlertCircle, ChevronDown, Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { EmptyScreen } from "../empty-screen";
import { ChatMessage } from "./chat-message";
import { ChatTextarea } from "./chat-textarea";
import { LoadingMessage } from "./loading-message";
import { ConversationLimitReached } from "./conversation-limit-reached";

interface ReasoningStep {
  type: "reasoning_start" | "reasoning_chunk" | "reasoning_complete";
  content: string;
  step?: string;
  specialist?: string;
  tool_name?: string;
  progress?: string;
  timestamp: string;
}

interface Message {
  id: string;
  content: string | object;
  isUser: boolean;
  reasoningSteps?: ReasoningStep[];
}

interface ChatContainerProps {
  messages: Message[];
  reasoningSteps?: ReasoningStep[];
  onSendMessage: (message: string) => void;
  onDeleteMessage?: (id: string) => void;
  onEditMessage: (id: string, newContent: string) => void;
  onRegenerateMessage: (id: string) => void;
  onStartNewChat?: () => void;
  user?: UserResource | null;
  onStopGeneration?: () => void;
  isLoading: boolean;
  isHistoryLoading: boolean;
  isConnected: boolean;
  isLimitReached?: boolean;
  error?: string;
  className?: string;
}

export const ChatContainer = ({
  messages,
  reasoningSteps,
  onSendMessage,
  onDeleteMessage,
  onEditMessage,
  onRegenerateMessage,
  onStartNewChat,
  user,
  onStopGeneration,
  isLoading,
  isHistoryLoading,
  isConnected,
  isLimitReached = false,
  error,
  className,
}: ChatContainerProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Check if user is near bottom of chat
  const checkIfNearBottom = () => {
    if (!scrollContainerRef.current) return true;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    
    // Show button if more than 100px from bottom
    return distanceFromBottom < 100;
  };

  // Handle scroll to show/hide button
  useEffect(() => {
    const handleScroll = () => {
      if (!scrollContainerRef.current) return;
      
      const isNearBottom = checkIfNearBottom();
      setShowScrollButton(!isNearBottom && messages.length > 0);
    };

    const scrollContainer = scrollContainerRef.current;
    if (scrollContainer) {
      scrollContainer.addEventListener("scroll", handleScroll);
      handleScroll(); // Check initial state
    }

    return () => {
      if (scrollContainer) {
        scrollContainer.removeEventListener("scroll", handleScroll);
      }
    };
  }, [messages.length]);

  // Keyboard shortcut for scroll to bottom (Ctrl/Cmd + End)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "End") {
        e.preventDefault();
        scrollToBottom();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (!isHistoryLoading) {
      scrollToBottom();
    }
  }, [messages, isHistoryLoading]);

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-background relative overflow-hidden",
        className
      )}
    >
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden pb-40 sm:pb-48 md:pb-52"
        style={{
          // Enhanced mobile scrolling
          WebkitOverflowScrolling: "touch",
          overscrollBehavior: "contain",
          scrollBehavior: "smooth",
          // Prevent horizontal scroll on mobile
          touchAction: "pan-y",
          // Better momentum scrolling on iOS
          scrollSnapType: "none",
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
                onSendMessage={onSendMessage}
              />
            ))}
            {isLoading && (
              <LoadingMessage
                reasoningSteps={reasoningSteps}
                onCancel={onStopGeneration}
              />
            )}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full px-2 sm:px-4">
            <EmptyScreen onSendMessage={onSendMessage} />
          </div>
        )}
      </div>

      <div
        className="fixed bottom-0 left-0 right-0 bg-transparent p-2 sm:p-3 md:p-4 z-20"
        style={{
          paddingBottom: "max(0.5rem, env(safe-area-inset-bottom))",
          // Prevent input from being affected by scrolling
          touchAction: "none",
        }}
      >
        <div className="max-w-2xl mx-auto">
          {/* Scroll to Bottom Button - Above text input - Only show when scrolled up */}
          {showScrollButton && (
            <div className="mb-2 flex justify-center">
              <button
                type="button"
                onClick={scrollToBottom}
                className={cn(
                  "flex items-center justify-center rounded-lg transition-all duration-300",
                  "w-7 h-7", // Smaller size
                  "bg-background/60 backdrop-blur-xl backdrop-saturate-150",
                  "border border-white/8 hover:border-white/12",
                  "shadow-2xl",
                  "text-muted-foreground hover:text-foreground",
                  "hover:scale-110 active:scale-95",
                  "animate-in fade-in duration-300"
                )}
                title="Scroll to latest message - Ctrl+End"
                aria-label="Scroll to bottom"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          )}

          {error && !isLimitReached && (
            <div className="mb-2 sm:mb-3">
              <div className="flex items-center gap-1.5 rounded-xl bg-destructive/10 p-3 text-xs sm:text-sm text-destructive border border-destructive/20 shadow-lg backdrop-blur-sm">
                <AlertCircle className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" />
                <p className="leading-relaxed">{error}</p>
              </div>
            </div>
          )}
          
          {isLimitReached && onStartNewChat ? (
            <ConversationLimitReached
              messageCount={messages.length}
              messageLimit={50}
              onStartNewChat={onStartNewChat}
            />
          ) : (
            <ChatTextarea
              onSendMessage={onSendMessage}
              onStopGeneration={onStopGeneration}
              isConnected={isConnected}
              isLoading={isLoading || false}
              placeholder={isLimitReached ? "Message limit reached. Start a new chat to continue." : "Send a message..."}
            />
          )}
        </div>
      </div>
    </div>
  );
};
