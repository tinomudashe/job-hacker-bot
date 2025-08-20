"use client";

import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function Logo({ className, size = "md" }: LogoProps) {
  const sizeClasses = {
    sm: "w-8 h-8 text-sm",
    md: "w-10 h-10 sm:w-12 sm:h-12 text-lg sm:text-xl",
    lg: "w-16 h-16 text-2xl",
  };

  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-xl transition-all duration-200 hover:scale-105",
        "bg-primary hover:bg-primary/90",
        "shadow-sm hover:shadow-md",
        sizeClasses[size],
        className
      )}
    >
      {/* Main logo container */}
      <div className="relative z-10 flex items-center justify-center w-full h-full">
        <div className="flex items-center justify-center">
          {/* Job Hacker monogram */}
          <span className="font-black text-primary-foreground tracking-[-0.08em] leading-none flex items-center relative">
            {/* Lowercase j */}
            <span className="inline-block">
              j
            </span>
            {/* Uppercase H */}
            <span className="inline-block scale-[0.85] -ml-[0.08em] translate-y-[-0.12em]">
              H
            </span>
          </span>
        </div>
      </div>
    </div>
  );
}

export function LogoWithText({
  className,
  showSubtext = true,
}: {
  className?: string;
  showSubtext?: boolean;
}) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <Logo size="md" />
      <div className="flex flex-col">
        <h1 className="text-base sm:text-lg font-semibold text-foreground leading-tight">
          Job Hacker Bot
        </h1>
        {showSubtext && (
          <p className="text-xs sm:text-sm text-muted-foreground font-normal">
            Your career co-pilot
          </p>
        )}
      </div>
    </div>
  );
}

// Minimal logo variant for compact spaces
export function MinimalLogo({ className, size = "sm" }: LogoProps) {
  const sizeClasses = {
    sm: "w-7 h-7 text-xs",
    md: "w-9 h-9 text-sm",
    lg: "w-12 h-12 text-base",
  };

  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-lg",
        "bg-primary/10 hover:bg-primary/20",
        "transition-colors duration-200",
        sizeClasses[size],
        className
      )}
    >
      <span className="font-bold text-primary">jH</span>
    </div>
  );
}

// Premium logo variant with subtle enhancements
export function PremiumLogo({ className, size = "md" }: LogoProps) {
  const sizeClasses = {
    sm: "w-8 h-8 text-sm",
    md: "w-10 h-10 sm:w-12 sm:h-12 text-lg sm:text-xl",
    lg: "w-16 h-16 text-2xl",
  };

  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-xl transition-all duration-300 hover:scale-110",
        "bg-gradient-to-br from-primary to-primary/80",
        "shadow-lg hover:shadow-xl group overflow-hidden",
        sizeClasses[size],
        className
      )}
    >
      {/* Subtle shine effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      {/* Main logo */}
      <div className="relative z-10 flex items-center justify-center">
        <span className="font-black text-primary-foreground tracking-[-0.05em] leading-none flex items-center">
          <span className="inline-block">j</span>
          <span className="inline-block scale-[0.85] -ml-[0.08em] translate-y-[-0.12em]">H</span>
        </span>
      </div>
    </div>
  );
}