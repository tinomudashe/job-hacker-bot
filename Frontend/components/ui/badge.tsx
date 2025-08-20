import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary/20 text-primary-foreground hover:bg-primary/30 backdrop-blur-sm",
        secondary:
          "border-transparent bg-secondary/20 text-secondary-foreground hover:bg-secondary/30 backdrop-blur-sm",
        destructive:
          "border-transparent bg-destructive/20 text-destructive-foreground hover:bg-destructive/30 backdrop-blur-sm",
        outline: "text-foreground border-white/10 backdrop-blur-sm",
        pro: "border border-blue-400/30 dark:border-blue-600/30 text-blue-600 dark:text-blue-400 bg-blue-500/10 dark:bg-blue-500/10 hover:bg-blue-500/20 dark:hover:bg-blue-500/20 shadow-sm",
        trial:
          "border border-amber-400/30 dark:border-amber-600/30 text-amber-600 dark:text-amber-400 bg-amber-500/10 dark:bg-amber-500/10 hover:bg-amber-500/20 dark:hover:bg-amber-500/20 shadow-sm",
        premium:
          "border border-purple-400/30 dark:border-purple-600/30 text-purple-600 dark:text-purple-400 bg-gradient-to-r from-purple-500/10 to-pink-500/10 hover:from-purple-500/20 hover:to-pink-500/20 shadow-sm",
        success:
          "border border-green-400/30 dark:border-green-600/30 text-green-600 dark:text-green-400 bg-green-500/10 dark:bg-green-500/10 hover:bg-green-500/20 dark:hover:bg-green-500/20 shadow-sm",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
