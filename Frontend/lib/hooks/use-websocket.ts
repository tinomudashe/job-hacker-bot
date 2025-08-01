"use client";

import { useSubscriptionStore } from "@/lib/stores/useSubscriptionStore";
import { toast } from "@/lib/toast";
import { useAuth } from "@clerk/nextjs";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  createdAt?: string;
  reasoningSteps?: ReasoningStep[];
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
  content?: string;
  id?: string;
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
  const { triggerRefetch } = useSubscriptionStore();

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

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/ws/orchestrator?token=${token}`;

    const newSocket = new WebSocket(wsUrl);
    socketRef.current = newSocket;

    newSocket.onopen = () => {
      setIsConnected(true);
      isConnecting.current = false;
      setError(null);
      console.log("WebSocket connection established");
      if (currentPageIdRef.current) {
        newSocket.send(
          JSON.stringify({
            type: "switch_page",
            page_id: currentPageIdRef.current,
          })
        );
      }
    };

    newSocket.onmessage = (event) => {
      let parsedData: WebSocketMessage;
      try {
        parsedData = JSON.parse(event.data);
      } catch (e) {
        parsedData = {
          type: "final_response",
          message: event.data,
          id: uuidv4(),
        };
      }

      switch (parsedData.type) {
        case "message_chunk":
        case "final_response":
          const messageContent = parsedData.content || parsedData.message || "";
          const messageId = parsedData.id || "ai-placeholder";

          setMessages((prev) => {
            const existingAiMessageIndex = prev.findIndex(
              (msg) => msg.id === "ai-placeholder"
            );

            if (existingAiMessageIndex !== -1) {
              const newMessages = [...prev];
              const currentMsg = newMessages[existingAiMessageIndex];
              newMessages[existingAiMessageIndex] = {
                ...currentMsg,
                content:
                  parsedData.type === "message_chunk"
                    ? currentMsg.content + messageContent
                    : messageContent,
                id:
                  parsedData.type === "final_response"
                    ? messageId
                    : currentMsg.id,
              };
              return newMessages;
            } else if (parsedData.type === "final_response") {
              return [
                ...prev,
                { id: messageId, content: messageContent, isUser: false },
              ];
            }
            return prev;
          });

          if (parsedData.type === "final_response") {
            setIsLoading(false);
            setReasoningSteps([]);
          }
          break;

        case "reasoning_chunk":
          const reasoningContent = parsedData.data?.content || "";
          setReasoningSteps((prev) => [
            ...prev,
            {
              type: "reasoning_chunk",
              content: reasoningContent,
              step: parsedData.data?.step,
              specialist: parsedData.data?.specialist,
              tool_name: parsedData.data?.tool_name,
              progress: parsedData.data?.progress,
              timestamp: parsedData.timestamp || new Date().toISOString(),
            },
          ]);
          break;

        case "error":
          toast.error(parsedData.message || "An unknown error occurred.");
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
            `[WebSocket] Ignoring unknown message type: ${parsedData.type}`,
            parsedData
          );
          break;
      }
    };

    newSocket.onclose = (event) => {
      setIsConnected(false);
      isConnecting.current = false;
      if (event.code !== 1000 && event.code !== 1001) {
        setTimeout(() => {
          if (isLoaded && isSignedIn) {
            connect();
          }
        }, 2000);
      }
    };
    newSocket.onerror = (error) => {
      setError("WebSocket connection failed.");
      isConnecting.current = false;
    };
  }, [
    getToken,
    currentPageIdRef,
    isLoaded,
    isSignedIn,
    triggerRefetch,
    setCurrentPageId,
  ]);

  useEffect(() => {
    if (isLoaded && currentPageId !== undefined) {
      const loadPageMessages = async () => {
        setIsHistoryLoading(true);
        const history = await fetchMessagesForPage(currentPageId);
        setMessages(history);
        setIsHistoryLoading(false);

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
      if (!message || message.trim() === "") return;
      if (socketRef.current?.readyState !== WebSocket.OPEN) {
        setError("Connection lost. Reconnecting...");
        if (isLoaded && isSignedIn) connect();
        return;
      }

      setIsLoading(true);
      setError(null);
      setReasoningSteps([]);

      const messageData = {
        type: "message",
        content: message.trim(),
        page_id: currentPageIdRef.current,
      };
      socketRef.current.send(JSON.stringify(messageData));

      const userMessage: Message = {
        id: uuidv4(),
        content: message.trim(),
        isUser: true,
        createdAt: new Date().toISOString(),
      };
      const aiPlaceholderMessage: Message = {
        id: "ai-placeholder",
        content: "",
        isUser: false,
      };

      setMessages((prevMessages) => [
        ...prevMessages,
        userMessage,
        aiPlaceholderMessage,
      ]);
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
            headers: { Authorization: `Bearer ${token}` },
          });
          if (!response.ok) {
            throw new Error("Failed to delete message(s).");
          }
        };
        toast.promise(deletePromise(), {
          loading: "Deleting messages...",
          success: "Messages deleted.",
          error: (err: Error) => {
            setMessages(originalMessages);
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
        toast.error("Message not found");
        return;
      }

      const originalMessages = [...messages];
      const messagesToKeep = messages.slice(0, messageIndex);
      const editedMessage = { ...messages[messageIndex], content: newContent };
      const subsequentCount = originalMessages.length - messageIndex - 1;

      const previewMessages = [...messagesToKeep, editedMessage];
      setMessages(previewMessages);

      const editPromise = async () => {
        const token = await getToken();
        if (!token) {
          throw new Error("Authentication token not available");
        }

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
        }

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
          setError(null);
        } else {
          throw new Error(
            "Connection lost - message edited but conversation cannot continue automatically"
          );
        }

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
          setMessages(originalMessages);
          return `Edit failed: ${err.message}`;
        },
      });
    },
    [messages, getToken]
  );

  const regenerateMessage = useCallback(
    async (id: string) => {
      const messageIndex = messages.findIndex((msg) => msg.id === id);
      if (messageIndex === -1) return;

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

      if (
        !socketRef.current ||
        socketRef.current.readyState !== WebSocket.OPEN
      ) {
        setError("Connection lost. Reconnecting...");
        try {
          await connect();
          await new Promise((resolve) => setTimeout(resolve, 1000));
          if (
            !socketRef.current ||
            socketRef.current.readyState !== WebSocket.OPEN
          ) {
            setError("Unable to reconnect. Please refresh the page.");
            setIsLoading(false);
            return;
          }
          setError(null);
        } catch (err) {
          setError("Connection failed. Please refresh the page.");
          setIsLoading(false);
          return;
        }
      }

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
          socketRef.current.send(JSON.stringify(regenerateData));
          setIsLoading(true);
          setError(null);
        } else {
          setError("Invalid message format for regeneration");
        }
      }
    },
    [messages, connect]
  );

  const startNewChat = React.useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "stop_generation" }));
    }
    setMessages([]);
    setError(null);
  }, []);

  const clearAllChats = useCallback(async () => {
    setMessages([]);
    currentPageIdRef.current = "";

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
    reasoningSteps,
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
