"use client";

import { useTheme } from "next-themes";
import { Button } from "./button";
import { useState, useEffect } from "react";
import { Sun, Moon, Monitor, Check } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "./dropdown-menu";
import { cn } from "@/lib/utils";

const themes = [
  { 
    name: "Light", 
    value: "light", 
    icon: Sun,
    description: "Bright and clean",
    color: "text-amber-500"
  },
  { 
    name: "Dark", 
    value: "dark", 
    icon: Moon,
    description: "Easy on the eyes",
    color: "text-blue-400"
  },
  { 
    name: "System", 
    value: "system", 
    icon: Monitor,
    description: "Follows your device",
    color: "text-gray-600 dark:text-gray-400"
  }
];

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="h-10 w-10 rounded-xl" disabled>
        <div className="h-4 w-4 animate-pulse bg-muted rounded" />
      </Button>
    );
  }

  const currentTheme = themes.find(t => t.value === theme) || themes[0];
  const CurrentIcon = currentTheme.icon;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-10 w-10 rounded-xl hover:bg-accent/50 transition-all duration-300 hover:scale-105"
        >
          <CurrentIcon className={cn("h-5 w-5 transition-colors", currentTheme.color)} />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent 
        align="end" 
        className="w-56 bg-background/95 backdrop-blur-xl border border-border/50 shadow-2xl rounded-2xl p-2"
        sideOffset={8}
      >
        {/* Header */}
        <div className="px-3 py-2 text-xs font-semibold text-muted-foreground border-b border-border/30 mb-1">
          Choose theme
        </div>
        
        {/* Theme Options */}
        <div className="space-y-1">
          {themes.map((themeOption) => {
            const Icon = themeOption.icon;
            const isActive = theme === themeOption.value;
            
            return (
              <DropdownMenuItem
                key={themeOption.value}
                onClick={() => setTheme(themeOption.value)}
                className={cn(
                  "cursor-pointer rounded-xl px-3 py-3 transition-all duration-200",
                  "hover:bg-accent/60 focus:bg-accent/60",
                  "group relative overflow-hidden",
                  isActive && "bg-accent/40 shadow-sm"
                )}
              >
                {/* Background glow for active item */}
                {isActive && (
                  <div className={cn(
                    "absolute inset-0 rounded-xl opacity-10",
                    themeOption.value === "light" && "bg-gradient-to-r from-amber-400 to-orange-400",
                    themeOption.value === "dark" && "bg-gradient-to-r from-blue-500 to-indigo-500",
                    themeOption.value === "system" && "bg-gradient-to-r from-gray-400 to-gray-600"
                  )} />
                )}
                
                <div className="flex items-center gap-3 w-full relative z-10">
                  <div className={cn(
                    "flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200",
                    isActive 
                      ? "bg-primary/10 shadow-sm" 
                      : "bg-muted/50 group-hover:bg-muted/80"
                  )}>
                    <Icon className={cn(
                      "h-4 w-4 transition-colors",
                      isActive ? themeOption.color : "text-muted-foreground group-hover:text-foreground"
                    )} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className={cn(
                      "font-medium text-sm transition-colors",
                      isActive ? "text-foreground" : "text-foreground/90"
                    )}>
                      {themeOption.name}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {themeOption.description}
                    </div>
                  </div>
                  
                  {isActive && (
                    <div className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10">
                      <Check className="h-3.5 w-3.5 text-primary" />
                    </div>
                  )}
                </div>
              </DropdownMenuItem>
            );
          })}
        </div>
        
        {/* System Theme Status */}
        {theme === "system" && (
          <div className="mt-2 pt-2 border-t border-border/30">
            <div className="px-3 py-2 rounded-xl bg-muted/30 border border-border/20">
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  resolvedTheme === "dark" ? "bg-blue-400" : "bg-amber-400"
                )} />
                <span className="text-xs text-muted-foreground">
                  Currently: <span className="font-medium text-foreground">
                    {resolvedTheme === "dark" ? "Dark" : "Light"}
                  </span> (auto)
                </span>
              </div>
            </div>
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
} 