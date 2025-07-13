"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "@/lib/toast";
import { cn } from "@/lib/utils";
import { useAuth } from "@clerk/nextjs";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import {
  AlertTriangle,
  Calendar,
  MessageSquare,
  Trash2,
  X,
} from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";

interface Page {
  id: string;
  title: string;
  created_at?: string;
  last_opened_at?: string;
}

interface ConversationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPage?: (pageId: string) => void;
  currentPageId?: string;
}

export function ConversationDialog({
  isOpen,
  onClose,
  onSelectPage,
  currentPageId,
}: ConversationDialogProps) {
  const [pages, setPages] = useState<Page[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [showDeleteAll, setShowDeleteAll] = useState(false);
  const { getToken } = useAuth();

  const fetchPages = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/pages", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setPages(data);
      } else {
        toast.error("Failed to load conversations");
      }
    } catch (error) {
      console.error("Error fetching pages:", error);
      toast.error("Failed to load conversations");
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    if (isOpen) {
      fetchPages();
      setShowDeleteAll(false);
    }
  }, [isOpen, fetchPages]);

  const handleDeletePage = async (pageId: string, event: React.MouseEvent) => {
    event.stopPropagation();

    if (!confirm("Are you sure you want to delete this conversation?")) {
      return;
    }

    setIsDeleting(pageId);
    try {
      const token = await getToken();
      const response = await fetch(`/api/pages/${pageId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setPages((prev) => prev.filter((page) => page.id !== pageId));
        toast.success("Conversation deleted");

        if (pageId === currentPageId && onSelectPage) {
          onSelectPage("");
        }
      } else {
        toast.error("Failed to delete conversation");
      }
    } catch (error) {
      console.error("Error deleting page:", error);
      toast.error("Failed to delete conversation");
    } finally {
      setIsDeleting(null);
    }
  };

  const handleDeleteAll = async () => {
    if (
      !confirm(
        "Are you sure you want to delete ALL conversations? This action cannot be undone."
      )
    ) {
      return;
    }

    setIsLoading(true);
    try {
      const token = await getToken();
      const deletePromises = pages.map((page) =>
        fetch(`/api/pages/${page.id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        })
      );

      await Promise.all(deletePromises);
      setPages([]);
      setShowDeleteAll(false);
      toast.success("All conversations deleted");

      if (onSelectPage) {
        onSelectPage("");
      }
    } catch (error) {
      console.error("Error deleting all pages:", error);
      toast.error("Failed to delete all conversations");
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogPortal>
        <DialogOverlay className="fixed inset-0 z-50 bg-black/70 dark:bg-black/80 backdrop-blur-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed left-[50%] top-[50%] z-50 w-[92vw] max-w-md h-[85vh] translate-x-[-50%] translate-y-[-50%] !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 shadow-2xl rounded-3xl !border !border-gray-200 dark:!border-white/8 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 flex flex-col"
          onPointerDownOutside={(e) => e.preventDefault()}
          onEscapeKeyDown={onClose}
        >
          {/* Header */}
          <DialogHeader className="flex-shrink-0 flex-row items-center justify-between p-5 rounded-t-3xl !border-b !border-gray-200 dark:!border-white/8 !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150">
            <DialogTitle className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl !bg-blue-100 !border !border-blue-200 shadow-lg dark:!bg-blue-500/20 dark:!border-blue-500/40">
                <MessageSquare className="h-5 w-5 !text-blue-600 dark:!text-blue-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Conversations
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 -mt-0.5 font-light">
                  {pages.length > 5
                    ? `5 of ${pages.length} total`
                    : `${pages.length} total`}
                </p>
              </div>
            </DialogTitle>

            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-9 w-9 rounded-xl transition-all duration-200 hover:scale-105 !bg-gray-100 !border !border-gray-200 hover:!bg-gray-200 dark:!bg-background/60 dark:!border-white/8 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:hover:!bg-background/80"
            >
              <X className="h-4 w-4" />
            </Button>
          </DialogHeader>

          {/* Content */}
          <div className="flex flex-col flex-1 min-h-0">
            {/* Actions */}
            {pages.length > 0 && (
              <div className="flex-shrink-0 flex justify-end p-5 !border-b !border-gray-200 dark:!border-white/8 !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDeleteAll(!showDeleteAll)}
                  className="text-red-600 hover:text-red-700 rounded-xl transition-all duration-300 hover:scale-105 !bg-red-50/95 !border-red-200/70 hover:!bg-red-100/95 hover:!border-red-300/80 hover:shadow-lg dark:text-red-400 dark:hover:text-red-300 dark:!bg-red-950/95 dark:!border-red-800/70 dark:hover:!bg-red-900/95 dark:hover:!border-red-700/80 font-medium"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
              </div>
            )}

            {/* Delete all confirmation */}
            {showDeleteAll && (
              <div className="flex-shrink-0 mx-5 mt-4 p-5 rounded-2xl !bg-red-50/95 !border !border-red-200/70 shadow-lg dark:!bg-red-950/95 dark:!border-red-800/70">
                <div className="flex items-start gap-4">
                  <div className="p-2.5 rounded-xl !bg-red-500/20 !border !border-red-300/40 shadow-sm dark:!bg-red-400/20 dark:!border-red-600/40">
                    <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-red-800 dark:text-red-200 mb-1">
                      Delete All Conversations?
                    </h4>
                    <p className="text-sm text-red-700/80 dark:text-red-300/80 leading-relaxed">
                      This will permanently delete all {pages.length}{" "}
                      conversations. This action cannot be undone.
                    </p>
                    <div className="flex gap-3 mt-4">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={handleDeleteAll}
                        disabled={isLoading}
                        className="backdrop-blur-sm rounded-xl font-medium hover:scale-105 transition-all duration-200"
                      >
                        {isLoading ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border border-white/30 border-t-white mr-2" />
                            Deleting...
                          </>
                        ) : (
                          "Delete All"
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowDeleteAll(false)}
                        className="rounded-xl !bg-gray-100 !border !border-gray-200 hover:!bg-gray-200 font-medium hover:scale-105 transition-all duration-200 dark:!bg-background/60 dark:!border-white/8 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:hover:!bg-background/80"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Conversations list with proper scrolling */}
            <div className="flex-1 flex flex-col min-h-0">
              <div className="flex-1 overflow-y-auto overscroll-contain scroll-smooth scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent dark:scrollbar-thumb-gray-600">
                <div className="p-4 pb-12 pt-2 space-y-3">
                  {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="text-center">
                        <div className="relative mb-6">
                          <div className="animate-spin rounded-full h-10 w-10 border-2 border-foreground/20 border-t-foreground mx-auto"></div>
                          <div className="animate-pulse absolute inset-0 rounded-full bg-foreground/10"></div>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                          Loading conversations...
                        </p>
                      </div>
                    </div>
                  ) : pages.length === 0 ? (
                    <div className="text-center py-12">
                      <div className="relative mb-6">
                        <div className="p-5 rounded-3xl inline-block !bg-blue-100 !border !border-blue-200 shadow-lg dark:!bg-blue-500/20 dark:!border-blue-500/40">
                          <MessageSquare className="h-12 w-12 !text-blue-600 dark:!text-blue-400" />
                        </div>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                        No conversations yet
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 max-w-sm mx-auto leading-relaxed">
                        Start chatting to create your first conversation. Your
                        chat history will appear here.
                      </p>
                      {/* Spacer for empty state */}
                      <div className="h-8"></div>
                    </div>
                  ) : (
                    <>
                      {/* Show only first 5 conversations */}
                      {pages.slice(0, 5).map((page) => {
                        // Enhanced file attachment detection
                        const isFileAttachment =
                          page.title.includes("**File Attached:**") ||
                          page.title.includes("CV/Resume uploaded") ||
                          page.title.includes("📎") ||
                          page.title.includes("📄");

                        const getFileInfo = () => {
                          if (page.title.includes("**File Attached:**")) {
                            const fileName = page.title
                              .split("**File Attached:**")[1]
                              ?.trim();
                            return { type: "file", fileName, icon: "📎" };
                          }
                          if (page.title.includes("CV/Resume uploaded")) {
                            const fileName =
                              page.title
                                .split("**File:**")[1]
                                ?.split("\n")[0]
                                ?.trim() || "CV/Resume";
                            return { type: "cv", fileName, icon: "📄" };
                          }
                          return null;
                        };

                        const fileInfo = getFileInfo();

                        return (
                          <div
                            key={page.id}
                            className={cn(
                              "group relative rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] border shadow-lg overflow-hidden",
                              currentPageId === page.id
                                ? isFileAttachment
                                  ? "!bg-purple-500/20 !border-purple-300/50 shadow-purple-500/20 dark:!bg-purple-400/20 dark:!border-purple-600/50 dark:shadow-purple-800/20"
                                  : "!bg-blue-50 !border-blue-200 shadow-2xl dark:!bg-background/80 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/20"
                                : isFileAttachment
                                ? "!bg-purple-50/90 !border-purple-200/50 hover:!bg-purple-100/95 hover:!border-purple-300/60 hover:shadow-xl dark:!bg-purple-950/90 dark:!border-purple-700/50 dark:hover:!bg-purple-900/95 dark:hover:!border-purple-600/60"
                                : "!bg-gray-50 !border-gray-200 hover:!bg-gray-100 hover:!border-gray-300 hover:shadow-xl dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8 dark:hover:!bg-background/80 dark:hover:!border-white/12"
                            )}
                            onClick={() => {
                              console.log(
                                `🔍 [ConversationDialog] Clicked on page:`,
                                {
                                  pageId: page.id,
                                  title: page.title,
                                  created: page.created_at,
                                }
                              );
                              if (onSelectPage) {
                                console.log(
                                  `📤 [ConversationDialog] Calling onSelectPage with ID: ${page.id}`
                                );
                                onSelectPage(page.id);
                                onClose();
                              }
                            }}
                          >
                            {/* Hover highlight effect */}
                            <div className="absolute inset-0 rounded-2xl pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300 !bg-gray-200/50 dark:!bg-white/10" />

                            <div className="flex items-start gap-4 p-4 relative z-10 overflow-hidden">
                              {/* Icon/Avatar */}
                              <div
                                className={cn(
                                  "flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center shadow-md transition-all duration-300 group-hover:scale-110",
                                  isFileAttachment
                                    ? "!bg-purple-500 text-white shadow-purple-500/25"
                                    : "!bg-gray-800 text-white shadow-gray-800/25 dark:!bg-gray-700 dark:shadow-gray-700/25"
                                )}
                              >
                                {fileInfo ? (
                                  <span className="text-lg">
                                    {fileInfo.icon}
                                  </span>
                                ) : (
                                  <MessageSquare className="h-5 w-5" />
                                )}
                              </div>

                              {/* Content */}
                              <div className="flex-1 min-w-0">
                                {isFileAttachment && fileInfo ? (
                                  <>
                                    <h3
                                      className={cn(
                                        "font-semibold text-sm mb-1 truncate",
                                        currentPageId === page.id
                                          ? "text-purple-700 dark:text-purple-300"
                                          : "text-purple-600 dark:text-purple-400"
                                      )}
                                    >
                                      File Attached:{" "}
                                      <span className="truncate">
                                        {fileInfo.fileName}
                                      </span>
                                    </h3>
                                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                                      {fileInfo.type === "cv"
                                        ? "CV/Resume uploaded"
                                        : "Document attachment"}
                                    </p>
                                  </>
                                ) : (
                                  <h3
                                    className={cn(
                                      "font-medium text-sm leading-tight truncate text-gray-900 dark:text-gray-100",
                                      currentPageId === page.id &&
                                        "font-semibold"
                                    )}
                                  >
                                    {page.title}
                                  </h3>
                                )}

                                {/* Display last_opened_at if available and different from created_at, else display created_at */}
                                {(page.created_at || page.last_opened_at) && (
                                  <div className="flex items-center gap-1.5 mt-2">
                                    <Calendar className="h-3 w-3 text-gray-500 dark:text-gray-400" />
                                    <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                                      {page.last_opened_at &&
                                      page.created_at &&
                                      new Date(page.last_opened_at).getTime() >
                                        new Date(page.created_at).getTime()
                                        ? `Last opened: ${formatDate(
                                            page.last_opened_at
                                          )}`
                                        : `Created: ${formatDate(
                                            page.created_at
                                          )}`}
                                    </span>
                                  </div>
                                )}
                              </div>

                              {/* Delete button */}
                              <Button
                                variant="ghost"
                                size="icon"
                                className="opacity-0 group-hover:opacity-100 h-8 w-8 text-gray-400 hover:text-red-500 rounded-xl relative z-10 transition-all duration-300 hover:scale-110 !bg-gray-100 !border !border-gray-200 hover:!bg-red-50/90 hover:!border-red-200/60 dark:!bg-background/60 dark:!border-white/8 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:hover:!bg-red-950/80 dark:hover:!border-red-800/60"
                                onClick={(e) => handleDeletePage(page.id, e)}
                                disabled={isDeleting === page.id}
                              >
                                {isDeleting === page.id ? (
                                  <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-red-500" />
                                ) : (
                                  <Trash2 className="h-3.5 w-3.5" />
                                )}
                              </Button>
                            </div>
                          </div>
                        );
                      })}

                      {/* Message when there are more than 5 conversations */}
                      {pages.length > 5 && (
                        <div className="mt-4 mb-6 p-4 rounded-2xl !bg-orange-50/95 !border !border-orange-200/70 shadow-lg dark:!bg-orange-950/95 dark:!border-orange-800/70">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 p-2 rounded-lg !bg-orange-500/20 !border !border-orange-300/40 dark:!bg-orange-400/20 dark:!border-orange-600/40">
                              <AlertTriangle className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-orange-800 dark:text-orange-200 mb-2">
                                Too many conversations
                              </h4>
                              <p className="text-sm text-orange-700/80 dark:text-orange-300/80 leading-relaxed mb-3">
                                Showing 5 of {pages.length} conversations.
                                Please delete some conversations to see more and
                                improve performance.
                              </p>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setShowDeleteAll(true)}
                                className="text-orange-600 hover:text-orange-700 rounded-lg transition-all duration-200 !bg-orange-100/50 !border-orange-200/50 hover:!bg-orange-200/60 hover:!border-orange-300/60 dark:text-orange-400 dark:hover:text-orange-300 dark:!bg-orange-900/50 dark:!border-orange-800/50 dark:hover:!bg-orange-800/60 dark:hover:!border-orange-700/60"
                              >
                                <Trash2 className="h-3 w-3 mr-2" />
                                Delete Conversations
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  {/* End of conversations indicator - only show when there are conversations */}
                  {pages.length > 0 && (
                    <div className="flex flex-col items-center justify-center py-8 opacity-60 animate-pulse">
                      <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                        <div className="w-12 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent dark:via-gray-600 animate-pulse"></div>
                        <span className="font-medium tracking-wide">
                          End of conversations
                        </span>
                        <div className="w-12 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent dark:via-gray-600 animate-pulse"></div>
                      </div>
                      <div className="mt-3 flex space-x-1">
                        <div
                          className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"
                          style={{
                            animationDelay: "0ms",
                            animationDuration: "1.5s",
                          }}
                        ></div>
                        <div
                          className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"
                          style={{
                            animationDelay: "200ms",
                            animationDuration: "1.5s",
                          }}
                        ></div>
                        <div
                          className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"
                          style={{
                            animationDelay: "400ms",
                            animationDuration: "1.5s",
                          }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPortal>
    </Dialog>
  );
}
