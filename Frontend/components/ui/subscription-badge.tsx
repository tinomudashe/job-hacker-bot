import { Badge } from "@/components/ui/badge";
import { Crown, Star } from "lucide-react";

interface SubscriptionBadgeProps {
  status: "trialing" | "active" | string;
}

export const SubscriptionBadge = ({ status }: SubscriptionBadgeProps) => {
  if (status !== "trialing" && status !== "active") {
    return null;
  }

  const isTrial = status === "trialing";

  return (
    <Badge
      variant="outline"
      className="py-0.5 px-1.5 border-blue-400/30 bg-background/60 text-blue-400 backdrop-blur-xl backdrop-saturate-150 text-[10px] font-bold"
    >
      {isTrial ? (
        <Star className="h-2.5 w-2.5 mr-1" />
      ) : (
        <Crown className="h-2.5 w-2.5 mr-1" />
      )}
      {isTrial ? "TRIAL" : "PRO"}
    </Badge>
  );
};
