"use client";

import { AlertCircle, MessageSquarePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";

interface ConversationLimitReachedProps {
  messageCount: number;
  messageLimit: number;
  onStartNewChat: () => void;
}

export function ConversationLimitReached({
  messageCount,
  messageLimit,
  onStartNewChat,
}: ConversationLimitReachedProps) {
  return (
    <Alert className="mx-auto max-w-2xl border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-950/20">
      <AlertCircle className="h-4 w-4 text-orange-600 dark:text-orange-400" />
      <AlertTitle className="text-orange-900 dark:text-orange-100">
        Conversation Limit Reached
      </AlertTitle>
      <AlertDescription className="mt-2 space-y-3">
        <p className="text-orange-800 dark:text-orange-200">
          This conversation has reached the maximum limit of{" "}
          <strong>{messageLimit} messages</strong> ({messageCount} used).
        </p>
        <p className="text-sm text-orange-700 dark:text-orange-300">
          To maintain optimal performance and keep conversations focused, each
          chat is limited to {messageLimit} messages. Please start a new
          conversation to continue.
        </p>
        <Button
          onClick={onStartNewChat}
          className="w-full sm:w-auto bg-orange-600 hover:bg-orange-700 text-white"
        >
          <MessageSquarePlus className="mr-2 h-4 w-4" />
          Start New Chat
        </Button>
      </AlertDescription>
    </Alert>
  );
}