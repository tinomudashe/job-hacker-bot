"use client";

import { Button } from "@/components/ui/button";
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
import { useEffect, useState } from "react";
import { cn } from "../../lib/utils";

interface AIProgressIndicatorProps {
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
    | "linkedin_api";
  className?: string;
  onCancel?: () => void;
}

const progressMessages = [
  "Thinking...",
  "Please wait...",
  "While you wait, here are some interesting facts about the job market...",
  "Global unemployment remains near 5% in 2024‑25, ILO reports.",
  "ILO lowered 2025 job growth forecast to 53 million.",
  "AI‑exposed roles grew 38% globally from 2019 to 2024.",
  "AI-skilled workers earn 56% higher wages, PwC data.",
  "AI drives 4× productivity in exposed industries, PwC finds.",
  "Remote work comprises ~30% of workdays worldwide.",
  "Gig economy comprises 17% of global workforce.",
  "Generative AI job postings hit ~16,000/month late‑2024.",
  "AI job postings on LinkedIn grew 38% (2020‑24).",
  "AI roles now ~14% of all software jobs.",
  "Microsoft AI specialists earn up to $377K/year.",
  "Tech firms offer $100M signing bonuses for AI talent.",
  "Tech companies give $200K pay premiums for AI skills.",
  "AI roles range $32K–$399K; average $115K.",
  "Switzerland pays highest average AI salaries globally.",
  "Denmark, Norway follow Switzerland in AI salaries.",
  "US ranks fourth in AI salary globally.",
  "Nigeria’s graduate unemployment rate ~58%.",
  "Youth unemployment hits ~12.6% globally.",
  "South Africa youth unemployment >30%.",
  "OECD unemployment stood at 4.9% in May 2025.",
  "OECD employment rate reached record 72.1%.",
  "OECD participation rate ~76.6% in Q1 2025.",
  "60% of businesses expect inflation to transform via 2030.",
  "42% of businesses expect slowdown to transform by 2030.",
  "47% expect climate adaptation to transform business.",
  "41% expect green transition to transform business.",
  "Green economy could create 24M jobs by 2030.",
  "72M jobs lost globally due to heat stress risk.",
  "41% projected wage premium for AI-complementary skills.",
  "AI complemented human skills 50% more than substituted.",
  "Skills-based hiring rose 15% for AI roles (UK).",
  "Degree requirement fell ~15% for AI jobs (UK).",
  "AI skills yield 23% wage premium over degrees.",
  "Job vacancies exceed unemployed by 1.5× in US.",
  "Remote work policies continue evolving in 2025.",
  "Hybrid models now common in tech and finance.",
  "33% of US employers required full in-office by 2024.",
  "Generative AI impacts diagnostics in healthcare significantly.",
  "Automation boosts fraud detection in finance.",
  "903 job posts listed 'ChatGPT' as skill requirement.",
  "88% of these roles in automation‑prone categories.",
  "Half of AI specialists seek unskilled roles now.",
  "62.8% of remote job seekers hold higher degrees.",
  "70% of remote gig seekers are women.",
  "85% of African informal jobs held by women.",
  "Indoor women informal rates: 92% Africa, 65% Asia.",
  "Brazil has 934K renewable-energy jobs.",
  "Australia had 20K green jobs in 2018.",
  "Nigeria allows remote digital labor migration.",
  "Vocational training demand rising globally.",
  "Skills in ethics, resilience growing due to AI.",
  "Upskilling speed in AI roles 66% faster.",
  "Job ads requiring AI ethics leadership increasing.",
  "High-skilled non-routine tasks susceptible to AI.",
  "Wage benefits vary across AI‑susceptible occupations.",
  "Past bootcamps produced underwhelming reskilling outcomes.",
  "Sweden offers paid lifelong‑learning furlough schemes.",
  "Governments in 28 countries have AI workforce strategies.",
  "Global talent shortage could hit 85M by 2030.",
  "Women’s labor participation 53% globally in 2022.",
  "Oceania reports highest female labor participation (~65%).",
  "Central Asia female participation lowest (~40%).",
  "Nigeria had 77% female labor participation.",
  "Women hold ~34% senior management roles globally.",
  "Women of color underrepresented in senior roles.",
  "Automation risk >75% in Thailand, Vietnam jobs.",
  "50–85% developing country jobs face automation risk.",
  "McKinsey estimates 400‑800M jobs automatable by 2030.",
  "Banlisa: 59% of business processes automatable.",
  "Automation in manufacturing: 478B hours/year automatable.",
  "Tailored micro‑certifications aid AI/green job readiness.",
  "Vocational education reduces mismatches in digital labor.",
  "Gig economy revenues to hit $1.85T by 2032.",
  "US freelancers make 38% of workforce.",
  "Forbes: US gig economy worth $1.27T.",
  "Entry-level roles now require AI fluency.",
  "Gen Z favor trades amid AI disruption.",
  "Mass layoffs in tech: Intel, Meta, Chevron.",
  "41% companies expect AI-related layoffs by 2030.",
  "Meta, Microsoft, BP cut thousands of jobs.",
  "Healthcare jobs remain resilient globally.",
  "Renewables fastest‑growing energy job sector.",
  "Cybersecurity demand surging worldwide.",
  "Big Data Specialist demand +117% by 2030.",
  "Wind turbine technician roles +60% growth.",
  "Solar installer jobs +48% globally.",
  "Nurse practitioner roles +46% US growth.",
  "Data scientist roles +36% growth.",
  "Info security analysts +33% job growth.",
  "Future: 78M net jobs created by 2030.",
  "Displaced jobs ~92M due to automation.",
  "Net 170M new roles by 2030 projected.",
  "Structural shifts create net 78M jobs.",
  "Educational lag: 58% graduates unemployed globally.",
  "Graduates' job confidence high but hiring low.",
  "Work experience trumps degrees for graduate hiring.",
  "LinkedIn effective but resumes still barrier.",
  "Skill-based hiring exceeds degree preferences worldwide.",
  "Healthcare, energy, tech drive recent job growth.",
  "HBR: jobs listing ChatGPT increased 903 postings.",
  "World Bank: developing jobs vulnerable to automation.",
  "France pushes retrofitting jobs for green growth.",
  "UK invests in battery factory employment.",
  "Cycle lanes retrofitting creates new Europe jobs.",
  "UN: long-term unemployment increased to 1.6M US.",
  "Long-term unemployed = 23.3% of all unemployed US.",
  "Unemployment rate stable near 4.1% in US.",
  "Average US pay: $36.30/hour in June 2025.",
  "Hourly pay up 3.7% YoY in US.",
  "State gov jobs +47K in June US.",
  "Healthcare jobs +39K in June US.",
  "Local education jobs +23K US June.",
  "Federal US jobs down 7K in June.",
  "Labor participation US = 62.3% in June.",
  "US employment‑population ratio = 59.7%.",
  "Part‑time economic reasons: 4.5M Americans.",
  "Marginally attached workers US: 1.8M.",
  "Discouraged US workers: 637K.",
  "April/May US job data upwardly revised.",
  "AI may both displace and enhance roles.",
  "Policy: focus adaptability over job protection.",
  "Sweden prioritizes worker adaptability training.",
  "China tech graduates prefer startups not government.",
  "Brazil workforce strong in informal green jobs.",
  "Kenya leads African remote tech hiring.",
  "India's AI mission trained 3.8M by 2025.",
  "28 governments now have AI workforce strategies.",
  "Green job creation offsets traditional job losses.",
  "Global remote work stabilizing post‑COVID era.",
  "Almost there — compiling personalized insights now.",
];

