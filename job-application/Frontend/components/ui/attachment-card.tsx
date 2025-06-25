"use client";

import { FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AttachmentCardProps {
  filename: string;
  filetype: string;
}

export function AttachmentCard({ filename, filetype }: AttachmentCardProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted text-muted-foreground max-w-xs">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
        <FileText className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold truncate text-foreground">{filename}</p>
        <p className="text-sm">{filetype}</p>
      </div>
    </div>
  );
} 