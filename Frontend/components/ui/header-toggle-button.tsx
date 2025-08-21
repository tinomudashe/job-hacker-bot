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
        "fixed top-8 right-8 z-[100]", // Much higher z-index to ensure it's always on top
        "flex items-center gap-1 px-2 py-1",
        "bg-background/80 backdrop-blur-xl backdrop-saturate-150",
        "border border-white/10 hover:border-white/20",
        "rounded-full shadow-2xl",
        "text-[10px] text-muted-foreground hover:text-foreground",
        "transition-all duration-300 hover:scale-105 active:scale-95",
        "group animate-pulse" // Add pulsating animation
      )}
      title={isHeaderVisible ? "Hide header options (Ctrl+H)" : "Show header options (Ctrl+H)"}
      aria-label={isHeaderVisible ? "Hide header options" : "Show header options"}
    >
      {isHeaderVisible ? (
        <EyeOff className="w-3 h-3 group-hover:scale-110 transition-transform" />
      ) : (
        <Eye className="w-3 h-3 group-hover:scale-110 transition-transform" />
      )}
      <span className="hidden sm:inline text-[10px]">
        {isHeaderVisible ? "Hide header options" : "Show header options"}
      </span>
    </button>
  );
}