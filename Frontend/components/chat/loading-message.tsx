"use client";

import { cn } from '@/lib/utils';

export function LoadingMessage() {
  return (
    <div className="flex items-center gap-2 py-4">
      <div className="flex items-center justify-center gap-1.5">
        <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.3s]" />
        <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.15s]" />
        <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" />
      </div>
    </div>
  );
} 