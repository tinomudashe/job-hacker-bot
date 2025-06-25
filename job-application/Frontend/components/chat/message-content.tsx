"use client";

import React from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AttachmentCard } from '@/components/ui/attachment-card';

interface MessageContentProps {
  content: any;
}

export function MessageContent({ content }: MessageContentProps) {
  if (!content) return null;

  const text = typeof content === 'string' ? content : content.message || '';

  if (typeof text === 'string' && text.startsWith('Attached file:')) {
    const filename = text.replace('Attached file: ', '');
    const filetype = filename.split('.').pop()?.toUpperCase() || '';
    return <AttachmentCard filename={filename} filetype={filetype} />;
  }

  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]}>
      {text}
    </ReactMarkdown>
  );
} 