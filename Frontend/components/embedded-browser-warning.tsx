"use client";

import { AlertCircle, ExternalLink, Chrome, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { useEffect, useState } from "react";

export function EmbeddedBrowserWarning() {
  const [isEmbedded, setIsEmbedded] = useState(false);
  const [currentUrl, setCurrentUrl] = useState("");

  useEffect(() => {
    // Check if we're in an embedded browser
    const userAgent = navigator.userAgent || "";
    const isEmbeddedBrowser = checkIfEmbedded(userAgent);
    setIsEmbedded(isEmbeddedBrowser);
    setCurrentUrl(window.location.href);
  }, []);

  const checkIfEmbedded = (userAgent: string): boolean => {
    // Check for common embedded browser patterns
    const patterns = [
      /FB_IAB/i,  // Facebook in-app browser
      /FBAN/i,    // Facebook app
      /Instagram/i,
      /Line/i,
      /MicroMessenger/i,  // WeChat
      /WhatsApp/i,
      /Telegram/i,
      /Twitter/i,
      /LinkedInApp/i,
      /GSA/i,     // Google Search App
    ];
    
    return patterns.some(pattern => pattern.test(userAgent));
  };

  const openInExternalBrowser = () => {
    // Try to open in external browser
    if (typeof window !== "undefined") {
      // For mobile devices, this will prompt to open in default browser
      window.open(currentUrl, "_system");
      
      // Alternative method - copy URL to clipboard
      navigator.clipboard.writeText(currentUrl).then(() => {
        alert("URL copied! Please paste it in your browser.");
      });
    }
  };

  if (!isEmbedded) return null;

  return (
    <div className="mx-auto max-w-md mb-6">
      <div className="rounded-xl border border-border bg-card p-6 shadow-lg">
        <div className="flex items-start gap-3">
          <div className="rounded-full bg-orange-100 dark:bg-orange-900/20 p-2">
            <AlertCircle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
          </div>
          <div className="flex-1 space-y-3">
            <div>
              <h3 className="font-semibold text-foreground">
                Browser Compatibility Issue
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Google Sign-In doesn't work in this embedded browser. Please open in your regular browser.
              </p>
            </div>
            
            <div className="flex flex-col gap-2">
              <Button
                onClick={openInExternalBrowser}
                className="w-full"
                variant="default"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                Open in External Browser
              </Button>
              
              <Button
                variant="outline"
                onClick={() => {
                  navigator.clipboard.writeText(currentUrl);
                  const toast = document.createElement('div');
                  toast.textContent = 'URL copied to clipboard!';
                  toast.className = 'fixed bottom-4 right-4 bg-foreground text-background px-4 py-2 rounded-lg shadow-lg z-50 animate-in slide-in-from-bottom-2';
                  document.body.appendChild(toast);
                  setTimeout(() => toast.remove(), 3000);
                }}
                className="w-full"
              >
                <Globe className="mr-2 h-4 w-4" />
                Copy URL to Clipboard
              </Button>
            </div>

            <div className="rounded-lg bg-muted/50 p-3 space-y-2">
              <p className="text-xs font-medium text-foreground">
                Quick Fix Instructions:
              </p>
              <ol className="text-xs text-muted-foreground space-y-1.5">
                <li className="flex gap-2">
                  <span className="font-semibold text-foreground">1.</span>
                  <span>Tap the menu (⋮ or ⋯) in the top corner</span>
                </li>
                <li className="flex gap-2">
                  <span className="font-semibold text-foreground">2.</span>
                  <span>Select "Open in Browser" or "Open in Chrome"</span>
                </li>
                <li className="flex gap-2">
                  <span className="font-semibold text-foreground">3.</span>
                  <span>Sign in with Google from there</span>
                </li>
              </ol>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <Chrome className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">
                Works best in Chrome, Safari, Firefox, or Edge
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}