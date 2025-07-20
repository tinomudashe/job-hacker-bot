"use client";

import { cn } from "@/lib/utils";
import * as React from "react";
import * as RechartsPrimitive from "recharts";

// --- Type Definitions ---
export type ChartConfig = {
  [k in string]: {
    label?: React.ReactNode;
    icon?: React.ComponentType;
    color?: string;
  };
};

// --- Chart Container ---
const ChartContainer = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    config: ChartConfig;
    children: React.ReactNode;
  }
>(({ config, className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex aspect-video justify-center text-xs",
      "[&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground",
      "[&_.recharts-cartesian-grid_line]:stroke-border/50",
      "[&_.recharts-tooltip-content]:rounded-md [&_.recharts-tooltip-content]:border [&_.recharts-tooltip-content]:bg-popover [&_.recharts-tooltip-content]:text-popover-foreground",
      className
    )}
    {...props}
  >
    <RechartsPrimitive.ResponsiveContainer>
      {children}
    </RechartsPrimitive.ResponsiveContainer>
  </div>
));
ChartContainer.displayName = "ChartContainer";

// --- Chart Tooltip ---
const ChartTooltip = RechartsPrimitive.Tooltip;

const ChartTooltipContent = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<typeof RechartsPrimitive.TooltipContent>
>(({ label, payload, className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-background/95 p-2.5 shadow-sm backdrop-blur-sm",
      className
    )}
  >
    <div className="font-medium">{label}</div>
    {(payload ?? []).map((item) => (
      <div key={item.dataKey} className="flex items-center gap-2">
        {item.color && (
          <div
            className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
            style={{ backgroundColor: item.color }}
          />
        )}
        <div className="flex flex-1 justify-between gap-4">
          <span className="text-muted-foreground">{item.name}</span>
          <span>{item.value}</span>
        </div>
      </div>
    ))}
  </div>
));
ChartTooltipContent.displayName = "ChartTooltipContent";

export { ChartContainer, ChartTooltip, ChartTooltipContent };
