"use client";

import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { InlineSuggestionWrapper } from "./inline-suggestion";
import * as React from "react";

interface CVTextWithSuggestionsProps {
  value: string;
  onChange: (value: string) => void;
  suggestions?: Array<{
    id: string;
    type: string;
    title: string;
    description: string;
    target_text: string;
    suggested_text: string;
    priority: string;
    reasoning: string;
    color: string;
  }>;
  onSuggestionApplied?: () => void;
  placeholder?: string;
  className?: string;
  multiline?: boolean;
}

export function CVTextWithSuggestions({
  value,
  onChange,
  suggestions = [],
  onSuggestionApplied,
  placeholder,
  className = "",
  multiline = false
}: CVTextWithSuggestionsProps) {
  const [showSuggestions, setShowSuggestions] = React.useState(true);

  // Find suggestions that apply to current text
  const applicableSuggestions = suggestions.filter(s => 
    value.toLowerCase().includes(s.target_text.toLowerCase())
  );

  const applySuggestion = (newText: string) => {
    onChange(newText);
    onSuggestionApplied?.();
  };

  const dismissSuggestion = (suggestionId: string) => {
    // Remove from local suggestions or handle dismissal
  };

  // If no suggestions, render normal input
  if (!showSuggestions || applicableSuggestions.length === 0) {
    if (multiline) {
      return (
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={className}
        />
      );
    } else {
      return (
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={className}
        />
      );
    }
  }

  // Render text with inline suggestions
  const renderTextWithSuggestions = () => {
    let result = value;
    let renderedElements: React.ReactNode[] = [];
    let lastIndex = 0;

    // Sort suggestions by position in text
    const sortedSuggestions = applicableSuggestions.sort((a, b) => {
      const aIndex = value.toLowerCase().indexOf(a.target_text.toLowerCase());
      const bIndex = value.toLowerCase().indexOf(b.target_text.toLowerCase());
      return aIndex - bIndex;
    });

    sortedSuggestions.forEach((suggestion, index) => {
      const targetIndex = value.toLowerCase().indexOf(suggestion.target_text.toLowerCase(), lastIndex);
      
      if (targetIndex !== -1) {
        // Add text before suggestion
        if (targetIndex > lastIndex) {
          renderedElements.push(
            <span key={`text-${index}`}>
              {value.substring(lastIndex, targetIndex)}
            </span>
          );
        }

        // Add suggestion wrapper
        renderedElements.push(
          <InlineSuggestionWrapper
            key={suggestion.id}
            originalText={suggestion.target_text}
            suggestion={suggestion}
            onApply={applySuggestion}
            onDismiss={() => dismissSuggestion(suggestion.id)}
          />
        );

        lastIndex = targetIndex + suggestion.target_text.length;
      }
    });

    // Add remaining text
    if (lastIndex < value.length) {
      renderedElements.push(
        <span key="text-end">
          {value.substring(lastIndex)}
        </span>
      );
    }

    return renderedElements;
  };

  // For multiline text (like summaries, descriptions)
  if (multiline) {
    return (
      <div className={`relative ${className}`}>
        {/* Hidden textarea for functionality */}
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="opacity-0 absolute inset-0 z-10"
        />
        
        {/* Visible text with suggestions overlay */}
        <div className="min-h-[80px] p-3 border border-input rounded-md bg-background text-sm leading-relaxed">
          {renderTextWithSuggestions()}
        </div>
      </div>
    );
  }

  // For single line text (like job titles, names)
  return (
    <div className={`relative ${className}`}>
      {/* Hidden input for functionality */}
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="opacity-0 absolute inset-0 z-10"
      />
      
      {/* Visible text with suggestions overlay */}
      <div className="h-10 px-3 py-2 border border-input rounded-md bg-background text-sm flex items-center">
        {renderTextWithSuggestions()}
      </div>
    </div>
  );
}