import { ThemeProvider } from "@/components/theme-provider";
import { DismissAllToasts } from "@/components/ui/dismiss-all-toasts";
import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Job Application Assistant",
  description: "Your AI-powered job application assistant",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
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
          <meta
            name="viewport"
            content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"
          />
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
              closeButton={true}
              richColors={true}
              expand={false}
              position="top-right"
              theme="system"
              offset={16}
              gap={8}
              visibleToasts={5}
              toastOptions={{
                duration: 4000,
                classNames: {
                  toast:
                    "bg-background/95 backdrop-blur-md border-border/50 text-foreground shadow-lg group",
                  description: "text-muted-foreground",
                  actionButton:
                    "bg-primary text-primary-foreground hover:bg-primary/90 transition-colors",
                  cancelButton:
                    "bg-muted text-muted-foreground hover:bg-muted/80 transition-colors",
                  closeButton:
                    "bg-transparent border-0 text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors !important opacity-100 !important",
                  success:
                    "bg-background/95 border-green-500/20 text-foreground",
                  error: "bg-background/95 border-red-500/20 text-foreground",
                  warning:
                    "bg-background/95 border-yellow-500/20 text-foreground",
                  info: "bg-background/95 border-blue-500/20 text-foreground",
                },
                style: {
                  borderRadius: "12px",
                  backdropFilter: "blur(16px)",
                  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
                  border: "1px solid hsl(var(--border) / 0.5)",
                },
                unstyled: false,
              }}
            />
            <DismissAllToasts />
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