const iconComponents = {
  thinking: Brain,
  searching: Search,
  generating: FileText,
  processing: Zap,
  downloading: Download,
  browser_automation: Globe,
  job_search: Briefcase,
  linkedin_api: Briefcase,
  // Fix: Add missing keys to prevent TypeScript error.
  "calling tool": Zap,
  reasoning: Brain,
  "calling api": Globe,
};

export function AIProgressIndicator({
  isLoading,
  progressText,
  progressType = "thinking",
  className,
  onCancel,
}: AIProgressIndicatorProps) {
  // Fix: Moved state declarations to the top level of the component.
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [hasReadInitialMessages, setHasReadInitialMessages] = useState(false);

  const IconComponent = iconComponents[progressType] || iconComponents.thinking;

  // Fix: Combined and corrected the message cycling logic.
  useEffect(() => {
    if (!isLoading) {
      setCurrentMessageIndex(0);
      setHasReadInitialMessages(false); // Reset state when not loading.
      return;
    }

    // This interval will now cycle through messages every 3 seconds.
    const messageInterval = setInterval(() => {
      setCurrentMessageIndex((prev) => {
        // Sequentially show the first two messages.
        if (!hasReadInitialMessages) {
          if (prev < 1) {
            return prev + 1;
          }
          setHasReadInitialMessages(true);
          // After the first two, pick a random message from the rest.
          return 2 + Math.floor(Math.random() * (progressMessages.length - 2));
        }

        // Continue picking random messages from the list.
        return 2 + Math.floor(Math.random() * (progressMessages.length - 2));
      });
    }, 5000); // Adjusted timing to 5 seconds.

    return () => clearInterval(messageInterval);
  }, [isLoading, hasReadInitialMessages]);

  if (!isLoading) return null;

  // Add "Did you know: " to fact-based loading messages.
  const rawMessage = progressText || progressMessages[currentMessageIndex];
  const isFact =
    !progressText &&
    currentMessageIndex > 2 &&
    currentMessageIndex < progressMessages.length - 1;
  const currentMessage = isFact ? `Did you know: ${rawMessage}` : rawMessage;

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
