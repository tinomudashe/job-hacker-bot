"use client";

import { cn } from "@/lib/utils";
import { 
  Crown, 
  Sparkles
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

interface Subscription {
  plan: string;
  is_active: boolean;
  trial_days_remaining?: number;
  expires_at?: string;
  features_unlocked?: number;
}

interface ModernSubscriptionBadgeProps {
  subscription: Subscription | null;
  className?: string;
  variant?: "minimal" | "detailed" | "animated" | "glassmorphic";
  showPulse?: boolean;
  onClick?: () => void;
}

export function ModernSubscriptionBadge({
  subscription,
  className,
  variant = "minimal",
  showPulse = true,
  onClick,
}: ModernSubscriptionBadgeProps) {
  const [isHovered, setIsHovered] = useState(false);

  if (!subscription || !subscription.is_active) {
    return null;
  }

  const isPro = subscription.plan === "pro";
  const isTrial = subscription.plan === "trial";

  // Minimal variant - clean and simple
  if (variant === "minimal") {
    return (
      <button
        type="button"
        onClick={onClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={cn(
          "relative inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md transition-all duration-200 border",
          isPro ? [
            "border-blue-500 dark:border-blue-400",
            "text-blue-600 dark:text-blue-400",
            "hover:border-blue-600 dark:hover:border-blue-300",
          ] : [
            "border-amber-500 dark:border-amber-400",
            "text-amber-600 dark:text-amber-400",
            "hover:border-amber-600 dark:hover:border-amber-300",
          ],
          className
        )}
      >
        {isPro ? <Crown className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
        <span className="font-semibold">{isPro ? "Pro" : "Trial"}</span>
      </button>
    );
  }

  // Detailed variant - outline only with more info
  if (variant === "detailed") {
    return (
      <div
        onClick={onClick}
        className={cn(
          "relative inline-flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition-all duration-300 border",
          isPro ? [
            "border-blue-500 dark:border-blue-400",
            "text-blue-600 dark:text-blue-400",
            "hover:border-blue-600 dark:hover:border-blue-300",
          ] : [
            "border-amber-500 dark:border-amber-400",
            "text-amber-600 dark:text-amber-400",
            "hover:border-amber-600 dark:hover:border-amber-300",
          ],
          className
        )}
      >
        <div className="flex items-center gap-2">
          {isPro ? <Crown className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
          <div className="flex flex-col">
            <span className="text-xs font-bold">
              {isPro ? "Pro" : "Trial"}
            </span>
            {!isPro && subscription.trial_days_remaining && (
              <span className="text-[10px] opacity-70">
                {subscription.trial_days_remaining} days left
              </span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Animated variant - outline with subtle animations
  if (variant === "animated") {
    return (
      <AnimatePresence>
        <motion.button
          type="button"
          onClick={onClick}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={cn(
            "relative inline-flex items-center gap-1.5 px-3 py-1 rounded-full border",
            isPro ? [
              "border-blue-500 dark:border-blue-400",
              "text-blue-600 dark:text-blue-400",
            ] : [
              "border-amber-500 dark:border-amber-400",
              "text-amber-600 dark:text-amber-400",
            ],
            className
          )}
        >          
          <motion.div
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 4, repeat: Infinity }}
          >
            {isPro ? <Crown className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
          </motion.div>
          
          <span className="text-xs font-bold">
            {isPro ? "Pro" : "Trial"}
          </span>
        </motion.button>
      </AnimatePresence>
    );
  }

  // Glassmorphic variant - outline only with glass effect
  if (variant === "glassmorphic") {
    return (
      <div
        onClick={onClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={cn(
          "relative inline-flex items-center gap-2 px-3 py-1.5 rounded-xl cursor-pointer transition-all duration-300",
          "backdrop-blur-sm",
          "border",
          isPro ? [
            "border-blue-500/50 hover:border-blue-500",
            "text-blue-600 dark:text-blue-400",
          ] : [
            "border-amber-500/50 hover:border-amber-500",
            "text-amber-600 dark:text-amber-400",
          ],
          className
        )}
      >        
        <div className="flex items-center gap-2">
          {isPro ? (
            <Crown className="h-4 w-4" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          
          <span className="text-xs font-semibold">
            {isPro ? "Pro" : "Trial"}
          </span>
          {!isPro && subscription.trial_days_remaining && isHovered && (
            <motion.span 
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-[10px] opacity-70"
            >
              {subscription.trial_days_remaining}d
            </motion.span>
          )}
        </div>
      </div>
    );
  }

  return null;
}

// Stripe-inspired subscription status indicator
export function SubscriptionStatus({ subscription }: { subscription: Subscription | null }) {
  if (!subscription) return null;

  const isPro = subscription.plan === "pro" && subscription.is_active;
  const isTrial = subscription.plan === "trial" && subscription.is_active;

  return (
    <div className="inline-flex items-center gap-1.5">
      <div className={cn(
        "h-2 w-2 rounded-full",
        isPro ? "bg-green-500" : isTrial ? "bg-yellow-500" : "bg-gray-400"
      )} />
      <span className="text-xs text-muted-foreground">
        {isPro ? "Premium" : isTrial ? "Trial" : "Free"}
      </span>
    </div>
  );
}