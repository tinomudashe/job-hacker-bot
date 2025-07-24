"use client";

import { cn } from "@/lib/utils";
import { 
  Brain, 
  ChevronDown, 
  ChevronRight, 
  Zap, 
  CheckCircle, 
  AlertCircle,
  Wrench,
  Target 
} from "lucide-react";
import { useState } from "react";

interface ReasoningStep {
  type: 'reasoning_start' | 'reasoning_chunk' | 'reasoning_complete';
  content: string;
  step?: string;
  specialist?: string;
  tool_name?: string;
  progress?: string;
  timestamp: string;
}

interface ReasoningStreamProps {
  steps: ReasoningStep[];
  isComplete?: boolean;
  className?: string;
}

const stepIcons = {
  analysis: Brain,
  tool_planning: Wrench,
  tool_execution_start: Zap,
  tool_progress: Wrench,
  tool_success: CheckCircle,
  tool_error: AlertCircle,
  tool_not_found: AlertCircle,
  tool_execution_complete: Target,
  default: Brain
};

const stepColors = {
  analysis: "text-blue-500",
  tool_planning: "text-purple-500", 
  tool_execution_start: "text-orange-500",
  tool_progress: "text-yellow-500",
  tool_success: "text-green-500",
  tool_error: "text-red-500",
  tool_not_found: "text-red-400",
  tool_execution_complete: "text-emerald-500",
  default: "text-muted-foreground"
};

export function ReasoningStream({ steps, isComplete = false, className }: ReasoningStreamProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!steps || steps.length === 0) return null;

  const latestStep = steps[steps.length - 1];

  return (
    <div className={cn("mb-3", className)}>
      {/* Collapsible Header - matches your app's glass morphism style */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full flex items-center gap-2 p-3 rounded-xl border transition-all duration-200",
          "bg-white/80 border-slate-200/60 shadow-sm hover:bg-white/90 hover:border-slate-300/70",
          "dark:bg-black/60 dark:border-gray-600/40 dark:hover:bg-black/70 dark:hover:border-gray-500/50",
          "backdrop-blur-sm"
        )}
      >
        {/* Brain Icon - matches your AI theming */}
        <div className="shrink-0">
          <Brain className="w-4 h-4 text-blue-500" />
        </div>
        
        {/* Current Status */}
        <div className="flex-1 text-left">
          <div className="text-sm font-medium text-foreground/90">
            {isComplete ? "✨ Reasoning Complete" : "🧠 AI Thinking..."}
          </div>
          <div className="text-xs text-muted-foreground/70">
            {latestStep.content}
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="shrink-0 flex items-center gap-2">
          {!isComplete && (
            <div className="flex gap-0.5">
              <div className="w-1 h-1 bg-blue-500/60 rounded-full animate-pulse" />
              <div className="w-1 h-1 bg-blue-500/60 rounded-full animate-pulse [animation-delay:0.2s]" />
              <div className="w-1 h-1 bg-blue-500/60 rounded-full animate-pulse [animation-delay:0.4s]" />
            </div>
          )}
          
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-muted-foreground/60" />
          ) : (
            <ChevronRight className="w-4 h-4 text-muted-foreground/60" />
          )}
        </div>
      </button>

      {/* Expanded Reasoning Steps */}
      {isExpanded && (
        <div className={cn(
          "mt-2 p-3 rounded-xl border",
          "bg-white/60 border-slate-200/50 shadow-sm",
          "dark:bg-black/40 dark:border-gray-600/30",
          "backdrop-blur-sm"
        )}>
          <div className="space-y-2">
            {steps.map((step, index) => {
              const StepIcon = stepIcons[step.step as keyof typeof stepIcons] || stepIcons.default;
              const stepColor = stepColors[step.step as keyof typeof stepColors] || stepColors.default;
              
              return (
                <div key={index} className="flex items-start gap-2 py-1">
                  {/* Step Icon */}
                  <div className="shrink-0 mt-0.5">
                    <StepIcon className={cn("w-3.5 h-3.5", stepColor)} />
                  </div>
                  
                  {/* Step Content */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-foreground/80">
                      {step.content}
                    </div>
                    
                    {/* Additional Info */}
                    {(step.tool_name || step.progress) && (
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground/60">
                        {step.tool_name && (
                          <span className="px-2 py-0.5 bg-muted/50 rounded-md">
                            {step.tool_name}
                          </span>
                        )}
                        {step.progress && (
                          <span className="text-muted-foreground/70">
                            {step.progress}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {/* Timestamp */}
                  <div className="shrink-0 text-xs text-muted-foreground/50">
                    {new Date(step.timestamp).toLocaleTimeString([], { 
                      timeStyle: 'short' 
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}