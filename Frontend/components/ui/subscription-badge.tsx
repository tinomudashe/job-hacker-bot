import { Badge } from "@/components/ui/badge";
import { Crown, Sparkles, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface Subscription {
  plan: string;
  is_active: boolean;
  trial_days_remaining?: number;
  admin_access?: boolean;
}

interface SubscriptionBadgeProps {
  subscription: Subscription | null;
  className?: string;
  showIcon?: boolean;
}

export function SubscriptionBadge({ 
  subscription, 
  className,
  showIcon = true 
}: SubscriptionBadgeProps) {
  if (!subscription) {
    return null;
  }

  // Admin badge
  if (subscription.admin_access) {
    return (
      <Badge 
        variant="secondary"
        className={cn(
          "gap-1 px-2.5 py-1 font-medium shadow-md backdrop-blur-md",
          "bg-gradient-to-r from-purple-500/20 to-indigo-500/20",
          "border-purple-400/50 dark:border-purple-600/50", 
          "hover:from-purple-500/30 hover:to-indigo-500/30",
          "transition-all duration-200",
          className
        )}
      >
        {showIcon && <Crown className="h-3 w-3" />}
        <span className="text-xs font-semibold">ADMIN</span>
      </Badge>
    );
  }

  if (subscription.plan === "pro" && subscription.is_active) {
    return (
      <Badge 
        variant="pro" 
        className={cn(
          "gap-1 px-2.5 py-1 font-medium shadow-md backdrop-blur-md",
          "bg-gradient-to-r from-blue-500/20 to-purple-500/20",
          "border-blue-400/50 dark:border-blue-600/50",
          "hover:from-blue-500/30 hover:to-purple-500/30",
          "transition-all duration-200",
          className
        )}
      >
        {showIcon && <Crown className="h-3 w-3" />}
        <span className="text-xs font-semibold">PRO</span>
      </Badge>
    );
  }

  if (subscription.plan === "trial" && subscription.is_active) {
    return (
      <Badge 
        variant="trial" 
        className={cn(
          "gap-1 px-2.5 py-1 font-medium shadow-md backdrop-blur-md",
          "bg-gradient-to-r from-amber-500/20 to-orange-500/20",
          "border-amber-400/50 dark:border-amber-600/50",
          "hover:from-amber-500/30 hover:to-orange-500/30",
          "transition-all duration-200",
          className
        )}
      >
        {showIcon && <Sparkles className="h-3 w-3" />}
        <span className="text-xs font-semibold">TRIAL</span>
        {subscription.trial_days_remaining !== undefined && (
          <span className="ml-1 text-[10px] opacity-80">
            ({subscription.trial_days_remaining}d left)
          </span>
        )}
      </Badge>
    );
  }

  if (!subscription.is_active) {
    return (
      <Badge 
        variant="secondary" 
        className={cn(
          "gap-1 px-2.5 py-1 font-medium opacity-60",
          className
        )}
      >
        {showIcon && <Clock className="h-3 w-3" />}
        <span className="text-xs">Expired</span>
      </Badge>
    );
  }

  return null;
}
