"use client"

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { v4 as uuidv4 } from "uuid";
import { toast } from "@/lib/toast";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface Message {
  id: string;
  content: string | object;
  isUser: boolean;
}

export const useWebSocket = (currentPageId?: string) => {
  const { getToken, isLoaded } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const isConnecting = useRef(false);
  const currentPageIdRef = useRef(currentPageId);

  // Update the ref when currentPageId changes
  useEffect(() => {
    currentPageIdRef.current = currentPageId;
  }, [currentPageId]);

  const fetchMessagesForPage = useCallback(async (pageId?: string) => {
    const token = await getToken();
    if (!token) return [];

    try {
      const url = pageId 
        ? `/api/messages?page_id=${pageId}` 
        : "/api/messages";
      
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (!response.ok) throw new Error("Failed to fetch messages");
      
      const history = await response.json();
      return history.map((msg: { id: string; content: string; is_user_message: boolean }) => ({
        id: msg.id,
        content: msg.content,
        isUser: msg.is_user_message,
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(errorMessage);
      return [];
    }
  }, [getToken]);

  const connect = useCallback(async () => {
    if (isConnecting.current || (socketRef.current && socketRef.current.readyState === WebSocket.OPEN)) {
      return;
    }
    isConnecting.current = true;

    const token = await getToken();
    if (!token) {
      setIsHistoryLoading(false);
      isConnecting.current = false;
      return;
    }

    // Fetch history first
    setIsHistoryLoading(true);
    const history = await fetchMessagesForPage(currentPageIdRef.current);
    setMessages(history);
    setIsHistoryLoading(false);

    // Then connect to WebSocket
    const wsUrl = `${WS_URL}/api/ws/orchestrator?token=${token}`;
    const newSocket = new WebSocket(wsUrl);
    socketRef.current = newSocket;

    newSocket.onopen = () => {
      setIsConnected(true);
      isConnecting.current = false;
      console.log("WebSocket connection established");
    };

    newSocket.onmessage = (event) => {
      let parsedContent;
      try {
        parsedContent = JSON.parse(event.data);
      } catch {
        parsedContent = event.data;
      }
      setMessages((prev) => [
        ...prev,
        { id: uuidv4(), content: parsedContent, isUser: false },
      ]);
      setIsLoading(false);
    };

    newSocket.onclose = () => {
      setIsConnected(false);
      isConnecting.current = false;
    };
    newSocket.onerror = () => {
      setError("WebSocket connection failed.");
      isConnecting.current = false;
    };
  }, [getToken, fetchMessagesForPage]);

  // Effect to handle page changes
  useEffect(() => {
    if (isLoaded && currentPageId !== undefined) {
      console.log(`Loading messages for page: ${currentPageId || 'new conversation'}`);
      const loadPageMessages = async () => {
        setIsHistoryLoading(true);
        const history = await fetchMessagesForPage(currentPageId);
        console.log(`Loaded ${history.length} messages for page: ${currentPageId || 'new conversation'}`);
        setMessages(history);
        setIsHistoryLoading(false);
        
        // Notify WebSocket about page change to sync context
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(JSON.stringify({ 
            type: 'switch_page', 
            page_id: currentPageId 
          }));
          console.log(`Notified WebSocket about page switch: ${currentPageId || 'new conversation'}`);
        }
      };
      loadPageMessages();
    }
  }, [currentPageId, isLoaded, fetchMessagesForPage]);

  useEffect(() => {
    if (isLoaded) {
      connect();
    }
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [isLoaded, connect]);

  const sendMessage = useCallback(async (content: string) => {
    let pageId = currentPageIdRef.current;
    
    console.log(`📤 [WebSocket] sendMessage called with content: "${content}"`);
    console.log(`📤 [WebSocket] Current pageId: ${pageId}`);
    console.log(`📤 [WebSocket] Current messages count: ${messages.length}`);
    
    // Create a new page if this is the first message and no page is selected
    if (messages.length === 0 && !pageId) {
      console.log(`📄 [WebSocket] Creating new page for first message`);
      const token = await getToken();
      if (!token) {
        setError("Authentication token not found.");
        return;
      }
      try {
        const response = await fetch('/api/pages', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ first_message: content }),
        });
        
        if (response.ok) {
          const newPage = await response.json();
          pageId = newPage.id;
          currentPageIdRef.current = pageId;
          console.log(`📄 [WebSocket] Created new page: ${pageId}`);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error";
        setError(errorMessage);
      }
    } else if (pageId) {
      console.log(`📄 [WebSocket] Using existing page: ${pageId}`);
    } else {
      console.log(`⚠️ [WebSocket] No page ID and messages exist - this shouldn't happen!`);
    }

    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      await connect(); // Reconnect if needed
    }

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      try {
        // Send message with page context
        const messageData = {
          content,
          page_id: pageId
        };
        
        console.log(`📤 [WebSocket] Sending message data:`, messageData);
        socketRef.current.send(JSON.stringify(messageData));
        setMessages((prev) => [
          ...prev,
          { id: uuidv4(), content, isUser: true },
        ]);
        setIsLoading(true);
      } catch {
        setError("Failed to send message.");
        setIsLoading(false);
      }
    } else {
      setError("Failed to connect to WebSocket.");
    }
  }, [connect, messages, getToken]);

  const deleteMessage = useCallback(async (id: string) => {
    const messageIndex = messages.findIndex((msg) => msg.id === id);
    if (messageIndex === -1) return;

    const originalMessages = [...messages];

    setMessages((prev) => prev.slice(0, messageIndex));

    const timeoutId = setTimeout(() => {
      const deletePromise = async () => {
        const token = await getToken();
        if (!token) {
          throw new Error("Authentication token not found.");
        }
        const response = await fetch(`/api/messages/${id}?cascade=true`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          throw new Error('Failed to delete message(s).');
        }
      };
      toast.promise(deletePromise(), {
        loading: 'Deleting messages...',
        success: 'Messages deleted.',
        error: (err: Error) => {
          setMessages(originalMessages); // Revert on error
          return err.message;
        },
      });
    }, 5000);

    toast("Message deleted", {
      action: {
        label: "Undo",
        onClick: () => {
          clearTimeout(timeoutId);
          setMessages(originalMessages);
        },
      },
    });
  }, [messages, getToken]);

  const editMessage = useCallback(async (id: string, newContent: string) => {
    const messageIndex = messages.findIndex((msg) => msg.id === id);
    if (messageIndex === -1) return;

    const originalMessages = [...messages];
    const updatedMessages = messages.slice(0, messageIndex);
    updatedMessages.push({ ...messages[messageIndex], content: newContent });
    setMessages(updatedMessages);

    toast("Fork conversation?", {
      description: "This will remove all subsequent messages and continue from here.",
      action: {
        label: "Confirm",
        onClick: async () => {
          const token = await getToken();
          if (!token) {
            setError("Authentication token not found.");
            setMessages(originalMessages);
            return;
          }

          try {
            await fetch(`/api/messages/${id}`, {
              method: 'PUT',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ content: newContent }),
            });

            await fetch(`/api/messages/${id}?cascade=true&above=true`, {
              method: 'DELETE',
              headers: { 'Authorization': `Bearer ${token}` },
            });

            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
              const messageData = {
                content: newContent,
                page_id: currentPageIdRef.current
              };
              socketRef.current.send(JSON.stringify(messageData));
              setIsLoading(true);
            }
          } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Unknown error";
            setError(errorMessage);
            setMessages(originalMessages);
          }
        },
      },
      onDismiss: () => setMessages(originalMessages),
    });
  }, [messages, getToken]);

  const regenerateMessage = useCallback(async (id: string) => {
    const messageIndex = messages.findIndex((msg) => msg.id === id);
    if (messageIndex === -1) return;

    // Find the last human message before the one being regenerated
    let lastHumanMessageIndex = -1;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].isUser) {
        lastHumanMessageIndex = i;
        break;
      }
    }
    
    if (lastHumanMessageIndex === -1) return;

    const messagesToRegenerate = messages.slice(0, lastHumanMessageIndex + 1);
    setMessages(messagesToRegenerate);

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const lastHumanMessage = messages[lastHumanMessageIndex];
      if(typeof lastHumanMessage.content === 'string') {
        const regenerateData = {
          type: 'regenerate',
          content: lastHumanMessage.content,
          page_id: currentPageIdRef.current
        };
        socketRef.current.send(JSON.stringify(regenerateData));
        setIsLoading(true);
      }
    }
  }, [messages]);

  const startNewChat = useCallback(async () => {
    // Clear frontend state immediately for better UX
    setMessages([]);
    currentPageIdRef.current = '';
    
    // Show immediate feedback for new conversation
    toast.success('New conversation started');
    
    // Clear WebSocket context and notify about page switch
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'clear_context' }));
      socketRef.current.send(JSON.stringify({ type: 'switch_page', page_id: '' }));
    }
    
    // NOTE: We DO NOT delete existing conversations when starting a new chat!
    // Users should be able to keep their conversation history and switch between them.
    // Only delete conversations when explicitly requested (e.g., "Clear all chats" button)
  }, []);

  const clearAllChats = useCallback(async () => {
    // Clear frontend state immediately for better UX
    setMessages([]);
    currentPageIdRef.current = '';
    
    // Clear WebSocket context
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'clear_context' }));
      socketRef.current.send(JSON.stringify({ type: 'switch_page', page_id: '' }));
    }
    
    // Delete ALL conversations from database (destructive operation)
    try {
      const token = await getToken();
      if (token) {
        const response = await fetch('/api/chats', {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!response.ok) {
          console.warn('Failed to delete chat history from database');
          toast.error('Failed to clear chat history');
        } else {
          toast.success('All conversations cleared');
        }
      }
    } catch (error) {
      console.warn('Error deleting chat history:', error);
      toast.error('Failed to clear chat history');
    }
  }, [getToken]);

  const stopGeneration = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'stop_generation' }));
      setIsLoading(false);
    }
  }, []);

  return {
    messages,
    sendMessage,
    deleteMessage,
    editMessage,
    regenerateMessage,
    startNewChat,
    clearAllChats,
    stopGeneration,
    isLoading,
    isHistoryLoading,
    error,
    isConnected,
  };
}; 