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
  // Start with empty state - will be populated by fetchMostRecentPage if needed
  const [currentPageId, setCurrentPageId] = React.useState<string>("");
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

  // Function to fetch the most recent conversation (only on initial load)
  const fetchMostRecentPage = React.useCallback(async () => {
    if (!isLoaded || hasInitialized) {
      return;
    }

    try {
      const token = await getToken();
      if (!token) {
        setIsLoadingRecentPage(false);
        setHasInitialized(true);
        return;
      }

      const cachedId = localStorage.getItem("lastConversationId");
      if (cachedId) {
        try {
          // FIX: The validation fetch call was incorrect. The Next.js proxy will
          // automatically forward this request to the backend.
          const validateResponse = await fetch(`/api/pages/${cachedId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });

          if (validateResponse.ok) {
            setCurrentPageId(cachedId);
            setIsLoadingRecentPage(false);
            setHasInitialized(true);
            return;
          } else {
            // If the cached ID is invalid, remove it from localStorage.
            localStorage.removeItem("lastConversationId");
          }
        } catch (error) {
          console.warn("Failed to validate cached conversation:", error);
          localStorage.removeItem("lastConversationId");
        }
      }

      // If no valid cached ID is found, fetch the most recent page.
      const response = await fetch("/api/pages/recent", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const recentPage = await response.json();
        if (recentPage && recentPage.id) {
          setCurrentPageId(recentPage.id);
          localStorage.setItem("lastConversationId", recentPage.id);
        }
      } else if (response.status !== 404) {
        console.warn(`Failed to fetch recent page, status: ${response.status}`);
      }
    } catch (error) {
      console.error("Failed to fetch most recent page:", error);
    } finally {
      setIsLoadingRecentPage(false);
      setHasInitialized(true);
    }
  }, [getToken, hasInitialized, isLoaded]);

  // Load the most recent conversation on page load (only once)
  React.useEffect(() => {
    if (isLoaded && user && !hasInitialized) {
      console.log(
        "📋 [page.tsx] useEffect triggered - calling fetchMostRecentPage"
      );
      fetchMostRecentPage();
    } else {
      console.log(
        "📋 [page.tsx] useEffect skipped - isLoaded:",
        isLoaded,
        "user:",
        !!user,
        "hasInitialized:",
        hasInitialized
      );
    }
  }, [isLoaded, user, hasInitialized]); // Removed fetchMostRecentPage from deps to prevent re-runs

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
          currentPageId={currentPageId}
          onSelectPage={handleSelectPage}
          isLoginPage={!isSignedIn}
        />
        <main className="flex-1 overflow-hidden pt-14 sm:pt-16 md:pt-20">
          <SignedIn>
            {isLoadingRecentPage || subscriptionLoading ? (
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
                onStopGeneration={stopGeneration}
                isLoading={isLoading}
                isHistoryLoading={isHistoryLoading}
                isConnected={isConnected}
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
