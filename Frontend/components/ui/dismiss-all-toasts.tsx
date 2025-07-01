"use client";

import { Bell, X } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "./button";

export function DismissAllToasts() {
  const [hasToasts, setHasToasts] = useState(false);

  // Check for toasts more efficiently and safely
  useEffect(() => {
    const checkToasts = () => {
      try {
        const toastContainer = document.querySelector("[data-sonner-toaster]");
        const toasts =
          toastContainer?.querySelectorAll("[data-sonner-toast]") || [];
        const toastCount = toasts.length;
        setHasToasts(toastCount > 0);
      } catch (error) {
        console.warn("Error checking toasts:", error);
        setHasToasts(false);
      }
    };

    // Initial check
    checkToasts();

    // Check periodically for toasts (reduced frequency to avoid interference)
    const interval = setInterval(checkToasts, 2000);

    // Also listen for DOM mutations to detect toast changes more efficiently
    const observer = new MutationObserver(() => {
      checkToasts();
    });

    const toastContainer = document.querySelector("[data-sonner-toaster]");
    if (toastContainer) {
      observer.observe(toastContainer, {
        childList: true,
        subtree: true,
      });
    }

    return () => {
      clearInterval(interval);
      observer.disconnect();
    };
  }, []);

  if (!hasToasts) return null;

  const handleDismissAll = () => {
    try {
      // Use the native Sonner dismiss method
      toast.dismiss();
      setHasToasts(false);
    } catch (error) {
      console.error("Error dismissing all toasts:", error);
    }
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleDismissAll}
      className="fixed bottom-4 right-4 z-50 bg-background/80 backdrop-blur-sm border border-border shadow-lg hover:shadow-xl transition-all duration-200"
      title="Dismiss all notifications (Ctrl+Shift+X)"
      style={{ pointerEvents: "auto" }}
    >
      <Bell className="h-4 w-4 mr-2" />
      <X className="h-3 w-3" />
      <span className="ml-1 text-xs">Clear all</span>
    </Button>
  );
}
