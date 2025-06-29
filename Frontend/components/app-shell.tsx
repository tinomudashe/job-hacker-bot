"use client";

import * as React from "react";
import {
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-50 flex items-center justify-between w-full h-16 px-4 border-b shrink-0 bg-gradient-to-b from-background to-background/80 backdrop-blur-xl">
        <div className="flex items-center">
          <React.Suspense
            fallback={
              <div className="flex items-center">
                <Sparkles className="w-6 h-6 mr-2" />
                <div className="font-semibold">Next.js Gemini Chatbot</div>
              </div>
            }
          >
          </React.Suspense>
        </div>
        <div className="flex items-center justify-end space-x-2">
          <Button variant="outline" asChild>
            <a
              target="_blank"
              href="https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvercel%2Fai%2Ftree%2Fmain%2Fexamples%2Fnext-ai-sdk&env=GOOGLE_GENERATIVE_AI_API_KEY&envDescription=Google%20Generative%20AI%20API%20Key&envLink=https%3A%2F%2Fai.google.dev%2F"
              rel="noopener noreferrer"
            >
              Deploy
            </a>
          </Button>
          <Button asChild>
            <a href="/login">Login</a>
          </Button>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
} 