"use client";

import React, { useState, useEffect } from 'react';
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
import { MessageSquare, Trash2, Calendar, X, AlertTriangle } from "lucide-react";
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

  useEffect(() => {
    if (isOpen) {
      fetchPages();
      setShowDeleteAll(false);
    }
  }, [isOpen]);

  const fetchPages = async () => {
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
  };

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
        <DialogOverlay className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed left-[50%] top-[50%] z-50 w-[90vw] max-w-lg h-[80vh] translate-x-[-50%] translate-y-[-50%] bg-background/80 backdrop-blur-xl backdrop-saturate-150 shadow-2xl rounded-3xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
          onPointerDownOutside={(e) => e.preventDefault()}
          onEscapeKeyDown={onClose}
          style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.2)',
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.1)'
          }}
        >
          {/* Enhanced glass highlight with edge glow */}
          <div 
            className="absolute inset-0 rounded-3xl pointer-events-none"
            style={{
              background: 'linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 50%, rgba(255,255,255,0.05) 100%)',
              border: '1px solid transparent',
              backgroundClip: 'padding-box'
            }}
          />
          
          {/* Subtle edge glow */}
          <div className="absolute inset-0 rounded-3xl pointer-events-none bg-gradient-to-b from-white/5 via-transparent to-transparent" />
          
          {/* Header */}
          <DialogHeader 
            className="flex-row items-center justify-between p-4 backdrop-blur-sm relative rounded-t-3xl"
            style={{
              borderBottom: '1px solid rgba(255,255,255,0.1)',
              background: 'linear-gradient(90deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))'
            }}
          >
            <DialogTitle className="flex items-center gap-3">
              <div 
                className="p-2 backdrop-blur-sm rounded-2xl relative"
                style={{
                  background: 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.1))',
                  border: '1px solid rgba(59,130,246,0.2)',
                  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1)'
                }}
              >
                <MessageSquare className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">Conversations</h2>
                <p className="text-sm text-muted-foreground">
                  {pages.length} total
                </p>
              </div>
            </DialogTitle>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8 rounded-2xl relative transition-all duration-200 hover:scale-105"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                backdropFilter: 'blur(10px)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.1)'
                e.currentTarget.style.border = '1px solid rgba(255,255,255,0.2)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.05)'
                e.currentTarget.style.border = '1px solid rgba(255,255,255,0.1)'
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </DialogHeader>

          {/* Content */}
          <div className="flex flex-col h-full">
            {/* Actions */}
            {pages.length > 0 && (
              <div 
                className="flex justify-end p-4 backdrop-blur-sm relative"
                style={{
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                  background: 'linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.05))'
                }}
              >
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDeleteAll(!showDeleteAll)}
                  className="text-red-500 hover:text-red-600 rounded-2xl transition-all duration-200 hover:scale-105"
                  style={{
                    background: 'linear-gradient(135deg, rgba(239,68,68,0.05), rgba(239,68,68,0.02))',
                    border: '1px solid rgba(239,68,68,0.2)',
                    backdropFilter: 'blur(10px)',
                    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'linear-gradient(135deg, rgba(239,68,68,0.1), rgba(239,68,68,0.05))'
                    e.currentTarget.style.border = '1px solid rgba(239,68,68,0.3)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'linear-gradient(135deg, rgba(239,68,68,0.05), rgba(239,68,68,0.02))'
                    e.currentTarget.style.border = '1px solid rgba(239,68,68,0.2)'
                  }}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
              </div>
            )}

            {/* Delete all confirmation */}
            {showDeleteAll && (
              <div 
                className="mx-4 mt-4 p-4 backdrop-blur-sm rounded-2xl relative"
                style={{
                  background: 'linear-gradient(135deg, rgba(239,68,68,0.1), rgba(239,68,68,0.05))',
                  border: '1px solid rgba(239,68,68,0.2)',
                  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)'
                }}
              >
                <div className="flex items-start gap-3">
                  <div 
                    className="p-1.5 rounded-xl"
                    style={{
                      background: 'rgba(239,68,68,0.2)',
                      border: '1px solid rgba(239,68,68,0.3)'
                    }}
                  >
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-red-600 dark:text-red-400">Delete All Conversations?</h4>
                    <p className="text-sm text-red-700/80 dark:text-red-300/80 mt-1">
                      This will permanently delete all {pages.length} conversations.
                    </p>
                    <div className="flex gap-2 mt-3">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={handleDeleteAll}
                        disabled={isLoading}
                        className="backdrop-blur-sm rounded-2xl"
                      >
                        {isLoading ? "Deleting..." : "Delete All"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowDeleteAll(false)}
                        className="rounded-2xl"
                        style={{
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          backdropFilter: 'blur(10px)'
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Conversations list */}
            <div className="flex-1 overflow-y-auto p-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-sm text-muted-foreground">Loading conversations...</p>
                  </div>
                </div>
              ) : pages.length === 0 ? (
                <div className="text-center py-8">
                  <div 
                    className="p-4 backdrop-blur-sm rounded-3xl inline-block mb-4 relative"
                    style={{
                      background: 'linear-gradient(135deg, rgba(59,130,246,0.05), rgba(139,92,246,0.05))',
                      border: '1px solid rgba(59,130,246,0.1)',
                      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)'
                    }}
                  >
                    <MessageSquare className="h-12 w-12 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">No conversations yet</h3>
                  <p className="text-sm text-muted-foreground">
                    Start a new chat to create your first conversation.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pages.map((page) => (
                    <div
                      key={page.id}
                      className={cn(
                        "group relative flex items-center justify-between p-3 rounded-2xl cursor-pointer transition-all duration-200 hover:scale-[1.02] backdrop-blur-sm",
                        currentPageId === page.id 
                          ? "shadow-lg" 
                          : "hover:shadow-lg"
                      )}
                      style={{
                        background: currentPageId === page.id
                          ? 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.05))'
                          : 'linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
                        border: currentPageId === page.id
                          ? '1px solid rgba(59,130,246,0.3)'
                          : '1px solid rgba(255,255,255,0.1)',
                        boxShadow: currentPageId === page.id
                          ? 'inset 0 1px 0 rgba(255,255,255,0.1), 0 4px 6px -1px rgba(59,130,246,0.1)'
                          : 'inset 0 1px 0 rgba(255,255,255,0.05)'
                      }}
                      onClick={() => {
                        if (onSelectPage) {
                          onSelectPage(page.id);
                          onClose();
                        }
                      }}
                      onMouseEnter={(e) => {
                        if (currentPageId !== page.id) {
                          e.currentTarget.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04))'
                          e.currentTarget.style.border = '1px solid rgba(255,255,255,0.2)'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (currentPageId !== page.id) {
                          e.currentTarget.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))'
                          e.currentTarget.style.border = '1px solid rgba(255,255,255,0.1)'
                        }
                      }}
                    >
                      {/* Enhanced glass highlight on hover */}
                      <div 
                        className="absolute inset-0 rounded-2xl pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                        style={{
                          background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(255,255,255,0.05) 100%)'
                        }}
                      />
                      
                      <div className="flex-1 min-w-0 relative z-10">
                        <h3 className={cn(
                          "font-medium truncate",
                          currentPageId === page.id ? "text-primary" : "text-foreground"
                        )}>
                          {page.title}
                        </h3>
                        {page.created_at && (
                          <div className="flex items-center gap-1 mt-1">
                            <Calendar className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              {formatDate(page.created_at)}
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="icon"
                        className="opacity-0 group-hover:opacity-100 h-8 w-8 text-muted-foreground hover:text-red-500 rounded-2xl relative z-10 transition-all duration-200 hover:scale-110"
                        style={{
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          backdropFilter: 'blur(10px)'
                        }}
                        onClick={(e) => handleDeletePage(page.id, e)}
                        disabled={isDeleting === page.id}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(239,68,68,0.1)'
                          e.currentTarget.style.border = '1px solid rgba(239,68,68,0.2)'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(255,255,255,0.05)'
                          e.currentTarget.style.border = '1px solid rgba(255,255,255,0.1)'
                        }}
                      >
                        {isDeleting === page.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-500" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPortal>
    </Dialog>
  );
} 