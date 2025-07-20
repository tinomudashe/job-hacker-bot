"use client";

import { ChatContainer } from "@/components/chat/chat-container";
import { Header } from "@/components/header";
import { LoginPrompt } from "@/components/login-prompt";
import { SubscriptionPrompt } from "@/components/subscription-prompt";
import { SignedIn, SignedOut, useAuth, useUser } from "@clerk/nextjs";
import * as React from "react";
import { useSubscription } from "../lib/hooks/use-subscription";
import { useWebSocket } from "../lib/hooks/use-websocket";

export default function Home() {
  // Start with empty state - will be populated by fetchMostRecentPage if needed
  const [currentPageId, setCurrentPageId] = React.useState<string>("");
  const [isLoadingRecentPage, setIsLoadingRecentPage] = React.useState(true);
  const [hasInitialized, setHasInitialized] = React.useState(false);

  const {
    messages,
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
  } = useWebSocket(currentPageId);
  const { user } = useUser();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { subscription, loading: subscriptionLoading } = useSubscription();

  // Function to fetch the most recent conversation (only on initial load)
  const fetchMostRecentPage = React.useCallback(async () => {
    console.log(
      "📋 [page.tsx] fetchMostRecentPage called - isLoaded:",
      isLoaded,
      "hasInitialized:",
      hasInitialized
    );
    if (!isLoaded || hasInitialized) {
      console.log("📋 [page.tsx] fetchMostRecentPage SKIPPED");
      return;
    }
    console.log(
      "📋 [page.tsx] fetchMostRecentPage RUNNING - will fetch recent conversation..."
    );

    try {
      const token = await getToken();
      if (!token) return;

      // If we have a cached ID, validate it first
      const cachedId = localStorage.getItem("lastConversationId");
      if (cachedId) {
        try {
          const validateResponse = await fetch(`/api/pages/${cachedId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (validateResponse.ok) {
            // Cached conversation is valid, keep it
            setCurrentPageId(cachedId);
            setIsLoadingRecentPage(false);
            setHasInitialized(true);
            return;
          } else {
            // Cached conversation is invalid, clear it and fetch recent
            localStorage.removeItem("lastConversationId");
          }
        } catch (error) {
          console.warn("Failed to validate cached conversation:", error);
          localStorage.removeItem("lastConversationId");
        }
      }

      // Fetch the most recent conversation
      const response = await fetch("/api/pages/recent", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const recentPage = await response.json();
        setCurrentPageId(recentPage.id);
        // Cache the conversation ID for future page loads
        localStorage.setItem("lastConversationId", recentPage.id);
      } else if (response.status === 404) {
        // No conversations found, start with empty state
        setCurrentPageId("");
        localStorage.removeItem("lastConversationId");
      }
    } catch (error) {
      console.warn("Failed to fetch most recent page:", error);
      setCurrentPageId("");
      localStorage.removeItem("lastConversationId");
    } finally {
      setIsLoadingRecentPage(false);
      setHasInitialized(true);
    }
  }, [isLoaded, getToken, hasInitialized]);

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
