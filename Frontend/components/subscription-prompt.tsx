import { Button } from "@/components/ui/button";
import { useSubscription } from "@/lib/hooks/use-subscription";
import { Crown } from "lucide-react";

export const SubscriptionPrompt = () => {
  const { createCheckoutSession, loading } = useSubscription();

  return (
    <div className="flex items-center justify-center h-full p-4">
      <div className="w-full max-w-md text-center p-6 bg-background/60 rounded-2xl shadow-2xl border border-white/8 backdrop-blur-xl backdrop-saturate-150">
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-2xl bg-blue-100 border border-blue-200 shadow-lg dark:bg-blue-500/20 dark:border-blue-400/40 flex items-center justify-center">
            <Crown className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
        <h2 className="text-2xl font-bold mb-2">Unlock Pro Features</h2>
        <p className="text-muted-foreground mb-6">
          Your subscription is not active. Please subscribe to continue using
          the app.
        </p>
        <Button
          onClick={() => createCheckoutSession()}
          disabled={loading}
          className="w-full h-11 text-base font-medium"
        >
          Subscribe to Pro
        </Button>
      </div>
    </div>
  );
};
