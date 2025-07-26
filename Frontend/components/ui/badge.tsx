import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
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
        pro: "bg-blue-50/95 dark:bg-blue-950/95 border-blue-200/70 dark:border-blue-800/70 text-blue-700 dark:text-blue-400 shadow-sm",
        trial:
          "bg-amber-50/95 dark:bg-amber-950/95 border-amber-200/70 dark:border-amber-800/70 text-amber-700 dark:text-amber-400 shadow-sm",
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
