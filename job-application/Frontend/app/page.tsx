"use client"

import * as React from "react";
import { ChatContainer } from "@/components/chat/chat-container";
import { useWebSocket } from "@/lib/hooks/use-websocket";
import { Header } from "@/components/header";
import { SignedIn, SignedOut, useUser, useAuth } from "@clerk/nextjs";
import { LoginPrompt } from "@/components/login-prompt";

export default function Home() {
  const [currentPageId, setCurrentPageId] = React.useState<string>('');
  const [isLoadingRecentPage, setIsLoadingRecentPage] = React.useState(true);
  
  const { 
    messages, 
    sendMessage,
    deleteMessage,
    editMessage,
    regenerateMessage,
    startNewChat,
    stopGeneration,
    isLoading, 
    error, 
    isConnected,
    isHistoryLoading,
  } = useWebSocket(currentPageId);
  const { user } = useUser();
  const { getToken, isLoaded, isSignedIn } = useAuth();

  // Function to fetch the most recent conversation
  const fetchMostRecentPage = React.useCallback(async () => {
    if (!isLoaded) return;
    
    try {
      const token = await getToken();
      if (!token) return;

      const response = await fetch('/api/pages/recent', {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const recentPage = await response.json();
        setCurrentPageId(recentPage.id);
      } else if (response.status === 404) {
        // No conversations found, start with empty state
        setCurrentPageId('');
      }
    } catch (error) {
      console.warn('Failed to fetch most recent page:', error);
      setCurrentPageId('');
    } finally {
      setIsLoadingRecentPage(false);
    }
  }, [isLoaded, getToken]);

  // Load the most recent conversation on page load
  React.useEffect(() => {
    if (isLoaded && user) {
      fetchMostRecentPage();
    }
  }, [isLoaded, user, fetchMostRecentPage]);

  const handleSelectPage = (pageId: string) => {
    setCurrentPageId(pageId);
  };

  const handleNewChat = () => {
    setCurrentPageId('');
    setIsLoadingRecentPage(false);
    startNewChat();
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      <div className="flex flex-col flex-1">
        <Header 
          onNewChat={handleNewChat}
          onClearChat={startNewChat}
          currentPageId={currentPageId}
          onSelectPage={handleSelectPage}
          isLoginPage={!isSignedIn}
        />
        <main className="flex-1 overflow-hidden pt-14 sm:pt-16 md:pt-20">
          <SignedIn>
            <ChatContainer
              user={user}
              messages={messages}
              onSendMessage={sendMessage}
              onDeleteMessage={deleteMessage}
              onEditMessage={editMessage}
              onRegenerateMessage={regenerateMessage}
              onStopGeneration={stopGeneration}
              isLoading={isLoading}
              isHistoryLoading={isHistoryLoading || isLoadingRecentPage}
              isConnected={isConnected}
              error={error}
            />
          </SignedIn>
          <SignedOut>
            <LoginPrompt />
          </SignedOut>
        </main>
      </div>
    </div>
  );
}
