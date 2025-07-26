import { useAuth } from "@clerk/nextjs";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

interface Subscription {
  plan: string;
  is_active: boolean;
}

export function useSubscription() {
  const { getToken } = useAuth();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);

  const fetchSubscription = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/billing/subscription", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error("Failed to fetch subscription status");
      }
      const data = await response.json();
      setSubscription(data);
    } catch (error) {
      console.error("Failed to fetch subscription:", error);
      setSubscription({ plan: "free", is_active: false });
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  // --- DEFINITIVE FIX: This function will be passed to the WebSocket hook ---
  // It allows the WebSocket to directly update this central state.
  const updateSubscription = useCallback((isActive: boolean, plan: string) => {
    console.log("Updating subscription state from WebSocket:", {
      isActive,
      plan,
    });
    setSubscription({ is_active: isActive, plan: plan });
  }, []);

  const createCheckoutSession = useCallback(async () => {
    if (subscription?.plan === "premium" && subscription?.is_active) {
      toast.info("You are already subscribed to the premium plan.");
      return;
    }
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
  }, [getToken, subscription]);

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
    portalLoading,
    createCheckoutSession,
    createPortalSession,
    updateSubscription, // Expose the new update function
    fetchSubscription, // --- FIX: Expose the fetch function ---
  };
}
