"use client";

import { cn } from "@/lib/utils";
import { AlertCircle, ChevronDown, Loader2 } from "lucide-react";
import { useEffect, useRef } from "react";
import { EmptyScreen } from "../empty-screen";
import { ChatMessage } from "./chat-message";
import { ChatTextarea } from "./chat-textarea";
import { LoadingMessage } from "./loading-message";

interface ReasoningStep {
  type: 'reasoning_start' | 'reasoning_chunk' | 'reasoning_complete';
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

// Helper function to detect what the AI is doing based on the conversation
function getProgressType(
  messages: any[]
):
  | "thinking"
  | "searching"
  | "generating"
  | "processing"
  | "downloading"
  | "browser_automation"
  | "job_search"
  | "linkedin_api" {
  if (messages.length === 0) return "thinking";

  const lastUserMessage =
    [...messages]
      .reverse()
      .find((m) => m.isUser)
      ?.content?.toLowerCase() || "";
  const lastFewMessages = [...messages]
    .slice(-3)
    .map((m) =>
      typeof m.content === "string" ? m.content : JSON.stringify(m.content)
    )
    .join(" ")
    .toLowerCase();

  // LinkedIn API indicators - check for fast job search patterns (highest priority)
  if (
    lastUserMessage.includes("linkedin") ||
    lastUserMessage.includes("software intern") ||
    lastUserMessage.includes("intern") ||
    lastFewMessages.includes("linkedin api") ||
    lastFewMessages.includes("direct linkedin") ||
    (lastUserMessage.includes("job") &&
      (lastUserMessage.includes("search") ||
        lastUserMessage.includes("find") ||
        lastUserMessage.includes("software")))
  ) {
    return "linkedin_api";
  }

  // Browser automation indicators - check for comprehensive job search patterns
  if (
    lastUserMessage.includes("comprehensive") ||
    lastUserMessage.includes("detailed job search") ||
    lastUserMessage.includes("browser automation") ||
    lastFewMessages.includes("browser use cloud") ||
    lastFewMessages.includes("cloud browser") ||
    lastFewMessages.includes("browser automation") ||
    lastFewMessages.includes("live preview")
  ) {
    return "browser_automation";
  }

  // Regular job search indicators
  if (
    lastUserMessage.includes("job") ||
    lastUserMessage.includes("search") ||
    lastUserMessage.includes("find") ||
    lastUserMessage.includes("employment") ||
    lastUserMessage.includes("opportunities") ||
    lastUserMessage.includes("career") ||
    lastUserMessage.includes("position") ||
    lastUserMessage.includes("work")
  ) {
    return "job_search";
  }

  // Content generation indicators
  if (
    lastUserMessage.includes("generate") ||
    lastUserMessage.includes("create") ||
    lastUserMessage.includes("write") ||
    lastUserMessage.includes("cover letter") ||
    lastUserMessage.includes("resume") ||
    lastUserMessage.includes("cv") ||
    lastUserMessage.includes("refine") ||
    lastUserMessage.includes("enhance") ||
    lastUserMessage.includes("improve") ||
    lastUserMessage.includes("tailor")
  ) {
    return "generating";
  }

  // Document processing indicators
  if (
    lastUserMessage.includes("analyze") ||
    lastUserMessage.includes("document") ||
    lastUserMessage.includes("file") ||
    lastUserMessage.includes("upload") ||
    lastUserMessage.includes("extract") ||
    lastUserMessage.includes("review")
  ) {
    return "processing";
  }

  // Download indicators
  if (
    lastUserMessage.includes("download") ||
    lastUserMessage.includes("pdf") ||
    lastUserMessage.includes("export") ||
    lastUserMessage.includes("save")
  ) {
    return "downloading";
  }

  return "thinking";
}

function getCustomProgressMessage(messages: any[]): string | undefined {
  return undefined;
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
  className,
}: ChatContainerProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

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

  const handleSelectJob = (job: any) => {
    onSendMessage(
      `I'm interested in the ${job.title} position at ${job.company}.`
    );
  };

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-background relative overflow-hidden",
        className
      )}
    >
      <div
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
                reasoningSteps={message.reasoningSteps}
              />
            ))}
            {isLoading && (
              <LoadingMessage
                progressType={getProgressType(messages)}
                customMessage={getCustomProgressMessage(messages)}
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
        className="fixed bottom-0 left-0 right-0 bg-transparent p-2 sm:p-3 md:p-4"
        style={{
          paddingBottom: "max(0.5rem, env(safe-area-inset-bottom))",
          // Prevent input from being affected by scrolling
          touchAction: "none",
        }}
      >
        <div className="max-w-2xl mx-auto">
          {/* Scroll to Bottom Button - Above text input */}
          {messages.length > 0 && (
            <div className="mb-2 flex justify-center">
              <button
                onClick={scrollToBottom}
                className={cn(
                  "flex items-center justify-center rounded-xl transition-all duration-200",
                  "w-8 h-8 sm:w-10 sm:h-10", // Smaller on mobile, larger on desktop
                  "bg-background/60 backdrop-blur-xl backdrop-saturate-150",
                  "border border-white/8 hover:border-white/12",
                  "shadow-2xl",
                  "text-muted-foreground hover:text-foreground",
                  "hover:scale-105 active:scale-95"
                )}
                title="Scroll to latest message - Ctrl+End"
                aria-label="Scroll to bottom"
              >
                <ChevronDown className="w-3 h-3" />
              </button>
            </div>
          )}

          {error && (
            <div className="mb-2 sm:mb-3">
              <div className="flex items-center gap-1.5 rounded-xl bg-destructive/10 p-3 text-xs sm:text-sm text-destructive border border-destructive/20 shadow-lg backdrop-blur-sm">
                <AlertCircle className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" />
                <p className="leading-relaxed">{error}</p>
              </div>
            </div>
          )}
          <ChatTextarea
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
