"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@clerk/nextjs";
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
import { toast } from "sonner";

interface CVSuggestion {
  id: string;
  section: string;
  type: string;
  title: string;
  description: string;
  target_text: string;
  suggested_text: string;
  priority: string;
  reasoning: string;
  color: string;
}

interface CVSuggestionsPanelProps {
  jobTitle: string;
  jobDescription?: string;
  onSuggestionApplied?: () => void;
  className?: string;
}

export function CVSuggestionsPanel({ 
  jobTitle, 
  jobDescription = "", 
  onSuggestionApplied,
  className = ""
}: CVSuggestionsPanelProps) {
  const { getToken } = useAuth();
  const [suggestions, setSuggestions] = React.useState<CVSuggestion[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [appliedSuggestions, setAppliedSuggestions] = React.useState<Set<string>>(new Set());
  const [applyingIds, setApplyingIds] = React.useState<Set<string>>(new Set());

  // Fetch suggestions when component mounts or job details change
  React.useEffect(() => {
    if (jobTitle) {
      fetchSuggestions();
    }
  }, [jobTitle, jobDescription]);

  const fetchSuggestions = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/cv/analyze-suggestions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          job_title: jobTitle,
          job_description: jobDescription
        })
      });

      if (!response.ok) {
        throw new Error("Failed to fetch suggestions");
      }

      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error("Error fetching suggestions:", error);
      toast.error("Failed to load suggestions");
    } finally {
      setLoading(false);
    }
  };

  const applySuggestion = async (suggestion: CVSuggestion) => {
    setApplyingIds(prev => new Set([...prev, suggestion.id]));
    
    try {
      const token = await getToken();
      const response = await fetch("/api/cv/apply-suggestion", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          suggestion_id: suggestion.id,
          new_text: suggestion.suggested_text,
          section: suggestion.section
        })
      });

      if (!response.ok) {
        throw new Error("Failed to apply suggestion");
      }

      // Mark as applied
      setAppliedSuggestions(prev => new Set([...prev, suggestion.id]));
      toast.success("Suggestion applied successfully");
      
      // Notify parent component
      onSuggestionApplied?.();
      
    } catch (error) {
      console.error("Error applying suggestion:", error);
      toast.error("Failed to apply suggestion");
    } finally {
      setApplyingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(suggestion.id);
        return newSet;
      });
    }
  };

  const dismissSuggestion = (suggestionId: string) => {
    setSuggestions(prev => prev.filter(s => s.id !== suggestionId));
  };

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'red':
        return {
          border: 'border-red-200',
          bg: 'bg-red-50',
          text: 'text-red-700',
          badge: 'bg-red-100 text-red-700',
          icon: <AlertCircle className="h-4 w-4 text-red-500" />
        };
      case 'blue':
        return {
          border: 'border-blue-200',
          bg: 'bg-blue-50', 
          text: 'text-blue-700',
          badge: 'bg-blue-100 text-blue-700',
          icon: <Lightbulb className="h-4 w-4 text-blue-500" />
        };
      case 'green':
        return {
          border: 'border-green-200',
          bg: 'bg-green-50',
          text: 'text-green-700', 
          badge: 'bg-green-100 text-green-700',
          icon: <Plus className="h-4 w-4 text-green-500" />
        };
      case 'purple':
        return {
          border: 'border-purple-200',
          bg: 'bg-purple-50',
          text: 'text-purple-700',
          badge: 'bg-purple-100 text-purple-700', 
          icon: <ArrowUpDown className="h-4 w-4 text-purple-500" />
        };
      default:
        return {
          border: 'border-gray-200',
          bg: 'bg-gray-50',
          text: 'text-gray-700',
          badge: 'bg-gray-100 text-gray-700',
          icon: <Lightbulb className="h-4 w-4 text-gray-500" />
        };
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      case 'medium':
        return <Lightbulb className="h-3 w-3 text-yellow-500" />;
      default:
        return <CheckCircle className="h-3 w-3 text-green-500" />;
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">Analyzing CV for improvements...</p>
        </div>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return (
      <div className={`text-center p-8 ${className}`}>
        <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">CV Looks Great!</h3>
        <p className="text-muted-foreground">
          No major improvements needed for this {jobTitle} role.
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">CV Improvement Suggestions</h3>
        <Badge variant="outline" className="text-xs">
          {suggestions.length} suggestions
        </Badge>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {suggestions.map((suggestion) => {
          const colorClasses = getColorClasses(suggestion.color);
          const isApplied = appliedSuggestions.has(suggestion.id);
          const isApplying = applyingIds.has(suggestion.id);

          return (
            <Card 
              key={suggestion.id} 
              className={`${colorClasses.border} ${colorClasses.bg} transition-all ${
                isApplied ? 'opacity-50' : ''
              }`}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {colorClasses.icon}
                    <CardTitle className={`text-sm ${colorClasses.text}`}>
                      {suggestion.title}
                    </CardTitle>
                    {getPriorityIcon(suggestion.priority)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Badge 
                      variant="outline" 
                      className={`text-xs ${colorClasses.badge} border-transparent`}
                    >
                      {suggestion.section}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => dismissSuggestion(suggestion.id)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-muted-foreground mb-3">
                  {suggestion.description}
                </p>
                
                {/* Show original vs suggested text */}
                <div className="space-y-2 mb-3">
                  <div className="text-xs text-muted-foreground">Current:</div>
                  <div className="bg-gray-100 p-2 rounded text-sm border">
                    {suggestion.target_text}
                  </div>
                  <div className="text-xs text-muted-foreground">Suggested:</div>
                  <div className={`${colorClasses.bg} p-2 rounded text-sm border ${colorClasses.border}`}>
                    {suggestion.suggested_text}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => applySuggestion(suggestion)}
                    disabled={isApplied || isApplying}
                    className="flex-1"
                  >
                    {isApplying ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                        Applying...
                      </>
                    ) : isApplied ? (
                      <>
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Applied
                      </>
                    ) : (
                      "Apply Suggestion"
                    )}
                  </Button>
                </div>

                {suggestion.reasoning && (
                  <p className="text-xs text-muted-foreground mt-2 italic">
                    💡 {suggestion.reasoning}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {suggestions.some(s => !appliedSuggestions.has(s.id)) && (
        <div className="border-t pt-4">
          <Button
            onClick={() => {
              suggestions
                .filter(s => !appliedSuggestions.has(s.id))
                .forEach(applySuggestion);
            }}
            className="w-full"
            variant="outline"
          >
            Apply All Remaining Suggestions
          </Button>
        </div>
      )}
    </div>
  );
}