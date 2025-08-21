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
        "fixed top-4 right-4 z-[100]", // Much higher z-index to ensure it's always on top
        "flex items-center gap-1.5 px-2.5 py-1.5",
        "bg-background/80 backdrop-blur-xl backdrop-saturate-150",
        "border border-white/10 hover:border-white/20",
        "rounded-full shadow-2xl",
        "text-xs text-muted-foreground hover:text-foreground",
        "transition-all duration-300 hover:scale-105 active:scale-95",
        "group"
      )}
      title={isHeaderVisible ? "Hide header options (Ctrl+H)" : "Show header options (Ctrl+H)"}
      aria-label={isHeaderVisible ? "Hide header options" : "Show header options"}
    >
      {isHeaderVisible ? (
        <EyeOff className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
      ) : (
        <Eye className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
      )}
      <span className="hidden sm:inline text-xs">
        {isHeaderVisible ? "Hide header options" : "Show header options"}
      </span>
    </button>
  );
}