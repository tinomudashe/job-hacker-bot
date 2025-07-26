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
        pro: "border-blue-700/50 bg-blue-950 text-blue-300 shadow-sm shadow-blue-500/10",
        trial:
          "border-amber-700/50 bg-amber-950 text-amber-300 shadow-sm shadow-amber-500/10",
        active:
          "border-green-700/50 bg-green-950 text-green-300 shadow-sm shadow-green-500/10",
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
