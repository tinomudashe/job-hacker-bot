"use client";

import { X, Bell } from "lucide-react";
import { Button } from "./button";
import { toast } from "@/lib/toast";
import { useState, useEffect } from "react";

export function DismissAllToasts() {
  const [hasToasts, setHasToasts] = useState(false);

  // This is a simple approach - in a real app you might want to listen to toast events
  useEffect(() => {
    const checkToasts = () => {
      const toastContainer = document.querySelector('[data-sonner-toaster]');
      const toastCount = toastContainer?.children.length || 0;
      setHasToasts(toastCount > 0);
    };

    // Check periodically for toasts
    const interval = setInterval(checkToasts, 1000);
    checkToasts(); // Initial check

    return () => clearInterval(interval);
  }, []);

  if (!hasToasts) return null;

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => {
        toast.dismissAll();
        setHasToasts(false);
      }}
      className="fixed bottom-4 right-4 z-50 bg-background/80 backdrop-blur-sm border border-border shadow-lg hover:shadow-xl transition-all duration-200"
      title="Dismiss all notifications (Ctrl+Shift+X)"
    >
      <Bell className="h-4 w-4 mr-2" />
      <X className="h-3 w-3" />
      <span className="ml-1 text-xs">Clear all</span>
    </Button>
  );
} 