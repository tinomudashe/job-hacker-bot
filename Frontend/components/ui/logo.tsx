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
        "relative flex items-center justify-center rounded-2xl shadow-xl transition-all duration-300 hover:scale-105 hover:shadow-2xl",
        "bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700",
        "border border-blue-400/30 backdrop-blur-sm group overflow-hidden",
        sizeClasses[size],
        className
      )}
    >
      {/* Animated background glow */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-400/30 via-blue-500/20 to-indigo-600/30 blur-lg opacity-60 group-hover:opacity-80 transition-opacity duration-300" />

      {/* Outer glow ring */}
      <div className="absolute inset-[-2px] rounded-2xl bg-gradient-to-br from-blue-400/20 via-transparent to-indigo-600/20 blur-sm" />

      {/* Subtle tech grid pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_24%,rgba(255,255,255,0.1)_25%,rgba(255,255,255,0.1)_26%,transparent_27%),linear-gradient(rgba(255,255,255,0.1)_24%,transparent_25%,transparent_26%,rgba(255,255,255,0.1)_27%)] bg-[length:8px_8px]" />
      </div>

      {/* Main logo container */}
      <div className="relative z-10 flex items-center justify-center w-full h-full">
        <div className="flex items-center justify-center">
          {/* Job Hacker monogram with refined typography */}
          <span className="font-black text-white tracking-[-0.08em] leading-none flex items-center relative">
            {/* Lowercase j with perfect positioning */}
            <span className="inline-block transform hover:scale-110 transition-transform duration-200 drop-shadow-sm">
              j
            </span>
            {/* Uppercase H with refined positioning for lowercase j */}
            <span className="inline-block transform scale-[0.85] -ml-[0.08em] translate-y-[-0.12em] opacity-95 relative">
              {/* Shadow behind H */}
              <span className="absolute inset-0 text-black/20 blur-[0.5px] translate-x-[0.5px] translate-y-[0.5px]">
                H
              </span>
              {/* Main H with drop shadow */}
              <span className="relative drop-shadow-sm">H</span>
            </span>

            {/* Subtle accent dot - tech inspired */}
            <span className="absolute -top-[0.1em] -right-[0.1em] w-[0.15em] h-[0.15em] bg-white/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-[0.5px]" />
          </span>
        </div>
      </div>

      {/* Enhanced layered highlights */}
      <div className="absolute inset-[1px] rounded-2xl bg-gradient-to-br from-white/25 via-white/8 to-transparent pointer-events-none" />
      <div className="absolute inset-[2px] rounded-2xl bg-gradient-to-tr from-transparent via-white/5 to-white/15 pointer-events-none" />

      {/* Premium bottom shine with gradient */}
      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-4/5 h-[1px] bg-gradient-to-r from-transparent via-white/40 to-transparent rounded-full" />

      {/* Subtle top highlight */}
      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-3/5 h-[0.5px] bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-full" />
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
    <div className={cn("flex items-center space-x-3 min-w-0", className)}>
      <Logo size="md" />
      <div className="min-w-0 flex-1">
        <h1 className="text-sm sm:text-base md:text-xl font-bold bg-gradient-to-r from-foreground via-foreground to-foreground/85 bg-clip-text text-transparent truncate tracking-tight">
          Job Hacker Bot
        </h1>
        {showSubtext && (
          <p className="text-xs text-muted-foreground/80 -mt-0.5 hidden sm:block font-medium tracking-wide">
            AI-Powered Assistant
          </p>
        )}
      </div>
    </div>
  );
}

// Premium logo variant with enhanced effects
export function PremiumLogo({ className, size = "md" }: LogoProps) {
  const sizeClasses = {
    sm: "w-8 h-8 text-sm",
    md: "w-10 h-10 sm:w-12 sm:h-12 text-lg sm:text-xl",
    lg: "w-16 h-16 text-2xl",
  };

  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-2xl shadow-2xl transition-all duration-500 hover:scale-110 hover:shadow-3xl",
        "bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700",
        "border border-blue-400/40 backdrop-blur-lg group overflow-hidden",
        sizeClasses[size],
        className
      )}
    >
      {/* Animated background particles */}
      <div className="absolute inset-0 opacity-20">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="absolute w-0.5 h-0.5 bg-white rounded-full opacity-60 animate-pulse"
            style={{
              left: `${15 + i * 25}%`,
              top: `${25 + i * 20}%`,
              animationDelay: `${i * 0.7}s`,
              animationDuration: `${2.5 + i * 0.5}s`,
            }}
          />
        ))}
      </div>

      {/* Premium glow effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-400/40 via-indigo-500/30 to-purple-600/40 blur-xl group-hover:blur-2xl transition-all duration-500" />

      {/* Rotating border accent */}
      <div className="absolute inset-0 rounded-2xl border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* Main logo with enhanced effects */}
      <div className="relative z-10 flex items-center justify-center">
        <span className="font-black text-white tracking-[-0.05em] leading-none flex items-center relative drop-shadow-lg">
          <span className="inline-block transform group-hover:rotate-2 transition-transform duration-300">
            j
          </span>
          <span className="inline-block transform scale-[0.85] -ml-[0.08em] translate-y-[-0.12em] opacity-95 group-hover:-rotate-2 transition-transform duration-300 relative">
            {/* Shadow behind H */}
            <span className="absolute inset-0 text-black/25 blur-[0.5px] translate-x-[0.5px] translate-y-[0.5px]">
              H
            </span>
            {/* Main H with enhanced shadow */}
            <span className="relative drop-shadow-md">H</span>
          </span>

          {/* Premium accent elements */}
          <span className="absolute -top-[0.15em] -right-[0.1em] w-[0.1em] h-[0.1em] bg-white/80 rounded-full group-hover:scale-150 transition-transform duration-300" />
          <span className="absolute -bottom-[0.1em] -left-[0.05em] w-[0.08em] h-[0.08em] bg-white/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        </span>
      </div>

      {/* Multiple premium layered highlights */}
      <div className="absolute inset-[1px] rounded-2xl bg-gradient-to-br from-white/30 via-white/10 to-transparent pointer-events-none" />
      <div className="absolute inset-[2px] rounded-2xl bg-gradient-to-tr from-transparent via-white/8 to-white/15 pointer-events-none" />
      <div className="absolute inset-[3px] rounded-2xl bg-gradient-to-b from-white/5 via-transparent to-transparent pointer-events-none" />
    </div>
  );
}
