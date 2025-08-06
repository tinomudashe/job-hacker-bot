"use client";

import { toast } from "@/lib/toast";
import { useAuth } from "@clerk/nextjs";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

const WS_URL = process.env.NEXT_PUBLIC_API_URL || "ws://localhost:8000";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  createdAt?: string; // Optional: Backend provides created_at, useful for display/ordering
}

interface WebSocketMessage {
  type: string;
  message?: string;
  page_id?: string;
  title?: string;
}

export const useWebSocket = (
  currentPageId?: string,
  setCurrentPageId?: (pageId: string) => void
) => {
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

  const fetchMessagesForPage = useCallback(
    async (pageId?: string) => {
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
        return history.map(
          (msg: {
            id: string;
            content: string;
            is_user_message: boolean;
            created_at: string;
          }) => ({
            id: msg.id,
            content: msg.content,
            isUser: msg.is_user_message,
            createdAt: msg.created_at,
          })
        );
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error";
        setError(errorMessage);
        return [];
      }
    },
    [getToken]
  );

  const connect = useCallback(async () => {
    if (
      isConnecting.current ||
      (socketRef.current && socketRef.current.readyState === WebSocket.OPEN)
    ) {
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
      // Immediately send switch_page for initial context sync
      if (currentPageIdRef.current) {
        newSocket.send(
          JSON.stringify({
            type: "switch_page",
            page_id: currentPageIdRef.current,
          })
        );
        console.log(
          `Initial WebSocket page switch notification: ${currentPageIdRef.current}`
        );
      }
    };

    newSocket.onmessage = (event) => {
      // Frontend expects JSON, backend sends JSON
      let parsedData: WebSocketMessage;
      try {
        parsedData = JSON.parse(event.data);
      } catch (e) {
        console.error(
          "Failed to parse WebSocket message as JSON:",
          event.data,
          e
        );
        // If it's not JSON, treat it as a plain text message for display
        parsedData = { type: "message", message: event.data };
      }

      // Handle different message types from backend
      if (parsedData.type === "message") {
        const aiMessageContent = parsedData.message || "";

        setMessages((prev) => {
          console.log(
            `📨 [WebSocket] BEFORE adding AI response: ${prev.length} messages`
          );

          // Simplified DUPLICATE PREVENTION: Check if the last AI message is identical
          // This is a basic check; backend should ideally prevent sending exact duplicates for sequential messages
          const lastMessage = prev[prev.length - 1];
          const isDuplicate =
            lastMessage &&
            !lastMessage.isUser &&
            lastMessage.content === aiMessageContent;

          if (isDuplicate) {
            console.log(
              `🚫 [WebSocket] DUPLICATE DETECTED - Last AI message identical, skipping`
            );
            return prev; // Return existing messages without modification
          }

          const newMessages = [
            ...prev,
            { id: uuidv4(), content: aiMessageContent, isUser: false },
          ];
          console.log(
            `📨 [WebSocket] AFTER adding AI response: ${newMessages.length} messages`
          );
          return newMessages;
        });
        setIsLoading(false);
      } else if (parsedData.type === "info") {
        // Handle info messages (e.g., "Loading...", "Searching...")
        // You might want to display these as temporary status updates rather than full messages
        console.log(`ℹ️ [WebSocket Info]: ${parsedData.message}`);
        // Potentially update a loading indicator or a temporary status message
        // For now, we'll just log it and not add to chat history directly
        // If you want to show it, you'd add it to messages with a special type/styling
      } else if (parsedData.type === "error") {
        console.error(`❌ [WebSocket Error]: ${parsedData.message}`);
        toast.error(parsedData.message || "Unknown error");
        setIsLoading(false);
      } else if (parsedData.type === "page_created") {
        // NEW: Handle page creation
        const { page_id } = parsedData;
           // Ensure page_id is a string before using it.
        if (page_id) {
          console.log(`📄 Page created by WebSocket: ${page_id}`);
          if (setCurrentPageId) {
            setCurrentPageId(page_id);
          }
          currentPageIdRef.current = page_id;
        }
      } else {
        console.warn(
          `⁉️ [WebSocket] Unknown message type: ${parsedData.type}`,
          parsedData
        );
        // Default to adding as a regular AI message if type is unknown but has a message field
        if (parsedData.message) {
          setMessages((prev) => [
            ...prev,
            { id: uuidv4(), content: parsedData.message || "", isUser: false },
          ]);
          setIsLoading(false);
        }
      }
    };

    newSocket.onclose = () => {
      setIsConnected(false);
      isConnecting.current = false;
      console.log("WebSocket connection closed");
    };
    newSocket.onerror = (error) => {
      setError(
        "WebSocket connection failed: " +
          (error instanceof Event ? error.type : String(error))
      );
      isConnecting.current = false;
      console.error("WebSocket connection error:", error);
    };
  }, [getToken, currentPageIdRef]);

  // Effect to handle page changes
  useEffect(() => {
    if (isLoaded && currentPageId !== undefined) {
      console.log(
        `[WebSocket Hook] Page changed. Loading messages for page: ${
          currentPageId || "new conversation"
        }`
      );
      const loadPageMessages = async () => {
        setIsHistoryLoading(true);
        console.log(
          `[WebSocket Hook] Fetching history for page: ${currentPageId}`
        );
        const history = await fetchMessagesForPage(currentPageId);
        console.log(
          `[WebSocket Hook] Loaded ${history.length} messages for page: ${
            currentPageId || "new conversation"
          }`
        );
        console.log("[WebSocket Hook] History received from API:", history); // Log raw history
        setMessages(history);
        setIsHistoryLoading(false);

        // Notify WebSocket about page change to sync context
        if (
          socketRef.current &&
          socketRef.current.readyState === WebSocket.OPEN
        ) {
          socketRef.current.send(
            JSON.stringify({
              type: "switch_page",
              page_id: currentPageId,
            })
          );
          console.log(
            `[WebSocket Hook] Notified WebSocket about page switch: ${
              currentPageId || "new conversation"
            }`
          );
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

  const sendMessage = useCallback(
    async (content: string) => {
      try {
        let pageId = currentPageIdRef.current;

        console.log(
          `📤 [WebSocket] sendMessage called with content: "${content}"`
        );
        console.log(`📤 [WebSocket] Current pageId: ${pageId}`);
        console.log(
          `📤 [WebSocket] Current messages count: ${messages.length}`
        );

        // REVERTED: Simple page creation logic that was working
        if (messages.length === 0 && !pageId) {
          console.log(`📄 [WebSocket] Creating new page for first message`);
          const token = await getToken();
          if (!token) {
            setError("Authentication token not found.");
            return;
          }

          try {
            const response = await fetch("/api/pages", {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ first_message: content }),
            });

            if (response.ok) {
              const newPage = await response.json();
              pageId = newPage.id;
              // Immediately update currentPageIdRef so subsequent messages use it
              currentPageIdRef.current = pageId;
              // Also update outer state if useWebSocket is used by a component that reads currentPageId from its state
              // This might need a direct setter passed from the component or a ref sync mechanism
              // For now, rely on currentPageIdRef and the effect to trigger a history load
              if (setCurrentPageId) {
                setCurrentPageId(pageId || "");
              }
              console.log(`📄 [WebSocket] New page created with ID: ${pageId}`);
            } else {
              throw new Error("Failed to create new page");
            }
          } catch (createPageError) {
            console.error("Error creating new page:", createPageError);
            setError(
              `Failed to start new conversation: ${
                createPageError instanceof Error
                  ? createPageError.message
                  : "Unknown error"
              }`
            );
            return; // Stop execution if page creation fails
          }
        }

        // Optimistically add user message to state
        const newUserMessage: Message = {
          id: uuidv4(),
          content: content,
          isUser: true,
          createdAt: new Date().toISOString(), // Add creation timestamp
        };
        setMessages((prev) => [...prev, newUserMessage]);
        setIsLoading(true); // Indicate loading for AI response

        // Send message to WebSocket
        if (
          socketRef.current &&
          socketRef.current.readyState === WebSocket.OPEN
        ) {
          const messagePayload = {
            type: "message",
            content: content,
            page_id: pageId, // Ensure pageId is always sent
          };
          socketRef.current.send(JSON.stringify(messagePayload));
          console.log(
            `📤 [WebSocket] Sent message with page_id: ${pageId || "(new)"}`
          );
        } else {
          setError("WebSocket is not connected. Please refresh the page.");
          setIsLoading(false);
        }
      } catch (err) {
        console.error("Error in sendMessage:", err);
        setError(
          "Failed to send message: " +
            (err instanceof Error ? err.message : String(err))
        );
        setIsLoading(false);
      }
    },
    [messages, getToken]
  );

  const deleteMessage = useCallback(
    async (id: string) => {
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
            method: "DELETE",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          if (!response.ok) {
            throw new Error("Failed to delete message(s).");
          }
        };
        toast.promise(deletePromise(), {
          loading: "Deleting messages...",
          success: "Messages deleted.",
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
    },
    [messages, getToken]
  );

  const editMessage = useCallback(
    async (id: string, newContent: string) => {
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

        console.log(
          `✏️ Editing message ${id} with new content: "${newContent.substring(
            0,
            50
          )}..."`
        );

        // Update message in database
        const updateResponse = await fetch(`/api/messages/${id}`, {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ content: newContent }),
        });

        if (!updateResponse.ok) {
          const errorData = await updateResponse.text();
          throw new Error(
            `Failed to update message: ${updateResponse.status} - ${errorData}`
          );
        }

        // Delete subsequent messages if any exist
        if (subsequentCount > 0) {
          const deleteResponse = await fetch(
            `/api/messages/${id}?cascade=true&above=true`,
            {
              method: "DELETE",
              headers: { Authorization: `Bearer ${token}` },
            }
          );

          if (!deleteResponse.ok) {
            const errorData = await deleteResponse.text();
            throw new Error(
              `Failed to delete subsequent messages: ${deleteResponse.status} - ${errorData}`
            );
          }
          console.log(`🗑️ Deleted ${subsequentCount} subsequent messages`);
        }

        // Enhanced WebSocket handling for continuing conversation
        if (
          socketRef.current &&
          socketRef.current.readyState === WebSocket.OPEN
        ) {
          const messageData = {
            content: newContent,
            page_id: currentPageIdRef.current,
          };

          console.log(
            `📤 [EDIT] Sending edited message to continue conversation:`,
            messageData
          );
          socketRef.current.send(JSON.stringify(messageData));
          setIsLoading(true);
          setError(null);
        } else {
          console.warn(
            "⚠️ WebSocket not connected, cannot continue conversation"
          );
          throw new Error(
            "Connection lost - message edited but conversation cannot continue automatically"
          );
        }

        console.log(`✅ Successfully edited message ${id}`);
        return `Message edited successfully${
          subsequentCount > 0
            ? ` (${subsequentCount} subsequent messages removed)`
            : ""
        }`;
      };

      toast.promise(editPromise(), {
        loading: "Saving changes...",
        success: (data) => data,
        error: (err) => {
          console.error("Error editing message:", err);
          setMessages(originalMessages); // Revert on error
          return `Edit failed: ${err.message}`;
        },
      });
    },
    [messages, getToken]
  );

  const regenerateMessage = useCallback(
    async (id: string) => {
      const messageIndex = messages.findIndex((msg) => msg.id === id);
      if (messageIndex === -1) {
        console.warn(
          `🔄 [Frontend] Message with id ${id} not found for regeneration`
        );
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
        console.warn(
          `🔄 [Frontend] No human message found before index ${messageIndex}`
        );
        return;
      }

      console.log(
        `🔄 [Frontend] Last human message index: ${lastHumanMessageIndex}`
      );

      const messagesToRegenerate = messages.slice(0, lastHumanMessageIndex + 1);
      console.log(
        `🔄 [Frontend] Keeping ${
          messagesToRegenerate.length
        } messages, removing ${
          messages.length - messagesToRegenerate.length
        } messages`
      );

      // CRITICAL: Set messages immediately and log the exact state
      setMessages((prev) => {
        console.log(
          `🔄 [Frontend] BEFORE regeneration: ${prev.length} messages`
        );
        console.log(
          `🔄 [Frontend] SETTING TO: ${messagesToRegenerate.length} messages`
        );
        return messagesToRegenerate;
      });

      // Handle WebSocket connection state for regeneration
      if (
        !socketRef.current ||
        socketRef.current.readyState !== WebSocket.OPEN
      ) {
        console.log(
          `🔄 [Frontend] WebSocket not connected, attempting to reconnect for regeneration`
        );
        setError("Connection lost. Reconnecting...");

        try {
          await connect(); // Attempt to reconnect

          // Check if reconnection was successful after a brief delay
          await new Promise((resolve) => setTimeout(resolve, 1000));

          if (
            !socketRef.current ||
            socketRef.current.readyState !== WebSocket.OPEN
          ) {
            setError("Unable to reconnect. Please refresh the page.");
            setIsLoading(false);
            return;
          }

          setError(null); // Clear error on successful reconnection
        } catch (err) {
          console.error("Failed to reconnect for regeneration:", err);
          setError("Connection failed. Please refresh the page.");
          setIsLoading(false);
          return;
        }
      }

      // Proceed with regeneration if WebSocket is connected
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        const lastHumanMessage = messages[lastHumanMessageIndex];
        if (typeof lastHumanMessage.content === "string") {
          const regenerateData = {
            type: "regenerate",
            content: lastHumanMessage.content,
            page_id: currentPageIdRef.current,
          };
          console.log(`🔄 [Frontend] Sending regenerate data:`, regenerateData);
          socketRef.current.send(JSON.stringify(regenerateData));
          setIsLoading(true);
          setError(null);
        } else {
          console.warn(
            `🔄 [Frontend] Last human message content is not a string:`,
            lastHumanMessage.content
          );
          setError("Invalid message format for regeneration");
        }
      }
    },
    [messages]
  );

  const startNewChat = React.useCallback((newPageId?: string) => {
    // Stop any ongoing generation immediately
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const stopMessage = JSON.stringify({ type: "stop_generation" });
      socketRef.current.send(stopMessage);
      console.log("🔌 [WebSocket] Sent stop_generation for new chat");
    }

    // Reset local message state without adding the "stop" message to the UI
    setMessages([]);
    setError(null);

    // The parent component is now responsible for managing the pageId
    console.log(
      `🔌 [WebSocket] Starting new chat for page: ${newPageId || "new page"}`
    );
  }, []);

  const clearAllChats = useCallback(async () => {
    // Clear frontend state immediately for better UX
    setMessages([]);
    currentPageIdRef.current = "";

    // Clear WebSocket context
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "clear_context" }));
      socketRef.current.send(
        JSON.stringify({ type: "switch_page", page_id: "" })
      );
    }
    toast.success("Chat history cleared locally.");
  }, []);

  const stopGeneration = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "stop_generation" }));
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
