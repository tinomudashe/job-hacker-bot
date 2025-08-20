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
  | "linkedin_api"
  | "conversation"
  | "tool_execution"
  | "data_persistence"
  | "response_formatting";

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

  // Extract meaningful information from the last step
  let displayText = customMessage;
  let displayType: ProgressType = progressType;
  
  if (lastStep) {
    // Check for specific node names from LangGraph
    if (lastStep.step?.includes("conversation")) {
      displayType = "conversation" as ProgressType;
      displayText = lastStep.content || "Understanding your request...";
    } else if (lastStep.step?.includes("tool_execution")) {
      displayType = "tool_execution" as ProgressType;
      displayText = lastStep.tool_name || lastStep.content || "Executing tools...";
    } else if (lastStep.step?.includes("data_persistence")) {
      displayType = "data_persistence" as ProgressType;
      displayText = lastStep.content || "Saving data...";
    } else if (lastStep.step?.includes("response_formatting")) {
      displayType = "response_formatting" as ProgressType;
      displayText = lastStep.content || "Formatting response...";
    } else if (lastStep.tool_name) {
      // If we have a tool name, show it
      displayType = "calling tool";
      displayText = lastStep.tool_name;
    } else if (lastStep.content) {
      // Use the content if available
      displayText = lastStep.content;
      // Try to infer type from content
      if (lastStep.content.toLowerCase().includes("search")) {
        displayType = "searching";
      } else if (lastStep.content.toLowerCase().includes("generat")) {
        displayType = "generating";
      } else if (lastStep.content.toLowerCase().includes("download")) {
        displayType = "downloading";
      }
    }
  }

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
