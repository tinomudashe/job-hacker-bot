"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogOverlay,
  DialogPortal,
} from "@/components/ui/dialog";
import { SignInButton, SignedIn, SignedOut, useAuth } from "@clerk/nextjs";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { 
  Check, 
  ShieldCheck, 
  Crown, 
  X, 
  Sparkles,
  Zap,
  TrendingUp,
  Award,
  Users,
  FileText,
  BrainCircuit,
  Clock
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

interface PricingDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const proFeatures = [
  {
    icon: <FileText className="w-4 h-4" />,
    title: "Unlimited Resume Generation",
    description: "Create and refine resumes without limits"
  },
  {
    icon: <Sparkles className="w-4 h-4" />,
    title: "Smart Cover Letters",
    description: "AI-powered personalized cover letters"
  },
  {
    icon: <Zap className="w-4 h-4" />,
    title: "ATS Optimization",
    description: "Beat applicant tracking systems"
  },
  {
    icon: <BrainCircuit className="w-4 h-4" />,
    title: "Interview Intelligence",
    description: "Comprehensive question library & coaching"
  },
  {
    icon: <TrendingUp className="w-4 h-4" />,
    title: "Skill Gap Analysis",
    description: "Identify and bridge career gaps"
  },
  {
    icon: <Users className="w-4 h-4" />,
    title: "Priority Support",
    description: "Get help when you need it most"
  },
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
        <DialogOverlay className="fixed inset-0 z-50 bg-black/50 dark:bg-black/70 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed left-[50%] top-[50%] z-50 w-[95vw] max-w-lg translate-x-[-50%] translate-y-[-50%] bg-background border border-border shadow-2xl rounded-2xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 flex flex-col overflow-hidden"
          onEscapeKeyDown={onClose}
        >
          {/* Close Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="absolute right-4 top-4 z-10 h-8 w-8 rounded-full"
          >
            <X className="h-4 w-4" />
          </Button>

          {/* Header */}
          <div className="p-8 pb-6 text-center border-b">
            <div className="flex items-center justify-center mb-4">
              <div className="p-3 bg-primary/10 rounded-2xl">
                <Crown className="h-8 w-8 text-primary" />
              </div>
            </div>
            
            <h2 className="text-2xl font-bold mb-2">
              JobHackerBot Pro
            </h2>
            <p className="text-muted-foreground text-sm">
              Unlock every feature to land your dream job
            </p>
          </div>

          {/* Pricing Section */}
          <div className="px-8 py-6 bg-muted/30 border-b">
            <div className="text-center">
              <div className="flex items-baseline justify-center gap-1">
                <span className="text-5xl font-bold">$2.99</span>
                <span className="text-lg text-muted-foreground">/ week</span>
              </div>
              <p className="mt-2 text-sm text-primary font-medium flex items-center justify-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                Start with 1-day free trial
              </p>
            </div>
          </div>

          {/* Features List */}
          <div className="flex-1 overflow-y-auto px-8 py-6 max-h-[40vh]">
            <div className="space-y-4">
              {proFeatures.map((feature, index) => (
                <div key={index} className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                    {feature.icon}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-sm">
                      {feature.title}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {feature.description}
                    </p>
                  </div>
                  <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                </div>
              ))}
            </div>
          </div>

          {/* Action Section */}
          <div className="px-8 py-6 bg-muted/30 border-t">
            <SignedIn>
              <Button
                className="w-full h-12 text-base font-semibold"
                onClick={handleCheckout}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-background/20 border-t-background rounded-full animate-spin mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Start Your 1-Day Free Trial
                  </>
                )}
              </Button>
            </SignedIn>
            
            <SignedOut>
              <div onClick={onClose}>
                <SignInButton mode="modal">
                  <Button className="w-full h-12 text-base font-semibold">
                    <Sparkles className="w-4 h-4 mr-2" />
                    Start Your 1-Day Free Trial
                  </Button>
                </SignInButton>
              </div>
            </SignedOut>

            {/* Trust Indicators */}
            <div className="mt-4 flex flex-col items-center gap-2">
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-green-500" />
                  <span>Secure Payment</span>
                </div>
                <div className="flex items-center gap-1">
                  <Award className="w-3.5 h-3.5 text-primary" />
                  <span>Cancel Anytime</span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground text-center">
                Billed weekly after trial. No hidden fees.
              </p>
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPortal>
    </Dialog>
  );
}