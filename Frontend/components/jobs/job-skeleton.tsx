"use client";

import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface JobSkeletonProps {
  variant?: "compact" | "detailed" | "minimal";
  className?: string;
}

export function JobSkeleton({ variant = "compact", className }: JobSkeletonProps) {
  if (variant === "minimal") {
    return (
      <div className={cn("p-4 border rounded-lg", className)}>
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
            <div className="flex items-center gap-2 mt-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
      </div>
    );
  }

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {/* Company Logo Skeleton */}
            <Skeleton className="w-12 h-12 rounded-lg shrink-0" />

            {/* Job Title and Company */}
            <div className="flex-1 space-y-2">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              
              {/* Location and Type */}
              <div className="flex items-center gap-2 mt-3">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-20 rounded-full" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            </div>
          </div>

          {/* Save Button Skeleton */}
          <Skeleton className="w-9 h-9 rounded-lg" />
        </div>
      </CardHeader>

      <CardContent className="pb-4">
        {/* Salary and Posted Date */}
        <div className="flex items-center gap-4">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-28" />
        </div>

        {/* Skills - only for detailed variant */}
        {variant === "detailed" && (
          <div className="mt-4 space-y-2">
            <Skeleton className="h-4 w-24" />
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-6 w-16 rounded-full" />
              <Skeleton className="h-6 w-20 rounded-full" />
              <Skeleton className="h-6 w-14 rounded-full" />
              <Skeleton className="h-6 w-18 rounded-full" />
              <Skeleton className="h-6 w-12 rounded-full" />
            </div>
          </div>
        )}

        {/* Description Preview - only for detailed variant */}
        {variant === "detailed" && (
          <div className="mt-4 space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-4 border-t bg-muted/20">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Skeleton className="h-8 w-24 rounded-md" />
            <Skeleton className="h-8 w-20 rounded-md" />
          </div>
          <Skeleton className="h-8 w-24 rounded-md" />
        </div>
      </CardFooter>
    </Card>
  );
}