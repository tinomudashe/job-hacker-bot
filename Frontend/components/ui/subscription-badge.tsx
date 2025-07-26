import { Badge } from "@/components/ui/badge";

interface Subscription {
  plan: string;
  is_active: boolean;
}

interface SubscriptionBadgeProps {
  subscription: Subscription | null;
}

export function SubscriptionBadge({ subscription }: SubscriptionBadgeProps) {
  if (!subscription) {
    return null;
  }

  if (subscription.plan === "pro" && subscription.is_active) {
    return (
      <Badge variant="pro" className="ml-2">
        Pro
      </Badge>
    );
  }

  if (subscription.plan === "trial" && subscription.is_active) {
    return (
      <Badge variant="trial" className="ml-2">
        Trial
      </Badge>
    );
  }

  return (
    <Badge variant="destructive" className="ml-2">
      Inactive
    </Badge>
  );
}
