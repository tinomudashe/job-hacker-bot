"use client";

import { Button } from "@/components/ui/button";
import { useIsWebview } from "@/lib/hooks/use-is-webview";
import { useSubscription } from "@/lib/hooks/use-subscription";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import {
  AlertTriangle,
  Menu,
  MessageSquare,
  Plus,
  Settings,
  X,
} from "lucide-react";
import { usePathname } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";
import { ConversationDialog } from "./conversation-dialog";
import { PricingDialog } from "./pricing-dialog";
import { SettingsDialog } from "./settings-dialog";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { LogoWithText } from "./ui/logo";
import { SubscriptionBadge } from "./ui/subscription-badge";
import { ThemeToggle } from "./ui/theme-toggle";

interface HeaderProps {
  onNewChat: () => void;
  onClearChat?: () => void;
  currentPageId?: string;
  onSelectPage: (pageId: string) => void;
  isLoginPage?: boolean;
}

export function Header({
  onNewChat,
  onClearChat,
  currentPageId,
  onSelectPage,
  isLoginPage = false,
}: HeaderProps) {
  const [showPagesDialog, setShowPagesDialog] = React.useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = React.useState(false);
  const [showMobileMenu, setShowMobileMenu] = React.useState(false);
  const [isMounted, setIsMounted] = React.useState(false);
  const isWebview = useIsWebview();
  const { subscription } = useSubscription();
  const pathname = usePathname();
  const [showPricingDialog, setShowPricingDialog] = React.useState(false);

  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("checkout") === "success") {
      setShowSettingsDialog(true);
      toast.success("Welcome to Pro! Your subscription is active.");
      window.history.replaceState(null, "", window.location.pathname);
    } else if (params.get("checkout") === "cancel") {
      setShowSettingsDialog(true);
      toast.info("The subscription process was canceled.");
      window.history.replaceState(null, "", window.location.pathname);
    }
  }, [setShowSettingsDialog]);

  return (
    <>
      <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
          {/* DEFINITIVE FIX: Replace the old div with a theme-aware Alert component. */}
          {isWebview && (
            <Alert className="mb-2 rounded-t-xl rounded-b-none backdrop-blur-xl backdrop-saturate-150">
    72→              <AlertTriangle className="h-5 w-5 text-yellow-500" />
    73→              <AlertTitle className="font-semibold text-yellow-700 dark:text-yellow-400">
    74→                Login Tip
    75→              </AlertTitle>
    76→              <AlertDescription className="text-yellow-600 dark:text-yellow-500/80">
    77→                For a reliable sign-in experience, please use your phone&apos;s
    78→                main browser (e.g., Chrome or Safari).
    79→              </AlertDescription>
    80→            </Alert>
    81→       )}
          <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/60 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
            {/* Logo and Title */}
            <LogoWithText className="flex-1" />

            {/* Desktop Actions */}
            <div className="hidden md:flex items-center gap-1.5 lg:gap-2 flex-shrink-0">
              {!isLoginPage && (
                <>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      console.log(
                        `💬 [Header] Opening conversations dialog. Current page: ${currentPageId}`
                      );
                      setShowPagesDialog(true);
                    }}
                    className="h-9 w-9 lg:h-10 lg:w-10 rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105"
                    title="View Conversations"
                  >
                    <MessageSquare className="h-4 w-4 lg:h-5 lg:w-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={onNewChat}
                    className="h-9 w-9 lg:h-10 lg:w-10 rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105"
                    title="New Chat"
                  >
                    <Plus className="h-4 w-4 lg:h-5 lg:w-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowSettingsDialog(true)}
                    className="h-9 w-9 lg:h-10 lg:w-10 rounded-xl hover:bg-blue-500/10 hover:text-blue-500 transition-all duration-200 hover:scale-105"
                    title="Settings"
                  >
                    <Settings className="h-4 w-4 lg:h-5 lg:w-5" />
                  </Button>
                  <SignedIn>
                    {subscription && (
                      <SubscriptionBadge subscription={subscription} />
                    )}
                  </SignedIn>
                  <div className="h-6 w-px bg-border/50 mx-1" />
                </>
              )}
              {/* This div is the key to fixing the layout */}
              <div className="flex items-center gap-1.5 lg:gap-2">
                <ThemeToggle />
                <SignedIn>
                  <div className="ml-2">
                    <UserButton />
                  </div>
                </SignedIn>
                <SignedOut>
                  {pathname === "/" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 px-3 lg:h-9 lg:px-4 rounded-lg lg:rounded-xl hover:bg-white/10"
                      onClick={() => setShowPricingDialog(true)}
                    >
                      Pricing
                    </Button>
                  )}
                  <SignInButton mode="modal">
                    <Button
                      size="sm"
                      className="h-8 px-3 lg:h-9 lg:px-4 rounded-lg lg:rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200 hover:scale-105"
                    >
                      Sign In
                    </Button>
                  </SignInButton>
                </SignedOut>
              </div>
            </div>

            {/* Mobile Actions */}
            <div className="flex md:hidden items-center space-x-1.5 sm:space-x-2">
              <SignedIn>
                {subscription && (
                  <SubscriptionBadge subscription={subscription} />
                )}
                <UserButton />
              </SignedIn>
              <SignedOut>
                <div className="flex items-center gap-1.5">
                  {pathname === "/" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 px-3 sm:h-9 sm:px-4 rounded-lg sm:rounded-xl hover:bg-white/10"
                      onClick={() => setShowPricingDialog(true)}
                    >
                      Pricing
                    </Button>
                  )}
                  <SignInButton mode="modal">
                    <Button
                      size="sm"
                      className="h-8 px-3 sm:h-9 sm:px-4 rounded-lg sm:rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200 hover:scale-105"
                    >
                      Sign In
                    </Button>
                  </SignInButton>
                </div>
              </SignedOut>
              {!isLoginPage && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowMobileMenu(!showMobileMenu)}
                  className="h-8 w-8 sm:h-9 sm:w-9 rounded-lg sm:rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105"
                >
                  {showMobileMenu ? (
                    <X className="h-4 w-4 sm:h-5 sm:w-5" />
                  ) : (
                    <Menu className="h-4 w-4 sm:h-5 sm:w-5" />
                  )}
                </Button>
              )}
              {isLoginPage && (
                <div className="flex-shrink-0">
                  <ThemeToggle />
                </div>
              )}
            </div>
          </header>

          {/* Mobile Menu */}
          {isMounted && showMobileMenu && !isLoginPage && (
            <div className="md:hidden mt-2 bg-background/70 backdrop-blur-xl border border-white/8 rounded-xl sm:rounded-2xl shadow-2xl overflow-hidden">
              <div className="p-3 sm:p-4 space-y-2 sm:space-y-3">
                <Button
                  variant="ghost"
                  onClick={() => {
                    console.log(
                      `💬 [Header Mobile] Opening conversations dialog. Current page: ${currentPageId}`
                    );
                    setShowPagesDialog(true);
                    setShowMobileMenu(false);
                  }}
                  className="w-full justify-start h-11 sm:h-12 rounded-lg sm:rounded-xl hover:bg-white/10 transition-all duration-200"
                >
                  <MessageSquare className="h-4 w-4 sm:h-5 sm:w-5 mr-3" />
                  <span className="text-sm sm:text-base">
                    View Conversations
                  </span>
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    onNewChat();
                    setShowMobileMenu(false);
                  }}
                  className="w-full justify-start h-11 sm:h-12 rounded-lg sm:rounded-xl hover:bg-white/10 transition-all duration-200"
                >
                  <Plus className="h-4 w-4 sm:h-5 sm:w-5 mr-3" />
                  <span className="text-sm sm:text-base">New Chat</span>
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setShowSettingsDialog(true);
                    setShowMobileMenu(false);
                  }}
                  className="w-full justify-start h-11 sm:h-12 rounded-lg sm:rounded-xl hover:bg-blue-500/10 hover:text-blue-500 transition-all duration-200"
                >
                  <Settings className="h-4 w-4 sm:h-5 sm:w-5 mr-3" />
                  <span className="text-sm sm:text-base">Settings</span>
                </Button>
                <div className="flex items-center justify-between pt-2 border-t border-white/10">
                  <span className="text-sm text-muted-foreground">Theme</span>
                  <ThemeToggle />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Close mobile menu when clicking outside */}
      {isMounted && showMobileMenu && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          onClick={() => setShowMobileMenu(false)}
        />
      )}
      <PricingDialog
        isOpen={showPricingDialog}
        onClose={() => setShowPricingDialog(false)}
      />
      {isMounted && (
        <>
          <ConversationDialog
            isOpen={showPagesDialog}
            onClose={() => setShowPagesDialog(false)}
            onSelectPage={(pageId: string) => {
              console.log(`🎯 [Header] onSelectPage called with ID: ${pageId}`);
              onSelectPage(pageId);
            }}
            currentPageId={currentPageId}
          />

          <SettingsDialog
            open={showSettingsDialog}
            onOpenChange={setShowSettingsDialog}
            onClearChat={onClearChat}
          />
        </>
      )}
    </>
  );
}

// We need to re-create a simplified ChatSearch or placeholder
// For now, let's keep it simple. We can build it out later.
// import { Search } from "lucide-react"
// import { Input } from "./ui/input"
// export const ChatSearch = () => (
//   <div className="relative">
//     <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
//     <Input placeholder="Search chat..." className="pl-9 w-48" />
//   </div>
// )
