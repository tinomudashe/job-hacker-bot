"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { EmailComposer } from "./email-composer";
import { FollowUpTracker } from "./follow-up-tracker";
import { cn } from "@/lib/utils";
import {
  Mail,
  Send,
  Clock,
  FileText,
  Sparkles,
  Plus,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";

interface EmailDialogProps {
  onSendMessage?: (message: string) => void;
  trigger?: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  initialTab?: "compose" | "follow-up" | "tracker";
  initialContext?: any;
  className?: string;
}

export function EmailDialog({
  onSendMessage,
  trigger,
  open,
  onOpenChange,
  initialTab = "compose",
  initialContext,
  className,
}: EmailDialogProps) {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [isOpen, setIsOpen] = useState(open || false);

  const handleOpenChange = (newOpen: boolean) => {
    setIsOpen(newOpen);
    if (onOpenChange) {
      onOpenChange(newOpen);
    }
  };

  const defaultTrigger = (
    <Button variant="outline" className="gap-2">
      <Mail className="h-4 w-4" />
      Email Tools
    </Button>
  );

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || defaultTrigger}
      </DialogTrigger>
      <DialogContent className={cn("max-w-4xl max-h-[90vh] overflow-y-auto", className)}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-primary" />
            Email Assistant
            <span className="ml-auto text-sm font-normal text-muted-foreground flex items-center gap-1">
              <Sparkles className="h-3 w-3" />
              AI-Powered
            </span>
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="compose" className="gap-1">
              <Send className="h-3 w-3" />
              Compose
            </TabsTrigger>
            <TabsTrigger value="follow-up" className="gap-1">
              <Clock className="h-3 w-3" />
              Follow-up
            </TabsTrigger>
            <TabsTrigger value="tracker" className="gap-1">
              <FileText className="h-3 w-3" />
              Tracker
            </TabsTrigger>
          </TabsList>

          <TabsContent value="compose" className="mt-4">
            <EmailComposer
              onSendMessage={onSendMessage}
              initialContext={initialContext}
              mode="compose"
            />
          </TabsContent>

          <TabsContent value="follow-up" className="mt-4">
            <EmailComposer
              onSendMessage={onSendMessage}
              initialContext={initialContext}
              mode="follow-up"
            />
          </TabsContent>

          <TabsContent value="tracker" className="mt-4">
            <FollowUpTracker
              onSendMessage={onSendMessage}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

// Quick access button for email tools
export function EmailToolsButton({
  onSendMessage,
  className,
}: {
  onSendMessage?: (message: string) => void;
  className?: string;
}) {
  const [showQuickActions, setShowQuickActions] = useState(false);

  const quickActions = [
    {
      label: "Job Application Email",
      icon: <Send className="h-4 w-4" />,
      action: () => {
        if (onSendMessage) {
          onSendMessage("Help me write a job application email");
        }
      },
    },
    {
      label: "Follow-up Email",
      icon: <Clock className="h-4 w-4" />,
      action: () => {
        if (onSendMessage) {
          onSendMessage("Generate a follow-up email for my job application");
        }
      },
    },
    {
      label: "Thank You Email",
      icon: <Mail className="h-4 w-4" />,
      action: () => {
        if (onSendMessage) {
          onSendMessage("Write a thank you email after an interview");
        }
      },
    },
    {
      label: "Networking Email",
      icon: <Plus className="h-4 w-4" />,
      action: () => {
        if (onSendMessage) {
          onSendMessage("Help me write a networking email");
        }
      },
    },
  ];

  return (
    <div className={cn("relative", className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowQuickActions(!showQuickActions)}
        className="gap-1"
      >
        <Mail className="h-4 w-4" />
        Email
        <ChevronRight
          className={cn(
            "h-3 w-3 transition-transform",
            showQuickActions && "rotate-90"
          )}
        />
      </Button>

      {showQuickActions && (
        <div className="absolute top-full mt-2 right-0 z-50 w-64 rounded-lg border bg-popover p-2 shadow-lg">
          <div className="space-y-1">
            {quickActions.map((action, index) => (
              <button
                key={index}
                onClick={() => {
                  action.action();
                  setShowQuickActions(false);
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors text-left"
              >
                {action.icon}
                {action.label}
              </button>
            ))}
          </div>
          
          <div className="border-t mt-2 pt-2">
            <EmailDialog
              onSendMessage={onSendMessage}
              trigger={
                <button className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors text-left font-medium">
                  <Sparkles className="h-4 w-4 text-primary" />
                  Open Email Assistant
                </button>
              }
            />
          </div>
        </div>
      )}
    </div>
  );
}