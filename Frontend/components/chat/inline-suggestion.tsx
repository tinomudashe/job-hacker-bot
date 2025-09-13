"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  AlertCircle, 
  CheckCircle, 
  Lightbulb, 
  ArrowUpDown, 
  Plus,
  Loader2,
  X
} from "lucide-react";
import * as React from "react";

interface InlineSuggestion {
  id: string;
  type: string;
  title: string;
  description: string;
  suggested_text: string;
  priority: string;
  reasoning: string;
  color: string;
}

interface InlineSuggestionProps {
  originalText: string;
  suggestion: InlineSuggestion;
  onApply: (newText: string) => void;
  onDismiss: () => void;
  className?: string;
}

export function InlineSuggestionWrapper({ 
  originalText, 
  suggestion, 
  onApply, 
  onDismiss,
  className = ""
}: InlineSuggestionProps) {
  const [showCard, setShowCard] = React.useState(false);
  const [isApplying, setIsApplying] = React.useState(false);
  const [isApplied, setIsApplied] = React.useState(false);

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'red':
        return {
          underline: 'border-b-2 border-red-400 border-dashed',
          card: 'border-red-200 bg-red-50',
          text: 'text-red-700',
          badge: 'bg-red-100 text-red-600',
          icon: <AlertCircle className="h-4 w-4 text-red-500" />
        };
      case 'blue':
        return {
          underline: 'border-b-2 border-blue-400 border-dashed',
          card: 'border-blue-200 bg-blue-50', 
          text: 'text-blue-700',
          badge: 'bg-blue-100 text-blue-600',
          icon: <Lightbulb className="h-4 w-4 text-blue-500" />
        };
      case 'green':
        return {
          underline: 'border-b-2 border-green-400 border-dashed',
          card: 'border-green-200 bg-green-50',
          text: 'text-green-700', 
          badge: 'bg-green-100 text-green-600',
          icon: <Plus className="h-4 w-4 text-green-500" />
        };
      case 'purple':
        return {
          underline: 'border-b-2 border-purple-400 border-dashed',
          card: 'border-purple-200 bg-purple-50',
          text: 'text-purple-700',
          badge: 'bg-purple-100 text-purple-600', 
          icon: <ArrowUpDown className="h-4 w-4 text-purple-500" />
        };
      default:
        return {
          underline: 'border-b-2 border-gray-400 border-dashed',
          card: 'border-gray-200 bg-gray-50',
          text: 'text-gray-700',
          badge: 'bg-gray-100 text-gray-600',
          icon: <Lightbulb className="h-4 w-4 text-gray-500" />
        };
    }
  };

  const colorClasses = getColorClasses(suggestion.color);

  const handleApply = async () => {
    setIsApplying(true);
    try {
      await onApply(suggestion.suggested_text);
      setIsApplied(true);
      setShowCard(false);
    } catch (error) {
      console.error("Error applying suggestion:", error);
    } finally {
      setIsApplying(false);
    }
  };

  if (isApplied) {
    return (
      <span className={`${className}`}>
        {suggestion.suggested_text}
      </span>
    );
  }

  return (
    <span className={`relative inline-block ${className}`}>
      {/* Underlined text that triggers suggestion */}
      <span
        className={`cursor-pointer ${colorClasses.underline} hover:bg-yellow-100/50 transition-colors`}
        onClick={() => setShowCard(!showCard)}
        onMouseEnter={() => setShowCard(true)}
        onMouseLeave={() => setTimeout(() => setShowCard(false), 200)}
      >
        {originalText}
      </span>

      {/* Suggestion card - positioned absolutely */}
      {showCard && (
        <div className="absolute z-50 top-full left-0 mt-2 w-80 max-w-sm">
          <Card 
            className={`${colorClasses.card} ${colorClasses.card} shadow-lg border-2`}
            onMouseEnter={() => setShowCard(true)}
            onMouseLeave={() => setShowCard(false)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {colorClasses.icon}
                  <span className={`font-semibold text-sm ${colorClasses.text}`}>
                    {suggestion.title}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${colorClasses.badge} border-transparent`}
                  >
                    {suggestion.priority}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-5 w-5 p-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDismiss();
                      setShowCard(false);
                    }}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              </div>

              <p className="text-sm text-muted-foreground mb-3">
                {suggestion.description}
              </p>
              
              {/* Show suggested change */}
              <div className="space-y-2 mb-3">
                <div className="text-xs font-medium text-muted-foreground">Suggested:</div>
                <div className={`${colorClasses.card} p-2 rounded text-sm border border-dashed`}>
                  {suggestion.suggested_text}
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleApply}
                  disabled={isApplying}
                  className="flex-1"
                >
                  {isApplying ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                      Applying...
                    </>
                  ) : (
                    "Apply"
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    onDismiss();
                    setShowCard(false);
                  }}
                  className="px-3"
                >
                  Dismiss
                </Button>
              </div>

              {suggestion.reasoning && (
                <p className="text-xs text-muted-foreground mt-2 italic">
                  💡 {suggestion.reasoning}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </span>
  );
}

// Hook to manage suggestions for a CV section
export function useCVSuggestions(jobTitle: string, jobDescription: string = "") {
  const [suggestions, setSuggestions] = React.useState<InlineSuggestion[]>([]);
  const [loading, setLoading] = React.useState(false);

  const fetchSuggestions = React.useCallback(async () => {
    if (!jobTitle) return;
    
    setLoading(true);
    try {
      // This would call the backend API we created
      // For now, return empty array until we integrate the API
      setSuggestions([]);
    } catch (error) {
      console.error("Error fetching suggestions:", error);
    } finally {
      setLoading(false);
    }
  }, [jobTitle, jobDescription]);

  React.useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  return {
    suggestions,
    loading,
    refetchSuggestions: fetchSuggestions
  };
}