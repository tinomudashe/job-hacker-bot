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
        pro: "border-transparent bg-gradient-to-r from-purple-500 to-pink-500 text-primary-foreground shadow-lg shadow-purple-500/30",
        trial:
          "border-transparent bg-gradient-to-r from-yellow-400 to-orange-500 text-primary-foreground shadow-lg shadow-orange-500/30",
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
