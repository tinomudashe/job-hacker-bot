import { useAuth } from "@clerk/nextjs";
import * as React from "react";
import { toast } from "sonner";

export interface SubscriptionState {
  plan: string;
  status: string;
  period_end?: string;
}

export const useSubscription = () => {
  const { getToken } = useAuth();
  const [subscription, setSubscription] =
    React.useState<SubscriptionState | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [portalLoading, setPortalLoading] = React.useState(false);

  const fetchSubscription = React.useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/billing/subscription", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Could not fetch subscription status");
      const data = await response.json();
      setSubscription(data);
    } catch (error) {
      console.error("Failed to fetch subscription", error);
      setSubscription(null);
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  React.useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  const createCheckoutSession = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/billing/create-checkout-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const { url } = await response.json();
        window.location.href = url;
      } else {
        toast.error("Failed to create checkout session.");
      }
    } catch (error) {
      console.error("Failed to create checkout session:", error);
      toast.error("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const createPortalSession = async () => {
    setPortalLoading(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/billing/create-portal-session", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const { url } = await response.json();
        window.location.href = url;
      } else {
        toast.error("Could not open billing management.");
      }
    } catch (error) {
      console.error("Failed to create portal session:", error);
      toast.error("An error occurred. Please try again.");
    } finally {
      setPortalLoading(false);
    }
  };

  return {
    subscription,
    loading,
    fetchSubscription,
    createCheckoutSession,
    createPortalSession,
    portalLoading,
  };
};
