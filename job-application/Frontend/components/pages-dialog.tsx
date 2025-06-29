"use client";

import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogPortal,
  DialogOverlay,
} from "@/components/ui/dialog";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Button } from "@/components/ui/button";
import { useAuth } from "@clerk/nextjs";
import { toast } from "@/lib/toast";
import { MessageSquare, Trash2, Calendar, X, AlertTriangle, FileText, Paperclip } from "lucide-react";
import { cn } from "@/lib/utils";

interface Page {
  id: string;
  title: string;
  created_at?: string;
}

interface PagesDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPage?: (pageId: string) => void;
  currentPageId?: string;
}

export function PagesDialog({ isOpen, onClose, onSelectPage, currentPageId }: PagesDialogProps) {
  const [pages, setPages] = useState<Page[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [showDeleteAll, setShowDeleteAll] = useState(false);
  const { getToken } = useAuth();

  const fetchPages = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = await getToken();
      const response = await fetch('/api/pages', {
        headers: { 'Authorization': `Bearer ${token}` },
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
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        setPages(prev => prev.filter(page => page.id !== pageId));
        toast.success("Conversation deleted");
        
        if (pageId === currentPageId && onSelectPage) {
          onSelectPage('');
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
    if (!confirm("Are you sure you want to delete ALL conversations? This action cannot be undone.")) {
      return;
    }

    setIsLoading(true);
    try {
      const token = await getToken();
      const deletePromises = pages.map(page => 
        fetch(`/api/pages/${page.id}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        })
      );

      await Promise.all(deletePromises);
      setPages([]);
      setShowDeleteAll(false);
      toast.success("All conversations deleted");
      
      if (onSelectPage) {
        onSelectPage('');
      }
    } catch (error) {
      console.error("Error deleting all pages:", error);
      toast.error("Failed to delete all conversations");
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogPortal>
        <DialogOverlay className="fixed inset-0 z-50 bg-black/70 dark:bg-black/80 backdrop-blur-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed left-[50%] top-[50%] z-50 w-[92vw] max-w-md h-[85vh] translate-x-[-50%] translate-y-[-50%] backdrop-blur-3xl backdrop-saturate-200 shadow-2xl rounded-3xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 bg-white/95 border border-white/40 dark:bg-gray-950/95 dark:border-gray-800/50 flex flex-col"
          onPointerDownOutside={(e) => e.preventDefault()}
          onEscapeKeyDown={onClose}
        >
          {/* Enhanced glassmorphism effects */}
          <div className="absolute inset-0 rounded-3xl pointer-events-none bg-gradient-to-br from-white/30 via-white/10 to-transparent dark:from-white/20 dark:via-white/5 dark:to-transparent" />
          <div className="absolute inset-0 rounded-3xl pointer-events-none border border-white/50 dark:border-white/30" />
          <div className="absolute inset-[1px] rounded-3xl pointer-events-none bg-gradient-to-b from-white/20 via-transparent to-transparent dark:from-white/10 dark:via-transparent dark:to-transparent" />
          
          {/* Header */}
          <DialogHeader 
            className="flex-shrink-0 flex-row items-center justify-between p-5 backdrop-blur-md relative rounded-t-3xl border-b border-gray-200/60 bg-gradient-to-r from-gray-50/90 to-white/70 dark:border-gray-700/60 dark:from-gray-900/90 dark:to-gray-950/70"
          >
            <DialogTitle className="flex items-center gap-3">
              <div className="p-2.5 backdrop-blur-sm rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-300/40 shadow-lg dark:from-blue-400/20 dark:to-purple-400/20 dark:border-blue-600/40">
                <MessageSquare className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Conversations</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 -mt-0.5">
                  {pages.length > 5 ? `5 of ${pages.length} total` : `${pages.length} total`}
                </p>
              </div>
            </DialogTitle>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-9 w-9 rounded-xl transition-all duration-200 hover:scale-105 bg-gray-100/90 border border-gray-200/70 backdrop-blur-sm hover:bg-gray-200/95 hover:border-gray-300/80 dark:bg-gray-800/90 dark:border-gray-700/70 dark:hover:bg-gray-700/95 dark:hover:border-gray-600/80"
            >
              <X className="h-4 w-4" />
            </Button>
          </DialogHeader>

          {/* Content */}
          <div className="flex flex-col flex-1 min-h-0">
            {/* Actions */}
            {pages.length > 0 && (
              <div className="flex-shrink-0 flex justify-end p-5 backdrop-blur-md relative border-b border-gray-200/50 bg-gradient-to-r from-gray-50/70 to-white/50 dark:border-gray-700/50 dark:from-gray-900/70 dark:to-gray-950/50">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDeleteAll(!showDeleteAll)}
                  className="text-red-600 hover:text-red-700 rounded-xl transition-all duration-300 hover:scale-105 bg-gradient-to-br from-red-50/95 to-red-100/85 border-red-200/70 backdrop-blur-sm hover:from-red-100/95 hover:to-red-200/90 hover:border-red-300/80 hover:shadow-lg dark:text-red-400 dark:hover:text-red-300 dark:from-red-950/95 dark:to-red-900/85 dark:border-red-800/70 dark:hover:from-red-900/95 dark:hover:to-red-800/90 dark:hover:border-red-700/80 font-medium"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
              </div>
            )}

            {/* Delete all confirmation */}
            {showDeleteAll && (
              <div className="flex-shrink-0 mx-5 mt-4 p-5 backdrop-blur-md rounded-2xl relative bg-gradient-to-br from-red-50/95 to-red-100/85 border border-red-200/70 shadow-lg dark:from-red-950/95 dark:to-red-900/85 dark:border-red-800/70">
                <div className="flex items-start gap-4">
                  <div className="p-2.5 rounded-xl bg-red-500/20 border border-red-300/40 backdrop-blur-sm shadow-sm dark:bg-red-400/20 dark:border-red-600/40">
                    <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-red-800 dark:text-red-200 mb-1">Delete All Conversations?</h4>
                    <p className="text-sm text-red-700/80 dark:text-red-300/80 leading-relaxed">
                      This will permanently delete all {pages.length} conversations. This action cannot be undone.
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
                        className="rounded-xl bg-white/80 border-gray-300/60 backdrop-blur-sm hover:bg-white/95 hover:border-gray-400/70 dark:bg-gray-800/80 dark:border-gray-600/60 dark:hover:bg-gray-700/95 dark:hover:border-gray-500/70 font-medium hover:scale-105 transition-all duration-200"
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
                      <div className="animate-spin rounded-full h-10 w-10 border-2 border-blue-500/20 border-t-blue-500 mx-auto"></div>
                      <div className="animate-pulse absolute inset-0 rounded-full bg-blue-500/10"></div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">Loading conversations...</p>
                  </div>
                </div>
              ) : pages.length === 0 ? (
                <div className="text-center py-12">
                  <div className="relative mb-6">
                    <div className="p-5 backdrop-blur-sm rounded-3xl inline-block bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-300/30 shadow-lg dark:from-blue-400/10 dark:to-purple-400/10 dark:border-blue-600/30">
                      <MessageSquare className="h-12 w-12 text-blue-500 dark:text-blue-400" />
                    </div>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">No conversations yet</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 max-w-sm mx-auto leading-relaxed">
                    Start chatting to create your first conversation. Your chat history will appear here.
                  </p>
                  {/* Spacer for empty state */}
                  <div className="h-8"></div>
                </div>
              ) : (
                <>
                  {/* Show only first 5 conversations */}
                  {pages.slice(0, 5).map((page) => {
                    // Enhanced file attachment detection
                    const isFileAttachment = page.title.includes('**File Attached:**') || 
                      page.title.includes('CV/Resume uploaded') ||
                      page.title.includes('📎') ||
                      page.title.includes('📄');
                    
                    const getFileInfo = () => {
                      if (page.title.includes('**File Attached:**')) {
                        const fileName = page.title.split('**File Attached:**')[1]?.trim();
                        return { type: 'file', fileName, icon: '📎' };
                      }
                      if (page.title.includes('CV/Resume uploaded')) {
                        const fileName = page.title.split('**File:**')[1]?.split('\n')[0]?.trim() || 'CV/Resume';
                        return { type: 'cv', fileName, icon: '📄' };
                      }
                      return null;
                    };

                    const fileInfo = getFileInfo();
                    
                    return (
                      <div
                        key={page.id}
                        className={cn(
                          "group relative rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] backdrop-blur-md border shadow-lg overflow-hidden",
                          currentPageId === page.id 
                            ? isFileAttachment
                              ? "bg-gradient-to-br from-purple-500/20 to-blue-500/20 border-purple-300/50 shadow-purple-500/20 dark:from-purple-400/20 dark:to-blue-400/20 dark:border-purple-600/50 dark:shadow-purple-800/20"
                              : "bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border-blue-300/50 shadow-blue-500/20 dark:from-blue-400/20 dark:to-cyan-400/20 dark:border-blue-600/50 dark:shadow-blue-800/20"
                            : isFileAttachment
                              ? "bg-gradient-to-br from-purple-50/90 to-blue-50/80 border-purple-200/50 hover:from-purple-100/95 hover:to-blue-100/85 hover:border-purple-300/60 hover:shadow-xl dark:from-purple-950/90 dark:to-blue-950/80 dark:border-purple-700/50 dark:hover:from-purple-900/95 dark:hover:to-blue-900/85 dark:hover:border-purple-600/60"
                              : "bg-gradient-to-br from-gray-50/90 to-white/80 border-gray-200/50 hover:from-gray-100/95 hover:to-white/90 hover:border-gray-300/60 hover:shadow-xl dark:from-gray-900/90 dark:to-gray-800/80 dark:border-gray-700/50 dark:hover:from-gray-800/95 dark:hover:to-gray-700/85 dark:hover:border-gray-600/60"
                        )}
                        onClick={() => {
                          console.log(`🔍 [PagesDialog] Clicked on page:`, {
                            pageId: page.id,
                            title: page.title,
                            created: page.created_at
                          });
                          if (onSelectPage) {
                            console.log(`📤 [PagesDialog] Calling onSelectPage with ID: ${page.id}`);
                            onSelectPage(page.id);
                            onClose();
                          }
                        }}
                      >
                        {/* Enhanced glassmorphism highlight on hover */}
                        <div className="absolute inset-0 rounded-2xl pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-br from-white/40 via-white/15 to-transparent dark:from-white/25 dark:via-white/8 dark:to-transparent" />
                        
                        <div className="flex items-start gap-4 p-4 relative z-10 overflow-hidden">
                          {/* Icon/Avatar */}
                          <div className={cn(
                            "flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center shadow-md transition-all duration-300 group-hover:scale-110",
                            isFileAttachment
                              ? "bg-gradient-to-br from-purple-500 to-blue-500 text-white shadow-purple-500/25"
                              : "bg-gradient-to-br from-gray-400 to-gray-600 text-white shadow-gray-500/25"
                          )}>
                            {fileInfo ? (
                              <span className="text-lg">{fileInfo.icon}</span>
                            ) : (
                              <MessageSquare className="h-5 w-5" />
                            )}
                          </div>
                          
                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            {isFileAttachment && fileInfo ? (
                              <>
                                <h3 className={cn(
                                  "font-semibold text-sm mb-1 truncate",
                                  currentPageId === page.id 
                                    ? "text-purple-700 dark:text-purple-300" 
                                    : "text-purple-600 dark:text-purple-400"
                                )}>
                                  File Attached: <span className="truncate">{fileInfo.fileName}</span>
                                </h3>
                                <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                                  {fileInfo.type === 'cv' ? 'CV/Resume uploaded' : 'Document attachment'}
                                </p>
                              </>
                            ) : (
                              <h3 className={cn(
                                "font-medium text-sm leading-tight truncate",
                                currentPageId === page.id 
                                  ? "text-blue-700 dark:text-blue-300" 
                                  : "text-gray-900 dark:text-gray-100"
                              )}>
                                {page.title}
                              </h3>
                            )}
                            
                            {page.created_at && (
                              <div className="flex items-center gap-1.5 mt-2">
                                <Calendar className="h-3 w-3 text-gray-500 dark:text-gray-400" />
                                <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                                  {formatDate(page.created_at)}
                                </span>
                              </div>
                            )}
                          </div>
                          
                          {/* Delete button */}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="opacity-0 group-hover:opacity-100 h-8 w-8 text-gray-400 hover:text-red-500 rounded-xl relative z-10 transition-all duration-300 hover:scale-110 bg-white/50 border border-gray-200/50 backdrop-blur-sm hover:bg-red-50/90 hover:border-red-200/60 dark:text-gray-500 dark:hover:text-red-400 dark:bg-gray-800/50 dark:border-gray-700/50 dark:hover:bg-red-950/80 dark:hover:border-red-800/60"
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
                    <div className="mt-4 mb-6 p-4 backdrop-blur-md rounded-2xl bg-gradient-to-br from-orange-50/95 to-yellow-50/85 border border-orange-200/70 shadow-lg dark:from-orange-950/95 dark:to-yellow-950/85 dark:border-orange-800/70">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 p-2 rounded-lg bg-orange-500/20 border border-orange-300/40 backdrop-blur-sm dark:bg-orange-400/20 dark:border-orange-600/40">
                          <AlertTriangle className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-orange-800 dark:text-orange-200 mb-2">
                            Too many conversations
                          </h4>
                          <p className="text-sm text-orange-700/80 dark:text-orange-300/80 leading-relaxed mb-3">
                            Showing 5 of {pages.length} conversations. Please delete some conversations to see more and improve performance.
                          </p>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setShowDeleteAll(true)}
                            className="text-orange-600 hover:text-orange-700 rounded-lg transition-all duration-200 bg-orange-100/50 border-orange-200/50 hover:bg-orange-200/60 hover:border-orange-300/60 dark:text-orange-400 dark:hover:text-orange-300 dark:bg-orange-900/50 dark:border-orange-800/50 dark:hover:bg-orange-800/60 dark:hover:border-orange-700/60"
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
                    <span className="font-medium tracking-wide">End of conversations</span>
                    <div className="w-12 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent dark:via-gray-600 animate-pulse"></div>
                  </div>
                  <div className="mt-3 flex space-x-1">
                    <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1.5s' }}></div>
                    <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '200ms', animationDuration: '1.5s' }}></div>
                    <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '400ms', animationDuration: '1.5s' }}></div>
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