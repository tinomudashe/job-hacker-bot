"use client";

import { useTheme } from "next-themes";
import { Button } from "./button";
import { useState, useEffect } from "react";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="relative h-10 w-10 rounded-xl hover:bg-accent/50 transition-all duration-300 hover:scale-105 overflow-hidden"
    >
      <span className="sr-only">Toggle theme</span>
      <div className="relative w-5 h-5">
        {/* Sun Icon */}
        <Sun 
          className={`absolute inset-0 h-5 w-5 transition-all duration-500 transform ${
            theme === "dark" 
              ? "rotate-90 scale-0 opacity-0 text-muted-foreground" 
              : "rotate-0 scale-100 opacity-100 text-amber-500 dark:text-amber-400"
          }`}
        />
        {/* Moon Icon */}
        <Moon 
          className={`absolute inset-0 h-5 w-5 transition-all duration-500 transform ${
            theme === "dark" 
              ? "rotate-0 scale-100 opacity-100 text-blue-400 dark:text-blue-300" 
              : "-rotate-90 scale-0 opacity-0 text-muted-foreground"
          }`}
        />
      </div>
      
      {/* Theme-aware background glow */}
      <div className={`absolute inset-0 rounded-xl transition-all duration-300 ${
        theme === "dark" 
          ? "bg-gradient-to-br from-blue-500/5 to-indigo-500/5 dark:from-blue-400/10 dark:to-indigo-400/10" 
          : "bg-gradient-to-br from-amber-400/5 to-orange-400/5 dark:from-amber-300/10 dark:to-orange-300/10"
      }`} />
    </Button>
  );
} 