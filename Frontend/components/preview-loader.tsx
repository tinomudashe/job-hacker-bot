"use client";

import * as React from "react";
import { FileText, Database, Palette, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface LoadingStep {
  id: string;
  title: string;
  description: string;
  status: "pending" | "loading" | "completed" | "error";
  icon?: React.ReactNode;
}

interface PreviewLoaderProps {
  contentType: "resume" | "cover_letter" | null;
  className?: string;
}

export function PreviewLoader({ contentType, className }: PreviewLoaderProps) {
  const [steps, setSteps] = React.useState<LoadingStep[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = React.useState(0);

  React.useEffect(() => {
    // Define steps based on content type
    const loadingSteps: LoadingStep[] = contentType === "resume" ? [
      {
        id: "auth",
        title: "Authenticating",
        description: "Verifying your credentials",
        status: "pending",
        icon: <CheckCircle className="h-4 w-4" />
      },
      {
        id: "fetch",
        title: "Fetching Resume Data",
        description: "Loading your personal information",
        status: "pending",
        icon: <Database className="h-4 w-4" />
      },
      {
        id: "process",
        title: "Processing Content",
        description: "Organizing experience and skills",
        status: "pending",
        icon: <FileText className="h-4 w-4" />
      },
      {
        id: "render",
        title: "Applying Template",
        description: "Rendering your chosen style",
        status: "pending",
        icon: <Palette className="h-4 w-4" />
      }
    ] : contentType === "cover_letter" ? [
      {
        id: "auth",
        title: "Authenticating",
        description: "Verifying your credentials",
        status: "pending",
        icon: <CheckCircle className="h-4 w-4" />
      },
      {
        id: "fetch",
        title: "Loading Cover Letter",
        description: "Retrieving your document",
        status: "pending",
        icon: <Database className="h-4 w-4" />
      },
      {
        id: "parse",
        title: "Parsing Content",
        description: "Extracting company and job details",
        status: "pending",
        icon: <FileText className="h-4 w-4" />
      },
      {
        id: "format",
        title: "Formatting Document",
        description: "Applying professional layout",
        status: "pending",
        icon: <Palette className="h-4 w-4" />
      }
    ] : [
      {
        id: "init",
        title: "Initializing",
        description: "Preparing preview environment",
        status: "loading",
        icon: <Loader2 className="h-4 w-4 animate-spin" />
      }
    ];

    setSteps(loadingSteps);
  }, [contentType]);

  // Simulate progress through steps
  React.useEffect(() => {
    if (steps.length === 0) return;

    const timer = setInterval(() => {
      setSteps(prevSteps => {
        const newSteps = [...prevSteps];
        const currentIndex = newSteps.findIndex(s => s.status === "loading");
        
        if (currentIndex === -1) {
          // Start with first step
          if (newSteps[0]) {
            newSteps[0].status = "loading";
          }
        } else if (currentIndex < newSteps.length - 1) {
          // Complete current step and move to next
          newSteps[currentIndex].status = "completed";
          newSteps[currentIndex + 1].status = "loading";
          setCurrentStepIndex(currentIndex + 1);
        } else {
          // Complete last step
          newSteps[currentIndex].status = "completed";
          clearInterval(timer);
        }
        
        return newSteps;
      });
    }, 800);

    return () => clearInterval(timer);
  }, [steps.length]);

  return (
    <div className={cn("flex flex-col items-center justify-center min-h-[400px] p-8", className)}>
      <div className="max-w-md w-full space-y-8">
        {/* Main loader animation */}
        <div className="flex justify-center mb-8">
          <div className="relative">
            <div className="h-16 w-16 rounded-full border-4 border-primary/20 animate-pulse" />
            <div className="absolute inset-0 h-16 w-16 rounded-full border-4 border-t-primary animate-spin" />
            <FileText className="absolute inset-0 m-auto h-8 w-8 text-primary" />
          </div>
        </div>

        {/* Loading steps */}
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg transition-all duration-300",
                step.status === "loading" && "bg-primary/5 border border-primary/20",
                step.status === "completed" && "opacity-60",
                step.status === "pending" && "opacity-30"
              )}
            >
              {/* Step icon */}
              <div className={cn(
                "mt-0.5 flex-shrink-0",
                step.status === "loading" && "text-primary",
                step.status === "completed" && "text-green-600",
                step.status === "pending" && "text-muted-foreground"
              )}>
                {step.status === "loading" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : step.status === "completed" ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  step.icon || <div className="h-4 w-4 rounded-full border-2 border-current" />
                )}
              </div>

              {/* Step content */}
              <div className="flex-1 min-w-0">
                <h4 className={cn(
                  "text-sm font-medium transition-colors",
                  step.status === "loading" && "text-foreground",
                  step.status === "completed" && "text-muted-foreground line-through",
                  step.status === "pending" && "text-muted-foreground"
                )}>
                  {step.title}
                </h4>
                <p className={cn(
                  "text-xs mt-0.5 transition-colors",
                  step.status === "loading" && "text-muted-foreground",
                  step.status === "completed" && "text-muted-foreground/60",
                  step.status === "pending" && "text-muted-foreground/40"
                )}>
                  {step.description}
                </p>
              </div>

              {/* Status indicator */}
              {step.status === "loading" && (
                <div className="flex gap-1 items-center mt-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Progress text */}
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            {currentStepIndex < steps.length - 1 
              ? `Processing step ${currentStepIndex + 1} of ${steps.length}...`
              : "Almost ready..."}
          </p>
        </div>
      </div>
    </div>
  );
}