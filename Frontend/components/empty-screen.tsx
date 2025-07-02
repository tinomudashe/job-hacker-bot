"use client";

import { Button } from "@/components/ui/button";
import { Brain, Building, FileText, Sparkles } from "lucide-react";

const exampleMessages = [
  {
    heading: "Generate cover letter from URL",
    message: "Paste any job link for a tailored cover letter",
    fullMessage:
      "Generate a cover letter from this job URL: [paste LinkedIn, Indeed, or company career page URL here]",
    icon: FileText,
    color: "emerald",
  },
  {
    heading: "Find jobs on specific platforms",
    message: "Search LinkedIn, Indeed, Glassdoor easily",
    fullMessage: "Find product manager jobs on Indeed in New York",
    icon: Building,
    color: "violet",
  },
  {
    heading: "Create professional resume PDF",
    message: "Download with beautiful formatting",
    fullMessage: "Download my resume as PDF with professional styling",
    icon: Brain,
    color: "amber",
  },
];

interface EmptyScreenProps {
  onSendMessage: (message: string) => void;
}

export function EmptyScreen({ onSendMessage }: EmptyScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12">
      {/* Hero Section */}
      <div className="mb-12 text-center max-w-2xl">
        <div className="inline-flex items-center justify-center w-16 h-16 mb-6 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-2xl">
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground via-foreground/90 to-foreground/70 bg-clip-text text-transparent mb-4">
          Hello there!
        </h1>
        <p className="text-lg text-muted-foreground/80 leading-relaxed">
          I'm your AI-powered job search assistant. Ready to help you find
          opportunities, craft perfect applications, and land your dream job!
        </p>
      </div>

      {/* Suggestion Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-5xl w-full">
        {exampleMessages.map((item, index) => {
          const IconComponent = item.icon;
          const colorClasses = {
            emerald: "bg-emerald-500 hover:bg-emerald-600",
            violet: "bg-violet-500 hover:bg-violet-600",
            amber: "bg-amber-500 hover:bg-amber-600",
          }[item.color];

          return (
            <Button
              key={index}
              variant="ghost"
              className="group relative h-[160px] p-6 text-left flex flex-col items-start justify-start rounded-2xl bg-background/70 backdrop-blur-xl border border-border/40 hover:border-border/70 hover:bg-background/85 transition-all duration-300 hover:scale-[1.01] hover:shadow-lg shadow-sm"
              onClick={() => onSendMessage(item.fullMessage)}
            >
              {/* Icon */}
              <div
                className={`flex items-center justify-center w-12 h-12 rounded-xl ${colorClasses} shadow-md mb-4 transition-all duration-300 group-hover:scale-105 flex-shrink-0`}
              >
                <IconComponent className="w-6 h-6 text-white" />
              </div>

              {/* Content */}
              <div className="flex-1 space-y-2 overflow-hidden">
                <h3 className="text-lg font-semibold text-foreground leading-tight">
                  {item.heading}
                </h3>
                <p className="text-sm text-muted-foreground/90 leading-relaxed">
                  {item.message}
                </p>
              </div>

              {/* Subtle hover indicator */}
              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="w-6 h-6 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center">
                  <svg
                    className="w-3 h-3 text-foreground/60"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </div>
            </Button>
          );
        })}
      </div>

      {/* Footer hint */}
      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground/60">
          Or type your own message below to get started
        </p>
      </div>
    </div>
  );
}
