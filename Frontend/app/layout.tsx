import { ThemeProvider } from "@/components/theme-provider";
import { DismissAllToasts } from "@/components/ui/dismiss-all-toasts";
import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";
import { GoogleAnalytics } from "@/components/google-analytics";
import { TikTokPixel } from "@/components/tiktok-pixel";
import { UserbackWidget } from "@/components/userback-widget";
import { ChromeExtensionBridge } from "@/components/chrome-extension-bridge";
import { ExtensionIntegration } from "@/components/extension-integration";

// This is the only new import being added.
const CookieConsentBanner = dynamic(
  () =>
    import("@/components/cookie-consent-banner").then(
      (mod) => mod.CookieConsentBanner
    ),
  { ssr: false }
);

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL("https://jobhackerbot.com"),
  title: {
    default: "Job Hacker Bot | Your AI-Powered Job Application Assistant",
    template: `%s | Job Hacker Bot`,
  },
  description:
    "Streamline your job search with an AI-powered assistant that helps you find jobs, tailor your resume, generate cover letters, and ace interviews.",
  applicationName: "Job Hacker Bot",
  keywords: [
    "AI job assistant",
    "job search automation",
    "resume builder",
    "cover letter generator",
    "interview preparation",
    "career advice",
    "AI career copilot",
    "custom resume themes",
    "downloadable resume",
    "downloadable cover letter",
    "job listing bot",
    "job recommendation engine",
    "personalized job search",
    "AI for job seekers",
    "automated job applications",
    "tailored job matching",
    "career development tool",
    "smart job hunting",
    "job hacker bot",
    "AI job application tool",
    "job search platform",
    "intelligent job matching",
    "career automation tool",
    "AI-powered resume assistant",
    "job hunting assistant",
  ],
  openGraph: {
    title: "Job Hacker Bot | Your AI-Powered Job Application Assistant",
    description:
      "Streamline your job search with an AI-powered assistant that helps you find jobs, tailor your resume, generate cover letters, and ace interviews.",
    url: "https://jobhackerbot.com",
    siteName: "Job Hacker Bot",
    images: [
      {
        url: "/og-image.png", // Must be a relative path
        width: 1200,
        height: 630,
        alt: "Job Hacker Bot a futuristic, AI-powered job application assistant",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Job Hacker Bot | Your AI-Powered Job Application Assistant",
    description:
      "Streamline your job search with an AI-powered assistant that helps you find jobs, tailor your resume, generate cover letters, and ace interviews.",
    images: [
      {
        url: "/og-image.png", // Must be a relative path
        width: 1200,
        height: 630,
        alt: "Job Hacker Bot a futuristic, AI-powered job application assistant",
      },
    ],
  },
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
          {process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID && (
            <GoogleAnalytics measurementId={process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID} />
          )}
          <TikTokPixel pixelId="D2K46TRC77U0CGBH7UH0" />
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {children}
            <ChromeExtensionBridge />
            <UserbackWidget />
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
            {/* This is the only new line of code being added. */}
            <CookieConsentBanner />
            <ExtensionIntegration />
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
