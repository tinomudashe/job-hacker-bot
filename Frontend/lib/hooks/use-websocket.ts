"use client";

import { useSubscriptionStore } from "@/lib/stores/useSubscriptionStore"; // Import the new store
import { toast } from "@/lib/toast";
import { useAuth } from "@clerk/nextjs";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws");

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  createdAt?: string; // Optional: Backend provides created_at, useful for display/ordering
  reasoningSteps?: ReasoningStep[]; // For AI messages with reasoning streams
}

interface ReasoningStep {
  type: "reasoning_start" | "reasoning_chunk" | "reasoning_complete";
  content: string;
  step?: string;
  specialist?: string;
  tool_name?: string;
  progress?: string;
  timestamp: string;
}

interface WebSocketMessage {
  type: string;
  message?: string;
  data?: {
    content: string;
    step?: string;
    specialist?: string;
    tool_name?: string;
    progress?: string;
  };
  timestamp?: string;
  page_id?: string;
}

export const useWebSocket = (
  currentPageId?: string,
  setCurrentPageId?: (id: string) => void
) => {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const isConnecting = useRef(false);
  const currentPageIdRef = useRef(currentPageId);
  const { triggerRefetch } = useSubscriptionStore(); // Get the trigger function

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
    // FIX: Construct WebSocket URL safely, removing any trailing slash from WS_URL
    // to prevent double slashes, and avoiding URL encoding issues with the token.
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/ws/orchestrator?token=${token}`;

    const newSocket = new WebSocket(wsUrl);
    socketRef.current = newSocket;

    newSocket.onopen = () => {
      setIsConnected(true);
      isConnecting.current = false;
      setError(null); // Clear any previous connection errors
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
        parsedData = JSON.parse(event.data) as WebSocketMessage;
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
      // FIX: The parser logic is rewritten to be more robust and to correctly
      // handle the events being sent by the backend, including reasoning and final_response.
      switch (parsedData.type) {
        case "message":
        case "final_response":
          const aiMessageContent =
            (parsedData as any).content || parsedData.message || "";

          setMessages((prev) => {
            const lastMessage = prev[prev.length - 1];
            // Prevent duplicates by checking if the last message is identical.
            const isDuplicate =
              lastMessage &&
              !lastMessage.isUser &&
              lastMessage.content === aiMessageContent;
            if (isDuplicate) {
              return prev;
            }
            return [
              ...prev,
              { id: uuidv4(), content: aiMessageContent, isUser: false },
            ];
          });
          setIsLoading(false);
          setReasoningSteps([]);
          break;

        case "reasoning":
          // This handles the complex event stream from LangGraph
          const eventData = (parsedData as any).data;
          if (!eventData) break;

          const eventKey = Object.keys(eventData)[0];
          const eventContent = eventData[eventKey];

          if (eventContent?.reasoning_events) {
            setReasoningSteps((prev) => [
              ...prev,
              ...eventContent.reasoning_events,
            ]);
          }
          break;

        case "reasoning_start":
        case "reasoning_chunk":
        case "reasoning_complete":
          setReasoningSteps((prev) => [
            ...prev,
            {
              type: parsedData.type as ReasoningStep["type"],
              content: parsedData.data?.content || "",
              step: parsedData.data?.step,
              specialist: parsedData.data?.specialist,
              tool_name: parsedData.data?.tool_name,
              progress: parsedData.data?.progress,
              timestamp: parsedData.timestamp || new Date().toISOString(),
            },
          ]);
          break;

        case "error":
          toast.error(parsedData.message || "Unknown error occurred");
          setIsLoading(false);
          break;

        case "page_created":
          const newPageId = parsedData.page_id as string;
          if (newPageId && setCurrentPageId) {
            setCurrentPageId(newPageId);
            currentPageIdRef.current = newPageId;
            localStorage.setItem("lastConversationId", newPageId);
            window.history.pushState({}, "", `/?page_id=${newPageId}`);
          }
          break;

        case "subscription_updated":
          triggerRefetch();
          toast.success("Your subscription has been updated!");
          break;

        default:
          console.warn(
            `[WebSocket] Unknown message type: ${parsedData.type}`,
            parsedData
          );
          if (parsedData.message) {
            setMessages((prev) => [
              ...prev,
              {
                id: uuidv4(),
                content: parsedData.message as string,
                isUser: false,
              },
            ]);
            setIsLoading(false);
          }
          break;
      }
    };

    newSocket.onclose = (event) => {
      setIsConnected(false);
      isConnecting.current = false;
      console.log(
        `WebSocket connection closed with code: ${event.code}, reason: ${event.reason}`
      );

      // Auto-reconnect if the connection was closed unexpectedly (not by user action)
      if (event.code !== 1000 && event.code !== 1001) {
        console.log("Attempting to reconnect in 2 seconds...");
        setTimeout(() => {
          if (isLoaded && isSignedIn) {
            connect();
          }
        }, 2000);
      }
    };
    newSocket.onerror = (error) => {
      setError(
        "WebSocket connection failed: " +
          (error instanceof Event ? error.type : String(error))
      );
      isConnecting.current = false;
      console.error("WebSocket connection error:", error);
    };
  }, [
    getToken,
    currentPageIdRef,
    isLoaded,
    isSignedIn,
    triggerRefetch,
    setCurrentPageId,
  ]);

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
    if (isLoaded && isSignedIn) {
      connect();
    }
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [isLoaded, isSignedIn, connect]);

  const sendMessage = useCallback(
    (message: string) => {
      // Centralized validation to prevent sending empty messages
      if (!message || message.trim() === "") {
        console.warn(
          "Attempted to send an empty or whitespace-only message. Aborting."
        );
        return;
      }

      if (socketRef.current?.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket is not connected. Message not sent.");
        setError("Connection lost. Reconnecting...");
        // Attempt to reconnect
        if (isLoaded && isSignedIn) {
          connect();
        }
        return;
      }

      // FIX: Activate the loading state immediately on send.
      setIsLoading(true);
      setError(null);

      const messageData = {
        type: "message",
        content: message.trim(),
        page_id: currentPageIdRef.current,
      };
      socketRef.current.send(JSON.stringify(messageData));
      // Optimistically add user message to the UI
      const userMessage: Message = {
        id: uuidv4(),
        content: message.trim(),
        isUser: true,
        createdAt: new Date().toISOString(),
      };
      setMessages((prevMessages) => [...prevMessages, userMessage]);
    },
    [currentPageIdRef, isLoaded, isSignedIn, connect]
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
    [messages, connect]
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
    reasoningSteps, // Return the new state
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
