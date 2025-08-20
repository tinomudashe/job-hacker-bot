"use client";

import { ChatContainer } from "@/components/chat/chat-container";
import { Header } from "@/components/header";
import { LoginPrompt } from "@/components/login-prompt";
import { SubscriptionPrompt } from "@/components/subscription-prompt";
import { useSubscription } from "@/lib/hooks/use-subscription";
import { useWebSocket } from "@/lib/hooks/use-websocket";
import { SignedIn, SignedOut, useAuth, useUser } from "@clerk/nextjs";
import * as React from "react";
import { toast } from "sonner";

export default function Home() {
  // Start with undefined - will be populated on mount
  const [currentPageId, setCurrentPageId] = React.useState<string | undefined>(undefined);
  const [isLoadingRecentPage, setIsLoadingRecentPage] = React.useState(true);
  const [hasInitialized, setHasInitialized] = React.useState(false);

  const {
    messages,
    reasoningSteps,
    sendMessage,
    deleteMessage,
    editMessage,
    regenerateMessage,
    startNewChat,
    clearAllChats,
    stopGeneration,
    isLoading,
    error,
    isConnected,
    isHistoryLoading,
    isLimitReached,
  } = useWebSocket(currentPageId, setCurrentPageId);
  const { user } = useUser();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const {
    subscription,
    loading: subscriptionLoading,
    fetchSubscription,
  } = useSubscription();

  // NEW: Handle successful checkout redirect
  React.useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    if (query.get("checkout") === "success") {
      toast.success("Welcome to Pro!", {
        description: "Your subscription has been activated.",
      });
      // Force a re-fetch of the subscription status to unlock features
      fetchSubscription();
      // Clean the URL
      window.history.replaceState(null, "", window.location.pathname);
    }
  }, [fetchSubscription]);


  // Load the most recent conversation on page load (only once)
  React.useEffect(() => {
    const loadInitialPage = async () => {
      console.log("🔍 [loadInitialPage] Starting initial page load");
      
      if (!isLoaded || !user || hasInitialized) {
        console.log("🔍 [loadInitialPage] Skipping:", { isLoaded, user: !!user, hasInitialized });
        if (isLoaded && !user) {
          setIsLoadingRecentPage(false);
          setHasInitialized(true);
        }
        return;
      }

      setIsLoadingRecentPage(true);
      
      try {
        const token = await getToken();
        if (!token) {
          console.log("🔍 [loadInitialPage] No token");
          setCurrentPageId("");
          return;
        }

        // Check localStorage first
        const cachedId = localStorage.getItem("lastConversationId");
        console.log("🔍 [loadInitialPage] Cached ID:", cachedId);
        
        if (cachedId) {
          // Validate cached page exists
          const validateResponse = await fetch(`/api/pages/${cachedId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          
          if (validateResponse.ok) {
            console.log("✅ [loadInitialPage] Loading cached page:", cachedId);
            setCurrentPageId(cachedId);
            setIsLoadingRecentPage(false);
            setHasInitialized(true);
            return;
          }
          
          console.log("❌ [loadInitialPage] Cached page invalid");
          localStorage.removeItem("lastConversationId");
        }

        // No cache or invalid, get most recent
        console.log("🔍 [loadInitialPage] Fetching most recent page");
        const recentResponse = await fetch("/api/pages/recent", {
          headers: { Authorization: `Bearer ${token}` },
        });
        
        if (recentResponse.ok) {
          const recentPage = await recentResponse.json();
          console.log("✅ [loadInitialPage] Got recent page:", recentPage);
          if (recentPage?.id) {
            setCurrentPageId(recentPage.id);
            localStorage.setItem("lastConversationId", recentPage.id);
          } else {
            setCurrentPageId("");
          }
        } else {
          console.log("🔍 [loadInitialPage] No pages found, starting fresh");
          setCurrentPageId("");
        }
      } catch (error) {
        console.error("[loadInitialPage] Error:", error);
        setCurrentPageId("");
      } finally {
        setIsLoadingRecentPage(false);
        setHasInitialized(true);
      }
    };

    loadInitialPage();
  }, [isLoaded, user, hasInitialized, getToken]);

  const handleSelectPage = (pageId: string) => {
    console.log(`📋 [page.tsx] handleSelectPage called with ID: ${pageId}`);
    console.log(`📋 [page.tsx] Previous currentPageId: ${currentPageId}`);
    setCurrentPageId(pageId);
    setHasInitialized(true); // Prevent auto-fetching after manual selection
    setIsLoadingRecentPage(false);
    // Cache the selected conversation
    if (pageId) {
      localStorage.setItem("lastConversationId", pageId);
    } else {
      localStorage.removeItem("lastConversationId");
    }
    console.log(`📋 [page.tsx] Updated currentPageId to: ${pageId}`);
  };

  const handleNewChat = React.useCallback(() => {
    console.log("📋 [page.tsx] handleNewChat called - starting new chat");

    // Clear localStorage first to prevent any conflicts
    localStorage.removeItem("lastConversationId");
    console.log("📋 [page.tsx] Cleared localStorage");

    // Reset all local state in the correct order using functional updates to ensure they complete
    setHasInitialized(() => {
      console.log("📋 [page.tsx] Setting hasInitialized to true");
      return true;
    });

    setCurrentPageId(() => {
      console.log("📋 [page.tsx] Setting currentPageId to empty");
      return "";
    });

    setIsLoadingRecentPage(() => {
      console.log("📋 [page.tsx] Setting isLoadingRecentPage to false");
      return false;
    });

    // Use React.startTransition to ensure state updates are processed
    React.startTransition(() => {
      console.log("📋 [page.tsx] Calling startNewChat() in transition");
      startNewChat();
    });

    console.log("📋 [page.tsx] handleNewChat completed");
  }, [startNewChat]);

  return (
    <div className="flex flex-col h-screen bg-background">
      <div className="flex flex-col flex-1">
        <Header
          onNewChat={handleNewChat}
          onClearChat={clearAllChats}
          currentPageId={currentPageId || undefined}
          onSelectPage={handleSelectPage}
          isLoginPage={!isSignedIn}
        />
        <main className="flex-1 overflow-hidden pt-14 sm:pt-16 md:pt-20">
          <SignedIn>
            {(isLoadingRecentPage || subscriptionLoading) ? (
              <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  <p className="text-muted-foreground text-sm">
                    Loading your conversation...
                  </p>
                </div>
              </div>
            ) : subscription?.status === "active" ||
              subscription?.status === "trialing" ? (
              <ChatContainer
                user={user}
                messages={messages}
                reasoningSteps={reasoningSteps}
                onSendMessage={sendMessage}
                onDeleteMessage={deleteMessage}
                onEditMessage={editMessage}
                onRegenerateMessage={regenerateMessage}
                onStartNewChat={startNewChat}
                onStopGeneration={stopGeneration}
                isLoading={isLoading}
                isHistoryLoading={isHistoryLoading}
                isConnected={isConnected}
                isLimitReached={isLimitReached}
                error={error || undefined}
              />
            ) : (
              <SubscriptionPrompt />
            )}
          </SignedIn>
          <SignedOut>
            <LoginPrompt />
          </SignedOut>
        </main>
      </div>
    </div>
  );
}
