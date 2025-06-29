"use client"

import { Button } from "@/components/ui/button"
import { Sparkles, Briefcase, FileText, Brain, Building } from "lucide-react"

const exampleMessages = [
  {
    heading: "Search jobs with browser automation",
    message: "get detailed results from major job boards",
    fullMessage: "Search for data analyst jobs in Poland using browser automation on LinkedIn",
    icon: Briefcase,
    gradient: "from-blue-500 to-cyan-500"
  },
  {
    heading: "Generate cover letter from URL",
    message: "paste any job posting link",
    fullMessage: "Generate a cover letter from this job URL: [paste LinkedIn, Indeed, or company career page URL here]",
    icon: FileText,
    gradient: "from-green-500 to-emerald-500"
  },
  {
    heading: "Find jobs on specific platforms",
    message: "search LinkedIn, Indeed, Glassdoor directly",
    fullMessage: "Find product manager jobs on Indeed in New York with browser automation",
    icon: Building,
    gradient: "from-purple-500 to-pink-500"
  },
  {
    heading: "Create a resume PDF",
    message: "with professional styling",
    fullMessage: "Download my resume as PDF with professional styling",
    icon: Brain,
    gradient: "from-orange-500 to-red-500"
  },
]

interface EmptyScreenProps {
  onSendMessage: (message: string) => void
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
          Hello there! 👋
        </h1>
        <p className="text-lg text-muted-foreground/80 leading-relaxed">
          I'm your AI-powered job search assistant. Ready to help you find opportunities, 
          craft perfect applications, and land your dream job!
        </p>
      </div>

      {/* Suggestion Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl w-full">
        {exampleMessages.map((item, index) => {
          const IconComponent = item.icon;
          return (
            <Button
              key={index}
              variant="ghost"
              className="group relative h-auto p-6 text-left flex flex-col items-start rounded-2xl bg-background/50 backdrop-blur-sm border border-border/50 hover:border-border transition-all duration-300 hover:scale-[1.02] hover:shadow-xl overflow-hidden"
              onClick={() => onSendMessage(item.fullMessage)}
            >
              {/* Background gradient overlay */}
              <div className={`absolute inset-0 bg-gradient-to-br ${item.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
              
              {/* Icon */}
              <div className={`flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br ${item.gradient} shadow-lg mb-4 group-hover:scale-110 transition-transform duration-300`}>
                <IconComponent className="w-5 h-5 text-white" />
              </div>
              
              {/* Content */}
              <div className="relative z-10">
                <p className="text-base font-semibold text-foreground mb-1 group-hover:text-foreground/90 transition-colors">
                  {item.heading}
                </p>
                <p className="text-sm text-muted-foreground/70 group-hover:text-muted-foreground transition-colors">
                  {item.message}
                </p>
              </div>
              
              {/* Hover arrow indicator */}
              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2 group-hover:translate-x-0">
                <div className="w-6 h-6 rounded-full bg-foreground/10 flex items-center justify-center">
                  <svg className="w-3 h-3 text-foreground/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
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
          Or type your own message below to get started ✨
        </p>
      </div>
    </div>
  )
} 