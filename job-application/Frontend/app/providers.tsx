"use client";

import { ThemeProvider } from "next-themes";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <header className="p-4 flex justify-end items-center gap-4">
        <ThemeToggle />
        <SignedOut>
          <SignInButton />
        </SignedOut>
        <SignedIn>
          <UserButton />
        </SignedIn>
      </header>
      <main>{children}</main>
    </ThemeProvider>
  );
} 