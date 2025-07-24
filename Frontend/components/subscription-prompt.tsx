import { Button } from "@/components/ui/button";
import { useSubscription } from "@/lib/hooks/use-subscription";
import { AlertTriangle, Crown } from "lucide-react";

export const SubscriptionPrompt = () => {
  const { createCheckoutSession, loading, subscription } = useSubscription();
  const isPaymentFailed =
    subscription?.status === "past_due" || subscription?.status === "unpaid";

  return (
    <div className="flex items-center justify-center h-full p-4">
      <div className="w-full max-w-md text-center p-6 bg-background/60 rounded-2xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
        <div className="flex justify-center mb-4">
          <div
            className={`w-16 h-16 rounded-2xl border shadow-lg flex items-center justify-center ${
              isPaymentFailed
                ? "bg-red-100 border-red-200 dark:bg-red-500/20 dark:border-red-400/40"
                : "bg-blue-100 border-blue-200 dark:bg-blue-500/20 dark:border-blue-400/40"
            }`}
          >
            {isPaymentFailed ? (
              <AlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
            ) : (
              <Crown className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            )}
          </div>
        </div>
        <h2 className="text-2xl font-bold mb-2">
          {isPaymentFailed ? "Payment Failed" : "Unlock Features"}
        </h2>
        <p className="text-muted-foreground mb-6">
          {isPaymentFailed
            ? "Your subscription is inactive due to a payment issue. Please update your payment method to restore access."
            : "Your subscription is not active. Please subscribe to continue using all features of the app."}
        </p>
        <Button
          onClick={() => createCheckoutSession()}
          disabled={loading}
          className="w-full h-11 text-base font-medium"
        >
          {isPaymentFailed
            ? "Update Payment Method"
            : "Activate Your Subscription"}
        </Button>
      </div>
    </div>
  );
};
