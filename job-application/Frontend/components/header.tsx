"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Plus, Bot, MessageSquare, Trash2, Menu, X } from "lucide-react"
import { SignedIn, SignedOut, UserButton, SignInButton } from "@clerk/nextjs"
import { ThemeToggle } from "./ui/theme-toggle"
import { PagesDialog } from "./pages-dialog"
import { ConfirmationDialog } from "./ui/confirmation-dialog"
import { cn } from "@/lib/utils"

interface HeaderProps {
  onNewChat: () => void
  onClearChat?: () => void
  currentPageId?: string
  onSelectPage: (pageId: string) => void
  isLoginPage?: boolean
}

export function Header({ onNewChat, onClearChat, currentPageId, onSelectPage, isLoginPage = false }: HeaderProps) {
  const [showPagesDialog, setShowPagesDialog] = React.useState(false)
  const [showClearConfirm, setShowClearConfirm] = React.useState(false)
  const [showMobileMenu, setShowMobileMenu] = React.useState(false)

  return (
    <>
      <div className="fixed top-0 left-0 right-0 z-50 bg-transparent p-2 sm:p-4 md:p-6 safe-area-inset-top">
        <div className="max-w-4xl mx-auto">
          <header className="flex items-center justify-between w-full px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 bg-background/80 rounded-xl sm:rounded-2xl md:rounded-3xl shadow-2xl border border-white/10 backdrop-blur-xl backdrop-saturate-150">
            {/* Logo and Title */}
            <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
              <div className="p-1.5 sm:p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg sm:rounded-xl shadow-lg flex-shrink-0">
                <Bot className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="text-sm sm:text-base md:text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent truncate">
                  Job Hacker Bot
                </h1>
                <p className="text-xs text-muted-foreground/80 -mt-0.5 hidden sm:block">AI-Powered Assistant</p>
              </div>
            </div>

            {/* Desktop Actions */}
            <div className="hidden md:flex items-center space-x-1.5 lg:space-x-2">
              {!isLoginPage && (
                <>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => setShowPagesDialog(true)}
                    className="h-9 w-9 lg:h-10 lg:w-10 rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105 touch-manipulation"
                    title="View Conversations"
                  >
                    <MessageSquare className="h-4 w-4 lg:h-5 lg:w-5" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={onNewChat}
                    className="h-9 w-9 lg:h-10 lg:w-10 rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105 touch-manipulation"
                    title="New Chat"
                  >
                    <Plus className="h-4 w-4 lg:h-5 lg:w-5" />
                  </Button>
                  {onClearChat && (
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      onClick={() => setShowClearConfirm(true)}
                      className="h-9 w-9 lg:h-10 lg:w-10 rounded-xl hover:bg-red-500/10 hover:text-red-500 transition-all duration-200 hover:scale-105 touch-manipulation"
                      title="Clear All Chat History"
                    >
                      <Trash2 className="h-4 w-4 lg:h-5 lg:w-5" />
                    </Button>
                  )}
                  <div className="h-6 w-px bg-border/50 mx-1" />
                </>
              )}
              <ThemeToggle />
              <SignedIn>
                <div className="ml-2">
                  <UserButton 
                    appearance={{
                      elements: {
                        avatarBox: "h-8 w-8 lg:h-9 lg:w-9 rounded-xl shadow-md hover:shadow-lg transition-all duration-200"
                      }
                    }}
                  />
                </div>
              </SignedIn>
              <SignedOut>
                <SignInButton mode="modal">
                  <Button 
                    variant="ghost" 
                    size="sm"
                    className="h-8 px-3 lg:h-9 lg:px-4 rounded-lg lg:rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-600/10 hover:from-blue-500/20 hover:to-purple-600/20 border border-blue-500/20 text-blue-600 dark:text-blue-400 transition-all duration-200 hover:scale-105 touch-manipulation ml-2"
                  >
                    Sign In
                  </Button>
                </SignInButton>
              </SignedOut>
            </div>

            {/* Mobile Actions */}
            <div className="flex md:hidden items-center space-x-1.5 sm:space-x-2">
              <SignedIn>
                <UserButton 
                  appearance={{
                    elements: {
                      avatarBox: "h-7 w-7 sm:h-8 sm:w-8 rounded-lg sm:rounded-xl shadow-md hover:shadow-lg transition-all duration-200"
                    }
                  }}
                />
              </SignedIn>
              <SignedOut>
                <SignInButton mode="modal">
                  <Button 
                    variant="ghost" 
                    size="sm"
                    className="h-8 px-3 sm:h-9 sm:px-4 rounded-lg sm:rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-600/10 hover:from-blue-500/20 hover:to-purple-600/20 border border-blue-500/20 text-blue-600 dark:text-blue-400 transition-all duration-200 hover:scale-105 touch-manipulation"
                  >
                    Sign In
                  </Button>
                </SignInButton>
              </SignedOut>
              {!isLoginPage && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowMobileMenu(!showMobileMenu)}
                  className="h-8 w-8 sm:h-9 sm:w-9 rounded-lg sm:rounded-xl hover:bg-white/10 transition-all duration-200 hover:scale-105 touch-manipulation"
                >
                  {showMobileMenu ? <X className="h-4 w-4 sm:h-5 sm:w-5" /> : <Menu className="h-4 w-4 sm:h-5 sm:w-5" />}
                </Button>
              )}
              {isLoginPage && (
                <ThemeToggle />
              )}
            </div>
          </header>

          {/* Mobile Menu */}
          {showMobileMenu && !isLoginPage && (
            <div className="md:hidden mt-2 bg-background/90 backdrop-blur-xl border border-white/10 rounded-xl sm:rounded-2xl shadow-2xl overflow-hidden animate-fade-in">
              <div className="p-3 sm:p-4 space-y-2 sm:space-y-3">
                <Button 
                  variant="ghost" 
                  onClick={() => {
                    setShowPagesDialog(true)
                    setShowMobileMenu(false)
                  }}
                  className="w-full justify-start h-11 sm:h-12 rounded-lg sm:rounded-xl hover:bg-white/10 transition-all duration-200 touch-manipulation"
                >
                  <MessageSquare className="h-4 w-4 sm:h-5 sm:w-5 mr-3" />
                  <span className="text-sm sm:text-base">View Conversations</span>
                </Button>
                <Button 
                  variant="ghost" 
                  onClick={() => {
                    onNewChat()
                    setShowMobileMenu(false)
                  }}
                  className="w-full justify-start h-11 sm:h-12 rounded-lg sm:rounded-xl hover:bg-white/10 transition-all duration-200 touch-manipulation"
                >
                  <Plus className="h-4 w-4 sm:h-5 sm:w-5 mr-3" />
                  <span className="text-sm sm:text-base">New Chat</span>
                </Button>
                {onClearChat && (
                  <Button 
                    variant="ghost" 
                    onClick={() => {
                      setShowClearConfirm(true)
                      setShowMobileMenu(false)
                    }}
                    className="w-full justify-start h-11 sm:h-12 rounded-lg sm:rounded-xl hover:bg-red-500/10 hover:text-red-500 transition-all duration-200 touch-manipulation"
                  >
                    <Trash2 className="h-4 w-4 sm:h-5 sm:w-5 mr-3" />
                    <span className="text-sm sm:text-base">Clear All History</span>
                  </Button>
                )}
                <div className="flex items-center justify-between pt-2 border-t border-white/10">
                  <span className="text-sm text-muted-foreground">Theme</span>
                  <ThemeToggle />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Close mobile menu when clicking outside */}
      {showMobileMenu && (
        <div 
          className="fixed inset-0 z-40 md:hidden" 
          onClick={() => setShowMobileMenu(false)}
        />
      )}
      
      <PagesDialog 
        isOpen={showPagesDialog} 
        onClose={() => setShowPagesDialog(false)}
        onSelectPage={onSelectPage}
        currentPageId={currentPageId}
      />
      
      <ConfirmationDialog
        open={showClearConfirm}
        onOpenChange={setShowClearConfirm}
        onConfirm={() => {
          onClearChat?.();
          setShowClearConfirm(false);
        }}
        title="Clear All Chat History?"
        description="This will permanently delete all your chat messages and conversation history. This action cannot be undone."
      />
    </>
  )
}

// We need to re-create a simplified ChatSearch or placeholder
// For now, let's keep it simple. We can build it out later.
// import { Search } from "lucide-react"
// import { Input } from "./ui/input"
// export const ChatSearch = () => (
//   <div className="relative">
//     <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
//     <Input placeholder="Search chat..." className="pl-9 w-48" />
//   </div>
// ) 