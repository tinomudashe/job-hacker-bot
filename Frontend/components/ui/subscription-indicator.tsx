"use client";

import { cn } from "@/lib/utils";
import { Crown, Sparkles, Lock, ChevronRight } from "lucide-react";
import { useState } from "react";
import { Button } from "./button";

interface Subscription {
  plan: string;
  is_active: boolean;
  trial_days_remaining?: number;
  expires_at?: string;
}

interface SubscriptionIndicatorProps {
  subscription: Subscription | null;
  className?: string;
  onClick?: () => void;
  compact?: boolean;
}

export function SubscriptionIndicator({
  subscription,
  className,
  onClick,
  compact = false,
}: SubscriptionIndicatorProps) {
  const [isHovered, setIsHovered] = useState(false);

  if (!subscription) {
    return null;
  }

  const isPro = subscription.plan === "pro" && subscription.is_active;
  const isTrial = subscription.plan === "trial" && subscription.is_active;
  const isExpired = !subscription.is_active;

  const getIcon = () => {
    if (isPro) return <Crown className="h-4 w-4" />;
    if (isTrial) return <Sparkles className="h-4 w-4" />;
    return <Lock className="h-4 w-4" />;
  };

  const getLabel = () => {
    if (isPro) return "Pro";
    if (isTrial) return "Trial";
    return "Free";
  };

  const getDescription = () => {
    if (isPro) {
      if (subscription.expires_at) {
        const expiryDate = new Date(subscription.expires_at);
        const daysLeft = Math.ceil(
          (expiryDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
        );
        if (daysLeft <= 7) {
          return `Expires in ${daysLeft} days`;
        }
      }
      return "Full access";
    }
    if (isTrial && subscription.trial_days_remaining !== undefined) {
      return `${subscription.trial_days_remaining} days left`;
    }
    if (isExpired) {
      return "Upgrade to Pro";
    }
    return "Limited access";
  };

  const getColorClasses = () => {
    if (isPro) {
      return "bg-gradient-to-r from-blue-500/10 to-purple-500/10 hover:from-blue-500/20 hover:to-purple-500/20 border-blue-400/30 dark:border-blue-600/30 text-blue-600 dark:text-blue-400";
    }
    if (isTrial) {
      return "bg-gradient-to-r from-amber-500/10 to-orange-500/10 hover:from-amber-500/20 hover:to-orange-500/20 border-amber-400/30 dark:border-amber-600/30 text-amber-600 dark:text-amber-400";
    }
    return "bg-gray-500/10 hover:bg-gray-500/20 border-gray-400/30 dark:border-gray-600/30 text-gray-600 dark:text-gray-400";
  };

  if (compact) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={onClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={cn(
          "relative h-8 px-2 rounded-full transition-all duration-300",
          getColorClasses(),
          isHovered ? "pr-3" : "",
          className
        )}
      >
        <div className="flex items-center gap-1.5">
          {getIcon()}
          <span className="text-xs font-semibold">{getLabel()}</span>
          {isHovered && (
            <ChevronRight className="h-3 w-3 animate-in slide-in-from-left-1" />
          )}
        </div>
        {isHovered && (
          <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap">
            <div className="bg-popover text-popover-foreground text-xs px-2 py-1 rounded-md shadow-lg border">
              {getDescription()}
            </div>
          </div>
        )}
      </Button>
    );
  }

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all duration-300 cursor-pointer",
        getColorClasses(),
        className
      )}
    >
      <div className="flex items-center gap-1.5">
        {getIcon()}
        <div className="flex flex-col">
          <span className="text-xs font-semibold leading-tight">
            {getLabel()}
          </span>
          <span className="text-[10px] opacity-70 leading-tight">
            {getDescription()}
          </span>
        </div>
      </div>
      {onClick && (
        <ChevronRight
          className={cn(
            "h-3 w-3 transition-transform duration-200",
            isHovered ? "translate-x-0.5" : ""
          )}
        />
      )}
    </div>
  );
}