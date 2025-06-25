import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ClerkProvider } from "@clerk/nextjs";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";
import { DismissAllToasts } from "@/components/ui/dismiss-all-toasts";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Job Application Assistant",
  description: "Your AI-powered job application assistant",
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "white" },
    { media: "(prefers-color-scheme: dark)", color: "black" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
        </head>
        <body className={inter.className}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {children}
            <Toaster 
              closeButton
              richColors
              expand={false}
              position="top-right"
              theme="system"
              toastOptions={{
                duration: 4000,
                classNames: {
                  toast: 'bg-background/95 backdrop-blur-md border-border/50 text-foreground shadow-lg',
                  description: 'text-muted-foreground',
                  actionButton: 'bg-primary text-primary-foreground hover:bg-primary/90',
                  cancelButton: 'bg-muted text-muted-foreground hover:bg-muted/80',
                  closeButton: 'bg-background border-border text-foreground hover:bg-accent',
                  success: 'bg-background/95 border-green-500/20 text-foreground',
                  error: 'bg-background/95 border-red-500/20 text-foreground', 
                  warning: 'bg-background/95 border-yellow-500/20 text-foreground',
                  info: 'bg-background/95 border-blue-500/20 text-foreground',
                },
                style: {
                  borderRadius: '12px',
                  backdropFilter: 'blur(16px)',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                }
              }}
            />
            <DismissAllToasts />
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
