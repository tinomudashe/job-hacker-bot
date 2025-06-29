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

    // Connect to WebSocket (history is handled by page change effect)
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
      
      console.log(`📨 [WebSocket] Received response - Content preview: "${typeof parsedContent === 'string' ? parsedContent.substring(0, 50) : JSON.stringify(parsedContent).substring(0, 50)}..."`);
      
      setMessages((prev) => {
        console.log(`📨 [WebSocket] BEFORE adding AI response: ${prev.length} messages`);
        
        // 2025 DUPLICATE PREVENTION: Check if this exact message already exists
        const contentString = typeof parsedContent === 'string' ? parsedContent : JSON.stringify(parsedContent);
        const isDuplicate = prev.some(msg => 
          !msg.isUser && 
          (typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)) === contentString
        );
        
        if (isDuplicate) {
          console.log(`🚫 [WebSocket] DUPLICATE DETECTED - Message already exists, skipping`);
          return prev; // Return existing messages without modification
        }
        
        const newMessages = [
          ...prev,
          { id: uuidv4(), content: parsedContent, isUser: false },
        ];
        console.log(`📨 [WebSocket] AFTER adding AI response: ${newMessages.length} messages`);
        console.log(`📨 [WebSocket] Last 3 messages:`, newMessages.slice(-3).map(m => ({
          isUser: m.isUser,
          preview: typeof m.content === 'string' ? m.content.substring(0, 30) : 'Object'
        })));
        return newMessages;
      });
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
  }, [getToken]);

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
    try {
      let pageId = currentPageIdRef.current;
      
      console.log(`📤 [WebSocket] sendMessage called with content: "${content}"`);
      console.log(`📤 [WebSocket] Current pageId: ${pageId}`);
      console.log(`📤 [WebSocket] Current messages count: ${messages.length}`);
      
      // REVERTED: Simple page creation logic that was working
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
          } else {
            const errorData = await response.text();
            throw new Error(`Failed to create page: ${response.status} - ${errorData}`);
          }
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : "Failed to create page";
          console.error("Page creation error:", err);
          setError(errorMessage);
          return;
        }
      } else if (pageId) {
        console.log(`📄 [WebSocket] Using existing page: ${pageId}`);
      } else {
        console.log(`⚠️ [WebSocket] No page ID and messages exist - this shouldn't happen!`);
      }

      // REVERTED: Simple WebSocket connection check
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        await connect(); // Reconnect if needed
      }

      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        // Send message with page context
        const messageData = {
          content,
          page_id: pageId
        };
        
        console.log(`📤 [WebSocket] Sending message data:`, messageData);
        socketRef.current.send(JSON.stringify(messageData));
        
        // Add user message to UI immediately
        setMessages((prev) => {
          console.log(`📤 [WebSocket] Adding user message to UI. Previous count: ${prev.length}`);
          const newMessages = [
            ...prev,
            { id: uuidv4(), content, isUser: true },
          ];
          console.log(`📤 [WebSocket] New message count: ${newMessages.length}`);
          return newMessages;
        });
        setIsLoading(true);
        setError(null);
      } else {
        setError("Failed to connect to WebSocket.");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to send message";
      console.error("Send message error:", err);
      setError(errorMessage);
      setIsLoading(false);
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
    if (messageIndex === -1) {
      console.warn(`Message with id ${id} not found for editing`);
      toast.error("Message not found");
      return;
    }

    const originalMessages = [...messages];
    const messagesToKeep = messages.slice(0, messageIndex);
    const editedMessage = { ...messages[messageIndex], content: newContent };
    const subsequentCount = originalMessages.length - messageIndex - 1;
    
    // Show preview immediately
    const previewMessages = [...messagesToKeep, editedMessage];
    setMessages(previewMessages);

    // REVERTED: Proper toast with confirmation and error handling
    const editPromise = async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not available");
      }

      console.log(`✏️ Editing message ${id} with new content: "${newContent.substring(0, 50)}..."`);

      // Update message in database
      const updateResponse = await fetch(`/api/messages/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: newContent }),
      });
      
      if (!updateResponse.ok) {
        const errorData = await updateResponse.text();
        throw new Error(`Failed to update message: ${updateResponse.status} - ${errorData}`);
      }

      // Delete subsequent messages if any exist
      if (subsequentCount > 0) {
        const deleteResponse = await fetch(`/api/messages/${id}?cascade=true&above=true`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        });
        
        if (!deleteResponse.ok) {
          const errorData = await deleteResponse.text();
          throw new Error(`Failed to delete subsequent messages: ${deleteResponse.status} - ${errorData}`);
        }
        console.log(`🗑️ Deleted ${subsequentCount} subsequent messages`);
      }

      // Enhanced WebSocket handling for continuing conversation
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        const messageData = {
          content: newContent,
          page_id: currentPageIdRef.current
        };
        
        console.log(`📤 [EDIT] Sending edited message to continue conversation:`, messageData);
        socketRef.current.send(JSON.stringify(messageData));
        setIsLoading(true);
        setError(null);
      } else {
        console.warn("⚠️ WebSocket not connected, cannot continue conversation");
        throw new Error("Connection lost - message edited but conversation cannot continue automatically");
      }
      
      console.log(`✅ Successfully edited message ${id}`);
      return `Message edited successfully${subsequentCount > 0 ? ` (${subsequentCount} subsequent messages removed)` : ''}`;
    };

    toast.promise(editPromise(), {
      loading: 'Saving changes...',
      success: (data) => data,
      error: (err) => {
        console.error("Error editing message:", err);
        setMessages(originalMessages); // Revert on error
        return `Edit failed: ${err.message}`;
      },
    });
  }, [messages, getToken]);

  const regenerateMessage = useCallback(async (id: string) => {
    const messageIndex = messages.findIndex((msg) => msg.id === id);
    if (messageIndex === -1) {
      console.warn(`🔄 [Frontend] Message with id ${id} not found for regeneration`);
      return;
    }

    console.log(`🔄 [Frontend] Regenerate requested for message ID: ${id}`);
    console.log(`🔄 [Frontend] Message index: ${messageIndex}`);
    console.log(`🔄 [Frontend] Total messages: ${messages.length}`);
    console.log(`🔄 [Frontend] Current page ID: ${currentPageIdRef.current}`);

    // Find the last human message before the one being regenerated
    let lastHumanMessageIndex = -1;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].isUser) {
        lastHumanMessageIndex = i;
        break;
      }
    }
    
    if (lastHumanMessageIndex === -1) {
      console.warn(`🔄 [Frontend] No human message found before index ${messageIndex}`);
      return;
    }

    console.log(`🔄 [Frontend] Last human message index: ${lastHumanMessageIndex}`);
    
    const messagesToRegenerate = messages.slice(0, lastHumanMessageIndex + 1);
    console.log(`🔄 [Frontend] Keeping ${messagesToRegenerate.length} messages, removing ${messages.length - messagesToRegenerate.length} messages`);
    
    // CRITICAL: Set messages immediately and log the exact state
    setMessages((prev) => {
      console.log(`🔄 [Frontend] BEFORE regeneration: ${prev.length} messages`);
      console.log(`🔄 [Frontend] SETTING TO: ${messagesToRegenerate.length} messages`);
      return messagesToRegenerate;
    });

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const lastHumanMessage = messages[lastHumanMessageIndex];
      if(typeof lastHumanMessage.content === 'string') {
        const regenerateData = {
          type: 'regenerate',
          content: lastHumanMessage.content,
          page_id: currentPageIdRef.current
        };
        console.log(`🔄 [Frontend] Sending regenerate data:`, regenerateData);
        socketRef.current.send(JSON.stringify(regenerateData));
        setIsLoading(true);
      } else {
        console.warn(`🔄 [Frontend] Last human message content is not a string:`, lastHumanMessage.content);
      }
    } else {
      console.error(`🔄 [Frontend] WebSocket not connected when trying to regenerate`);
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