"use client";

import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeaderToggleButtonProps {
  isHeaderVisible: boolean;
  onToggle: () => void;
}

export function HeaderToggleButton({ isHeaderVisible, onToggle }: HeaderToggleButtonProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn(
        "fixed top-8 right-8 z-[60]", // Above header (z-50) but below dialogs (z-50+ for modals)
        "flex items-center gap-1.5 px-3 py-2",
        "bg-background/80 backdrop-blur-xl backdrop-saturate-150",
        "border border-white/10 hover:border-white/20",
        "rounded-full shadow-2xl",
        "text-xs text-muted-foreground hover:text-foreground",
        "transition-all duration-300 hover:scale-105 active:scale-95",
        "group animate-pulse" // Add pulsating animation
      )}
      title={isHeaderVisible ? "Hide header options (Ctrl+H)" : "Show header options (Ctrl+H)"}
      aria-label={isHeaderVisible ? "Hide header options" : "Show header options"}
    >
      {isHeaderVisible ? (
        <EyeOff className="w-4 h-4 group-hover:scale-110 transition-transform" />
      ) : (
        <Eye className="w-4 h-4 group-hover:scale-110 transition-transform" />
      )}
      <span className="hidden sm:inline text-xs">
        {isHeaderVisible ? "Hide header options" : "Show header options"}
      </span>
    </button>
  );
}