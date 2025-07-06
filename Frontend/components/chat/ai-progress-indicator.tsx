"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  Brain,
  Briefcase,
  Download,
  FileText,
  Globe,
  Linkedin,
  Search,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

interface AIProgressIndicatorProps {
  isLoading: boolean;
  progressText?: string;
  progressType?:
    | "thinking"
    | "searching"
    | "generating"
    | "processing"
    | "downloading"
    | "browser_automation"
    | "job_search"
    | "linkedin_api";
  className?: string;
  onCancel?: () => void;
}

const progressMessages = [
  "Parsing...",
  "Searching...",
  "Please wait a bit longer...",
  "Almost ready...",
];

const iconComponents = {
  thinking: Brain,
  searching: Search,
  generating: FileText,
  processing: Zap,
  downloading: Download,
  browser_automation: Globe,
  job_search: Briefcase,
  linkedin_api: Linkedin,
};

export function AIProgressIndicator({
  isLoading,
  progressText,
  progressType = "thinking",
  className,
  onCancel,
}: AIProgressIndicatorProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

  const IconComponent = iconComponents[progressType] || iconComponents.thinking;

  // Message cycling
  useEffect(() => {
    if (!isLoading) {
      setCurrentMessageIndex(0);
      return;
    }

    const messageInterval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % progressMessages.length);
    }, 2000);

    return () => clearInterval(messageInterval);
  }, [isLoading]);

  if (!isLoading) return null;

  const currentMessage = progressText || progressMessages[currentMessageIndex];

  return (
    <div className={cn("flex items-center gap-2 py-1 px-1", className)}>
      {/* Elegant icon with subtle animation */}
      <div className="flex items-center justify-center">
        <IconComponent className="w-3.5 h-3.5 text-muted-foreground/70 animate-pulse" />
      </div>

      {/* Progress text with better typography */}
      <span className="text-sm sm:text-base text-muted-foreground/80 font-medium flex-1">
        {currentMessage}
      </span>

      {/* Elegant loading dots */}
      <div className="flex items-center gap-0.5 mr-1">
        <div
          className="w-1 h-1 bg-muted-foreground/40 rounded-full animate-pulse"
          style={{ animationDelay: "0ms", animationDuration: "1.5s" }}
        />
        <div
          className="w-1 h-1 bg-muted-foreground/40 rounded-full animate-pulse"
          style={{ animationDelay: "500ms", animationDuration: "1.5s" }}
        />
        <div
          className="w-1 h-1 bg-muted-foreground/40 rounded-full animate-pulse"
          style={{ animationDelay: "1000ms", animationDuration: "1.5s" }}
        />
      </div>

      {/* Refined stop button */}
      {onCancel && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          className="h-6 w-6 p-0 hover:bg-destructive/10 hover:text-destructive transition-colors rounded-sm opacity-60 hover:opacity-100"
        >
          <X className="w-3 h-3" />
        </Button>
      )}
    </div>
  );
}

// Polished Loading Message
export function EnhancedLoadingMessage({
  progressType = "thinking",
  customMessage,
  onCancel,
}: {
  progressType?:
    | "thinking"
    | "searching"
    | "generating"
    | "processing"
    | "downloading"
    | "browser_automation"
    | "job_search";
  customMessage?: string;
  onCancel?: () => void;
}) {
  return (
    <div className="flex items-start gap-3 py-2">
      {/* Refined AI Avatar */}
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-br from-primary/10 to-primary/5 flex items-center justify-center mt-0.5 border border-primary/10">
        <Sparkles className="w-3.5 h-3.5 text-primary/70" />
      </div>

      {/* Progress Content */}
      <div className="flex-1 min-w-0 mt-1">
        <AIProgressIndicator
          isLoading={true}
          progressType={progressType}
          progressText={customMessage}
          onCancel={onCancel}
        />
      </div>
    </div>
  );
}
