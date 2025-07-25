"use client";

import { Logo } from "../ui/logo";
import { AIProgressIndicator } from "./ai-progress-indicator";

type ProgressType =
  | "thinking"
  | "searching"
  | "generating"
  | "processing"
  | "downloading"
  | "calling tool"
  | "reasoning"
  | "calling api"
  | "browser_automation"
  | "job_search"
  | "linkedin_api";

interface ReasoningStep {
  type: "reasoning_start" | "reasoning_chunk" | "reasoning_complete";
  content: string;
  step?: string;
  specialist?: string;
  tool_name?: string;
  progress?: string;
  timestamp: string;
}

interface LoadingMessageProps {
  reasoningSteps?: ReasoningStep[];
  progressType?: ProgressType;
  customMessage?: string;
  onCancel?: () => void;
}

export function LoadingMessage({
  reasoningSteps,
  progressType = "thinking",
  customMessage,
  onCancel,
}: LoadingMessageProps) {
  // Find the last, most recent reasoning step to display.
  const lastStep =
    reasoningSteps && reasoningSteps.length > 0
      ? reasoningSteps[reasoningSteps.length - 1]
      : null;

  // Use the live content from the stream if it exists.
  const displayText = lastStep ? lastStep.content : customMessage;
  const displayType: ProgressType = lastStep
    ? (lastStep.step as ProgressType) || "thinking"
    : progressType;

  return (
    <div className="flex items-start gap-3 py-2">
      {/* Premium AI Avatar with Logo */}
      <div className="shrink-0 select-none mt-0.5">
        <Logo size="sm" className="w-7 h-7" />
      </div>

      {/* Progress Content */}
      <div className="flex-1 min-w-0 mt-1">
        <AIProgressIndicator
          isLoading={true}
          progressType={displayType}
          progressText={displayText}
          onCancel={onCancel}
        />
      </div>
    </div>
  );
}

// Minimalist version for backwards compatibility
export function SimpleLoadingMessage() {
  return (
    <div className="flex items-center gap-2 py-1">
      <div className="flex items-center justify-center gap-1">
        <span className="h-1 w-1 rounded-full bg-muted-foreground/60 animate-pulse [animation-delay:-0.3s]" />
        <span className="h-1 w-1 rounded-full bg-muted-foreground/60 animate-pulse [animation-delay:-0.15s]" />
        <span className="h-1 w-1 rounded-full bg-muted-foreground/60 animate-pulse" />
      </div>
    </div>
  );
}
