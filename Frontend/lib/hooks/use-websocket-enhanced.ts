"use client";

import { toast } from "@/lib/toast";
import { useAuth } from "@clerk/nextjs";
import { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { usePage } from "./use-page-context";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface Message {
  id: string;
  content: string | object;
  isUser: boolean;
}

export const useWebSocketEnhanced = () => {
  const { getToken, isLoaded } = useAuth();
  const { pageId, setPageId, ...pageContext } = usePage();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Refs for stable references
  const socketRef = useRef<WebSocket | null>(null);
  const isConnecting = useRef(false);
  const currentPageIdRef = useRef(pageId);
  const pendingOperations = useRef<Set<string>>(new Set());

  // Load last opened page from API on initial load
  useEffect(() => {
    const fetchLastOpenedPage = async () => {
      const token = await getToken();
      if (!token) return;

      try {
        const response = await fetch("/api/pages/last-opened", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const lastPage = await response.json();
          if (lastPage && lastPage.id) {
            setPageId(lastPage.id);
          }
        }
      } catch (error) {
        console.error("Failed to fetch last opened page:", error);
      }
    };

    if (isLoaded) {
      fetchLastOpenedPage();
    }
  }, [isLoaded, getToken, setPageId]);

  // Update refs and save to localStorage when props change
  useEffect(() => {
    currentPageIdRef.current = pageId;
    if (pageId) {
      localStorage.setItem("lastOpenPageId", pageId);
    }
  }, [pageId]);

  // Enhanced message fetching with better error handling
  const fetchMessagesForPage = useCallback(
    async (pageId?: string): Promise<Message[]> => {
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not available");
      }

      try {
        const url = pageId
          ? `/api/messages?page_id=${pageId}`
          : "/api/messages";

        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error(
            `Failed to fetch messages: ${response.status} ${response.statusText}`
          );
        }

        const history = await response.json();
        return history.map(
          (msg: { id: string; content: string; is_user_message: boolean }) => ({
            id: msg.id,
            content: msg.content,
            isUser: msg.is_user_message,
          })
        );
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error";
        console.error("Error fetching messages:", errorMessage);
        throw new Error(errorMessage);
      }
    },
    [getToken]
  );

  // Enhanced page creation with proper error handling
  const createNewPage = useCallback(
    async (firstMessage: string): Promise<string> => {
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not available");
      }

      try {
        console.log(
          `📄 [WebSocket Enhanced] Creating new page for message: "${firstMessage.substring(
            0,
            50
          )}..."`
        );

        const response = await fetch("/api/pages", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ first_message: firstMessage }),
        });

        if (!response.ok) {
          throw new Error(
            `Failed to create page: ${response.status} ${response.statusText}`
          );
        }

        const newPage = await response.json();
        console.log(`📄 [WebSocket Enhanced] Created new page: ${newPage.id}`);
        return newPage.id;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to create page";
        console.error("Error creating page:", errorMessage);
        throw new Error(errorMessage);
      }
    },
    [getToken]
  );

  // Enhanced WebSocket connection with better error handling
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
      setError("Authentication token not available");
      return;
    }

    try {
      const wsUrl = `${WS_URL}/api/ws/orchestrator?token=${token}`;
      const newSocket = new WebSocket(wsUrl);
      socketRef.current = newSocket;

      newSocket.onopen = () => {
        setIsConnected(true);
        isConnecting.current = false;
        setError(null);
        console.log("✅ WebSocket connection established");
      };

      newSocket.onmessage = (event) => {
        try {
          let parsedContent;
          try {
            parsedContent = JSON.parse(event.data);
          } catch {
            parsedContent = event.data;
          }

          console.log(`📨 [WebSocket Enhanced] Received message`);
          setMessages((prev) => [
            ...prev,
            { id: uuidv4(), content: parsedContent, isUser: false },
          ]);
          setIsLoading(false);
        } catch (err) {
          console.error("Error processing WebSocket message:", err);
          setError("Error processing server response");
        }
      };

      newSocket.onclose = (event) => {
        setIsConnected(false);
        isConnecting.current = false;
        console.log(
          `🔌 WebSocket connection closed: ${event.code} ${event.reason}`
        );

        // Attempt reconnection if not intentional close
        if (event.code !== 1000) {
          setTimeout(() => {
            if (!isConnecting.current) {
              console.log("🔄 Attempting WebSocket reconnection...");
              connect();
            }
          }, 3000);
        }
      };

      newSocket.onerror = (event) => {
        console.error("❌ WebSocket error:", event);
        setError("WebSocket connection failed");
        isConnecting.current = false;
      };
    } catch (err) {
      console.error("Error creating WebSocket connection:", err);
      setError("Failed to establish connection");
      isConnecting.current = false;
    }
  }, [getToken, setIsHistoryLoading, setError]);

  // Enhanced page loading with proper state management
  useEffect(() => {
    if (!isLoaded || pageId === undefined) return;

    const loadPageMessages = async () => {
      try {
        setIsHistoryLoading(true);

        console.log(
          `📖 Loading messages for page: ${pageId || "new conversation"}`
        );
        const history = await fetchMessagesForPage(pageId);

        console.log(
          `📖 Loaded ${history.length} messages for page: ${
            pageId || "new conversation"
          }`
        );
        setMessages(history);

        // Notify WebSocket about page change to sync context
        if (
          socketRef.current &&
          socketRef.current.readyState === WebSocket.OPEN
        ) {
          socketRef.current.send(
            JSON.stringify({
              type: "switch_page",
              page_id: pageId,
            })
          );
          console.log(
            `🔄 Notified WebSocket about page switch: ${
              pageId || "new conversation"
            }`
          );
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load messages";
        console.error("Error loading page messages:", err);
        setError(errorMessage);
        setIsHistoryLoading(false);
      } finally {
        setIsHistoryLoading(false);
      }
    };

    loadPageMessages();
  }, [pageId, isLoaded, fetchMessagesForPage]);

  // Initialize WebSocket connection
  useEffect(() => {
    if (isLoaded) {
      connect();
    }
    return () => {
      if (socketRef.current) {
        socketRef.current.close(1000, "Component unmounting");
      }
    };
  }, [isLoaded, connect]);

  // Enhanced message sending with better page management
  const sendMessage = useCallback(
    async (content: string) => {
      const operationId = uuidv4();
      pendingOperations.current.add(operationId);

      try {
        let pageId = currentPageIdRef.current;

        console.log(
          `📤 [WebSocket Enhanced] Sending message: "${content.substring(
            0,
            50
          )}..."`
        );
        console.log(`📤 [WebSocket Enhanced] Current pageId: ${pageId}`);
        console.log(
          `📤 [WebSocket Enhanced] Messages count: ${messages.length}`
        );

        // Determine if we need to create a new page
        const needsNewPage =
          !pageId &&
          (messages.length === 0 || !pageContext.isLoaded || pageContext.error);

        if (needsNewPage) {
          try {
            pageId = await createNewPage(content);
            currentPageIdRef.current = pageId;

            // Save new page ID to localStorage
            if (pageId) {
              localStorage.setItem("lastOpenPageId", pageId);
            }

            setPageId(pageId || null);
          } catch (err) {
            const errorMessage =
              err instanceof Error
                ? err.message
                : "Failed to create conversation";
            setError(errorMessage);
            throw new Error(errorMessage);
          }
        }

        // Ensure WebSocket is connected
        if (
          !socketRef.current ||
          socketRef.current.readyState !== WebSocket.OPEN
        ) {
          console.log("🔄 WebSocket not connected, attempting to connect...");
          await connect();

          // Wait a bit for connection to establish
          await new Promise((resolve) => setTimeout(resolve, 1000));

          if (
            !socketRef.current ||
            socketRef.current.readyState !== WebSocket.OPEN
          ) {
            throw new Error("Failed to establish WebSocket connection");
          }
        }

        // Send message with page context
        const messageData = {
          content,
          page_id: pageId,
        };

        console.log(
          `📤 [WebSocket Enhanced] Sending message data:`,
          messageData
        );
        socketRef.current.send(JSON.stringify(messageData));

        // Add user message to UI immediately
        setMessages((prev) => [
          ...prev,
          { id: uuidv4(), content, isUser: true },
        ]);
        setIsLoading(true);
        setError(null);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to send message";
        console.error("Error sending message:", err);
        setError(errorMessage);
        setIsLoading(false);
      } finally {
        pendingOperations.current.delete(operationId);
      }
    },
    [messages, pageContext, connect, createNewPage, getToken, setPageId]
  );

  // Enhanced message deletion with better error handling
  const deleteMessage = useCallback(
    async (id: string) => {
      const messageIndex = messages.findIndex((msg) => msg.id === id);
      if (messageIndex === -1) {
        console.warn(`Message with id ${id} not found`);
        return;
      }

      const originalMessages = [...messages];
      const messagesToKeep = messages.slice(0, messageIndex);

      // Immediate UI update
      setMessages(messagesToKeep);

      const timeoutId = setTimeout(() => {
        const deletePromise = async () => {
          try {
            const token = await getToken();
            if (!token) {
              throw new Error("Authentication token not available");
            }

            const response = await fetch(`/api/messages/${id}?cascade=true`, {
              method: "DELETE",
              headers: {
                Authorization: `Bearer ${token}`,
              },
            });

            if (!response.ok) {
              throw new Error(
                `Failed to delete message: ${response.status} ${response.statusText}`
              );
            }

            console.log(
              `🗑️ Successfully deleted message ${id} and subsequent messages`
            );
          } catch (err) {
            console.error("Error deleting message:", err);
            setMessages(originalMessages); // Revert on error
            throw err;
          }
        };

        toast.promise(deletePromise(), {
          loading: "Deleting messages...",
          success: "Messages deleted successfully",
          error: (err: Error) => {
            return `Failed to delete: ${err.message}`;
          },
        });
      }, 5000);

      toast("Message will be deleted", {
        description: `This will delete the message and ${
          originalMessages.length - messagesToKeep.length - 1
        } subsequent message(s)`,
        action: {
          label: "Undo",
          onClick: () => {
            clearTimeout(timeoutId);
            setMessages(originalMessages);
            console.log("🔄 Message deletion undone");
          },
        },
      });
    },
    [messages, getToken]
  );

  // Enhanced message editing with proper state management
  const editMessage = useCallback(
    async (id: string, newContent: string) => {
      const messageIndex = messages.findIndex((msg) => msg.id === id);
      if (messageIndex === -1) {
        console.warn(`Message with id ${id} not found for editing`);
        return;
      }

      const originalMessages = [...messages];
      const messagesToKeep = messages.slice(0, messageIndex);
      const editedMessage = { ...messages[messageIndex], content: newContent };
      const previewMessages = [...messagesToKeep, editedMessage];

      // Show preview immediately
      setMessages(previewMessages);

      const subsequentCount = originalMessages.length - messageIndex - 1;

      toast("Confirm message edit?", {
        description: `This will edit the message and remove ${subsequentCount} subsequent message(s). The conversation will continue from the edited message.`,
        action: {
          label: "Confirm Edit",
          onClick: async () => {
            try {
              const token = await getToken();
              if (!token) {
                throw new Error("Authentication token not available");
              }

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
                throw new Error(
                  `Failed to update message: ${updateResponse.status}`
                );
              }

              // Delete subsequent messages
              if (subsequentCount > 0) {
                const deleteResponse = await fetch(
                  `/api/messages/${id}?cascade=true&above=true`,
                  {
                    method: "DELETE",
                    headers: { Authorization: `Bearer ${token}` },
                  }
                );

                if (!deleteResponse.ok) {
                  throw new Error(
                    `Failed to delete subsequent messages: ${deleteResponse.status}`
                  );
                }
              }

              // Send edited message to WebSocket to continue conversation
              if (
                socketRef.current &&
                socketRef.current.readyState === WebSocket.OPEN
              ) {
                const messageData = {
                  content: newContent,
                  page_id: currentPageIdRef.current,
                };
                socketRef.current.send(JSON.stringify(messageData));
                setIsLoading(true);
                console.log("📝 Sent edited message to continue conversation");
              }

              toast.success("Message edited successfully");
            } catch (err) {
              const errorMessage =
                err instanceof Error ? err.message : "Failed to edit message";
              console.error("Error editing message:", err);
              setError(errorMessage);
              setMessages(originalMessages); // Revert on error
              toast.error(`Edit failed: ${errorMessage}`);
            }
          },
        },
        onDismiss: () => {
          setMessages(originalMessages);
          console.log("🔄 Message edit cancelled");
        },
      });
    },
    [messages, getToken]
  );

  // Enhanced regeneration with better error handling
  const regenerateMessage = useCallback(
    async (id: string) => {
      const messageIndex = messages.findIndex((msg) => msg.id === id);
      if (messageIndex === -1) {
        console.warn(`Message with id ${id} not found for regeneration`);
        return;
      }

      console.log(`🔄 [WebSocket Enhanced] Regenerating message ID: ${id}`);
      console.log(`🔄 [WebSocket Enhanced] Message index: ${messageIndex}`);
      console.log(`🔄 [WebSocket Enhanced] Total messages: ${messages.length}`);
      console.log(
        `🔄 [WebSocket Enhanced] Current page ID: ${currentPageIdRef.current}`
      );

      // Find the last human message before the one being regenerated
      let lastHumanMessageIndex = -1;
      for (let i = messageIndex - 1; i >= 0; i--) {
        if (messages[i].isUser) {
          lastHumanMessageIndex = i;
          break;
        }
      }

      if (lastHumanMessageIndex === -1) {
        console.error(
          `🔄 [WebSocket Enhanced] No human message found before index ${messageIndex}`
        );
        toast.error("Cannot regenerate: No previous user message found");
        return;
      }

      try {
        // Ensure WebSocket is connected
        if (
          !socketRef.current ||
          socketRef.current.readyState !== WebSocket.OPEN
        ) {
          console.log(
            "🔄 WebSocket not connected for regeneration, attempting to connect..."
          );
          await connect();

          // Wait for connection
          await new Promise((resolve) => setTimeout(resolve, 1000));

          if (
            !socketRef.current ||
            socketRef.current.readyState !== WebSocket.OPEN
          ) {
            throw new Error("WebSocket connection failed");
          }
        }

        const lastHumanMessage = messages[lastHumanMessageIndex];
        if (typeof lastHumanMessage.content !== "string") {
          throw new Error("Cannot regenerate: Invalid message content");
        }

        console.log(
          `🔄 [WebSocket Enhanced] Last human message index: ${lastHumanMessageIndex}`
        );

        const messagesToKeep = messages.slice(0, lastHumanMessageIndex + 1);
        console.log(
          `🔄 [WebSocket Enhanced] Keeping ${
            messagesToKeep.length
          } messages, removing ${
            messages.length - messagesToKeep.length
          } messages`
        );

        // Update UI immediately
        setMessages(messagesToKeep);
        setIsLoading(true);
        setError(null);

        const regenerateData = {
          type: "regenerate",
          content: lastHumanMessage.content,
          page_id: currentPageIdRef.current,
        };

        console.log(
          `🔄 [WebSocket Enhanced] Sending regenerate data:`,
          regenerateData
        );
        socketRef.current.send(JSON.stringify(regenerateData));

        // Set timeout for regeneration
        const timeoutId = setTimeout(() => {
          if (isLoading) {
            setIsLoading(false);
            setError("Regeneration timed out. Please try again.");
            console.error("🔄 Regeneration timed out");
          }
        }, 60000); // 60 second timeout

        // Clear timeout when loading stops
        const cleanup = () => {
          clearTimeout(timeoutId);
        };

        // Store cleanup function for potential cancellation
        (regenerateMessage as any)._cleanup = cleanup;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to regenerate message";
        console.error("Error regenerating message:", err);
        setError(errorMessage);
        setIsLoading(false);
        toast.error(`Regeneration failed: ${errorMessage}`);
      }
    },
    [messages, connect]
  );

  // Enhanced chat management
  const startNewChat = useCallback(async () => {
    try {
      // Clear local state immediately
      setMessages([]);
      currentPageIdRef.current = undefined;
      localStorage.removeItem("lastOpenPageId");

      // Clear WebSocket context
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.send(JSON.stringify({ type: "clear_context" }));
        socketRef.current.send(
          JSON.stringify({ type: "switch_page", page_id: null })
        );
      }

      toast.success("New conversation started");
      console.log("🆕 Started new conversation");
    } catch (err) {
      console.error("Error starting new chat:", err);
      toast.error("Failed to start new conversation");
    }
  }, []);

  const clearAllChats = useCallback(async () => {
    try {
      // Clear local state
      setMessages([]);
      currentPageIdRef.current = undefined;
      localStorage.removeItem("lastOpenPageId");

      // Clear WebSocket context
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.send(JSON.stringify({ type: "clear_context" }));
        socketRef.current.send(
          JSON.stringify({ type: "switch_page", page_id: null })
        );
      }

      // Delete all conversations from database
      const token = await getToken();
      if (token) {
        const response = await fetch("/api/chats", {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to clear chats: ${response.status}`);
        }

        toast.success("All conversations cleared");
        console.log("🗑️ Cleared all conversations");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to clear conversations";
      console.error("Error clearing chats:", err);
      toast.error(errorMessage);
    }
  }, [getToken]);

  const stopGeneration = useCallback(() => {
    try {
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.send(JSON.stringify({ type: "stop_generation" }));
        setIsLoading(false);
        console.log("⏹️ Stopped generation");
      }

      // Clear any pending regeneration cleanup
      if ((regenerateMessage as any)._cleanup) {
        (regenerateMessage as any)._cleanup();
      }
    } catch (err) {
      console.error("Error stopping generation:", err);
    }
  }, []);

  return {
    // Core state
    messages,
    isLoading,
    isHistoryLoading,
    error,
    isConnected,

    // Core functions
    sendMessage,
    deleteMessage,
    editMessage,
    regenerateMessage,
    startNewChat,
    clearAllChats,
    stopGeneration,

    // Utility functions
    createNewPage,
    fetchMessagesForPage,
  };
};
