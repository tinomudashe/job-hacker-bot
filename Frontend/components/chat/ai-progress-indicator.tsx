"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  Brain,
  Briefcase,
  Download,
  FileText,
  Globe,
  Search,
  Sparkles,
  X,
  Zap,
} from "lucide-react";

export interface AIProgressIndicatorProps {
  isLoading: boolean;
  progressText?: string;
  progressType?:
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
  className?: string;
  onCancel?: () => void;
}

// REMOVED: The large, hardcoded `progressMessages` array is now gone.

const iconComponents = {
  thinking: Brain,
  searching: Search,
  generating: FileText,
  processing: Zap,
  downloading: Download,
  browser_automation: Globe,
  job_search: Briefcase,
  linkedin_api: Briefcase,
  "calling tool": Zap,
  reasoning: Brain,
  "calling api": Globe,
  conversation: Brain,
  tool_execution: Zap,
  data_persistence: FileText,
  response_formatting: Sparkles,
};

// More descriptive messages based on LangGraph nodes and tools
const nodeMessages: Record<string, string[]> = {
  conversation: [
    "Understanding your request...",
    "Analyzing context...",
    "Processing your query..."
  ],
  tool_execution: [
    "Executing operations...",
    "Running tools...",
    "Processing data..."
  ],
  data_persistence: [
    "Saving your progress...",
    "Updating database...",
    "Storing information..."
  ],
  response_formatting: [
    "Formatting response...",
    "Preparing results...",
    "Finalizing output..."
  ],
  thinking: [
    "Analyzing your request...",
    "Considering options...",
    "Planning approach..."
  ],
  searching: [
    "Searching for information...",
    "Scanning resources...",
    "Finding relevant data..."
  ],
  generating: [
    "Creating content...",
    "Building your document...",
    "Generating results..."
  ],
  processing: [
    "Processing your request...",
    "Working on it...",
    "Computing results..."
  ],
  downloading: [
    "Preparing download...",
    "Generating file...",
    "Creating document..."
  ],
  job_search: [
    "Searching job opportunities...",
    "Analyzing job market...",
    "Finding matches..."
  ],
  browser_automation: [
    "Automating browser tasks...",
    "Navigating pages...",
    "Extracting data..."
  ],
  linkedin_api: [
    "Connecting to LinkedIn...",
    "Fetching job data...",
    "Processing listings..."
  ],
  reasoning: [
    "Planning approach...",
    "Analyzing options...",
    "Determining best path..."
  ],
  "calling api": [
    "Fetching external data...",
    "Connecting to service...",
    "Retrieving information..."
  ],
  "calling tool": [
    "Executing tool...",
    "Processing request...",
    "Running operation..."
  ]
};

// Map tool names to user-friendly descriptions
const toolDescriptions: Record<string, string> = {
  refine_cv_for_role: "Tailoring your CV for the role...",
  refine_cv_from_url: "Analyzing job posting and customizing CV...",
  generate_tailored_resume: "Creating personalized resume...",
  create_resume_from_scratch: "Building new resume from your data...",
  generate_cover_letter: "Writing cover letter...",
  analyze_job_fit: "Analyzing job compatibility...",
  search_jobs: "Searching job opportunities...",
  get_job_details: "Fetching job details...",
  update_resume: "Updating your resume...",
  add_experience: "Adding work experience...",
  add_education: "Adding education details...",
  add_skills: "Updating skills section...",
  download_resume: "Preparing resume download...",
  save_resume: "Saving resume data..."
};

export function AIProgressIndicator({
  isLoading,
  progressText,
  progressType = "thinking",
  className,
  onCancel,
}: AIProgressIndicatorProps) {
  const [fallbackMessageIndex, setFallbackMessageIndex] = React.useState(0);
  
  // Only cycle through fallback messages if no backend message is provided
  React.useEffect(() => {
    if (!isLoading || progressText) return;
    
    const messages = nodeMessages[progressType] || nodeMessages.thinking;
    const interval = setInterval(() => {
      setFallbackMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2000);
    
    return () => clearInterval(interval);
  }, [isLoading, progressType, progressText]);

  const IconComponent = iconComponents[progressType] || iconComponents.thinking;

  if (!isLoading) return null;

  // Prioritize backend-provided progress text
  let currentMessage = progressText;
  
  // Only use fallback messages if no backend message is provided
  if (!progressText) {
    // Check if progressText matches a tool name
    if (progressText && toolDescriptions[progressText]) {
      currentMessage = toolDescriptions[progressText];
    } else {
      // Use fallback cycling messages for generic states
      const messages = nodeMessages[progressType] || nodeMessages.thinking;
      currentMessage = messages[fallbackMessageIndex];
    }
  }

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

// This component now works correctly with the simplified indicator above.
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
    | "calling tool"
    | "reasoning"
    | "calling api";
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
