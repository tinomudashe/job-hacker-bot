"use client";

import { PageProvider } from "@/lib/hooks/use-page-context";
import { ClerkProvider } from "@clerk/nextjs";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { type ThemeProviderProps } from "next-themes/dist/types";

export function Providers({ children, ...props }: ThemeProviderProps) {
  return (
    <ClerkProvider>
      <NextThemesProvider {...props}>
        <PageProvider>{children}</PageProvider>
      </NextThemesProvider>
    </ClerkProvider>
  );
}
