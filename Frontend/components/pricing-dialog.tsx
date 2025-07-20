"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
} from "@/components/ui/dialog";
import { SignInButton, SignedIn, SignedOut, useAuth } from "@clerk/nextjs";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Check, ShieldCheck, Tag, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

interface PricingDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const proFeatures = [
  "Unlimited Resume Generations",
  "Unlimited Cover Letter Generations",
  "Advanced ATS Optimization",
  "Full Interview Question Library",
  "Smart Interview Coaching",
  "In-depth Skill Gap Analysis",
  "Priority Support",
];

export function PricingDialog({ isOpen, onClose }: PricingDialogProps) {
  const { getToken } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleCheckout = async () => {
    onClose();
    setIsLoading(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/billing/create-checkout-session", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to create checkout session");
      }

      const { url } = await response.json();
      router.push(url);
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error("An unexpected error occurred. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogPortal>
        <DialogOverlay className="fixed inset-0 z-50 bg-black/70 dark:bg-black/80 backdrop-blur-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed left-[50%] top-[50%] z-50 w-[92vw] max-w-md translate-x-[-50%] translate-y-[-50%] !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 shadow-2xl rounded-3xl !border !border-gray-200 dark:!border-white/8 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 flex flex-col"
          onEscapeKeyDown={onClose}
        >
          {/* Header */}
          <DialogHeader className="flex-shrink-0 flex-row items-center justify-between p-5 rounded-t-3xl !border-b !border-gray-200 dark:!border-white/8 !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150">
            <DialogTitle className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl !bg-blue-100 !border !border-blue-200 shadow-lg dark:!bg-blue-500/20 dark:!border-blue-500/40">
                <Tag className="h-5 w-5 !text-blue-600 dark:!text-blue-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  JobHackerBot Pro
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 -mt-0.5 font-normal">
                  Unlock every feature to land your dream job.
                </p>
              </div>
            </DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-9 w-9 rounded-xl transition-all duration-200 hover:scale-105 !bg-gray-100 !border !border-gray-200 hover:!bg-gray-200 dark:!bg-background/60 dark:!border-white/8 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:hover:!bg-background/80"
            >
              <X className="h-4 w-4" />
            </Button>
          </DialogHeader>

          {/* Content */}
          <div className="p-6 flex-1 overflow-y-auto">
            <div className="text-center mb-6">
              <p className="text-4xl font-bold">
                $2.99
                <span className="text-lg font-normal text-muted-foreground">
                  / week
                </span>
              </p>
            </div>

            {/* Floating Features Card */}
            <div className="p-5 rounded-2xl !bg-white/60 dark:!bg-black/20 !border !border-gray-200/80 dark:!border-white/10 shadow-md mb-6">
              <ul className="space-y-3">
                {proFeatures.map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-sm font-medium">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
            <SignedIn>
              <Button
                className="w-full h-12 text-lg font-semibold bg-blue-600 hover:bg-blue-700 rounded-xl"
                onClick={handleCheckout}
                disabled={isLoading}
              >
                {isLoading ? "Processing..." : "Start Your 1-Day Free Trial"}
              </Button>
            </SignedIn>
            <SignedOut>
              <div onClick={onClose}>
                <SignInButton mode="modal">
                  <Button className="w-full h-12 text-lg font-semibold bg-blue-600 hover:bg-blue-700 rounded-xl">
                    Start Your 1-Day Free Trial
                  </Button>
                </SignInButton>
              </div>
            </SignedOut>

            <div className="mt-4 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Cancel anytime. Your subscription is secure.</span>
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPortal>
    </Dialog>
  );
}
