"use client";

import { Button } from "@/components/ui/button";
import { SignIn } from "@clerk/nextjs";
import { X } from "lucide-react";
import { useRouter } from "next/navigation";
import { EmbeddedBrowserWarning } from "@/components/embedded-browser-warning";

export default function SignInPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <Button
        aria-label="Close"
        variant="ghost"
        size="icon"
        onClick={() => router.push("/")}
        className="absolute top-4 right-4 h-9 w-9 rounded-xl transition-all duration-200 hover:scale-105 !bg-gray-100 !border !border-gray-200 hover:!bg-gray-200 dark:!bg-background/60 dark:!border-white/8 dark:hover:!bg-background/80"
      >
        <X className="h-4 w-4" />
      </Button>
      <EmbeddedBrowserWarning />
      <div className="mt-4 flex items-center text-sm text-gray-500">
        <SignIn 
          routing="path"
          path="/sign-in"
          signUpUrl="/sign-up"
          appearance={{
            elements: {
              rootBox: "w-full",
              card: "shadow-none",
            },
          }}
        />
      </div>
    </div>
  );
}
