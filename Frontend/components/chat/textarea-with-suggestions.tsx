"use client";

import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  AlertCircle, 
  Lightbulb, 
  Plus,
  ArrowUpDown,
  X,
  CheckCircle,
  ArrowRight,
  Zap
} from "lucide-react";
import * as React from "react";

interface SuggestionOverlayProps {
  suggestions: Array<{
    id: string;
    title: string;
    description: string;
    suggested_text: string;
    color: string;
    target_text: string;
  }>;
  onApply: (suggestionId: string, newText: string) => void;
  onDismiss: (suggestionId: string) => void;
  currentValue: string;
}

function SuggestionOverlay({ suggestions, onApply, onDismiss, currentValue }: SuggestionOverlayProps) {
  if (!suggestions.length) return null;

  return (
    <div className="absolute top-full left-0 right-0 z-50 mt-4 space-y-3 max-w-full">
      {suggestions.slice(0, 2).map((suggestion) => { // Limit to 2 suggestions to avoid clutter
        const getColorClasses = (color: string) => {
          switch (color) {
            case 'red': 
              return { 
                bg: 'bg-red-50 dark:bg-red-900/20', 
                border: 'border-red-200 dark:border-red-500/30', 
                text: 'text-red-700 dark:text-red-300', 
                icon: <AlertCircle className="h-4 w-4 text-red-500 dark:text-red-400" /> 
              };
            case 'blue': 
              return { 
                bg: 'bg-blue-50 dark:bg-blue-900/20', 
                border: 'border-blue-200 dark:border-blue-500/30', 
                text: 'text-blue-700 dark:text-blue-300', 
                icon: <Lightbulb className="h-4 w-4 text-blue-500 dark:text-blue-400" /> 
              };
            case 'green': 
              return { 
                bg: 'bg-green-50 dark:bg-green-900/20', 
                border: 'border-green-200 dark:border-green-500/30', 
                text: 'text-green-700 dark:text-green-300', 
                icon: <Plus className="h-4 w-4 text-green-500 dark:text-green-400" /> 
              };
            case 'purple': 
              return { 
                bg: 'bg-purple-50 dark:bg-purple-900/20', 
                border: 'border-purple-200 dark:border-purple-500/30', 
                text: 'text-purple-700 dark:text-purple-300', 
                icon: <ArrowUpDown className="h-4 w-4 text-purple-500 dark:text-purple-400" /> 
              };
            default: 
              return { 
                bg: 'bg-gray-50 dark:bg-background/70', 
                border: 'border-gray-200 dark:border-white/20', 
                text: 'text-gray-700 dark:text-gray-300', 
                icon: <Lightbulb className="h-4 w-4 text-gray-500 dark:text-gray-400" /> 
              };
          }
        };

        const colors = getColorClasses(suggestion.color);

        return (
          <div key={suggestion.id} className={`!border !border-gray-200 dark:!border-white/20 rounded-xl p-4 sm:p-6 !bg-gray-50 dark:!bg-background/70 backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-200 group ${colors.border}`}>
            {/* Header with suggestion type and action */}
            <div className="p-3 sm:p-4 border-b border-gray-200/50 dark:border-white/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {colors.icon}
                  <span className={`font-semibold text-sm ${colors.text}`}>
                    {suggestion.title}
                  </span>
                  <Badge className="text-xs bg-white/50 dark:bg-black/20 text-gray-600 dark:text-gray-400 border-0">
                    {suggestion.color} priority
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0 hover:bg-white/30 dark:hover:bg-black/20 rounded-md"
                  onClick={() => onDismiss(suggestion.id)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>

            {/* Content with before/after comparison */}
            <div className="p-3 sm:p-4">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                {suggestion.description}
              </p>
              
              {/* Before/After comparison */}
              <div className="space-y-2 mb-4">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400">Current:</div>
                <div className="bg-gray-100 dark:bg-gray-800/50 p-2 rounded-lg text-xs border border-dashed border-gray-300 dark:border-gray-600">
                  <span className="line-through text-gray-500 dark:text-gray-400">{suggestion.target_text || "..."}</span>
                </div>
                
                <div className="flex items-center gap-1 text-xs font-medium text-gray-500 dark:text-gray-400">
                  <ArrowRight className="h-3 w-3" />
                  <span>Suggested:</span>
                </div>
                <div className={`${colors.bg} p-2 rounded-lg text-xs border border-dashed ${colors.border}`}>
                  <span className="font-medium">{suggestion.suggested_text}</span>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => onApply(suggestion.id, suggestion.suggested_text)}
                  className="flex-1 h-8 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium transition-all duration-200 hover:scale-[1.02]"
                >
                  <Zap className="h-3 w-3 mr-1" />
                  Apply
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onDismiss(suggestion.id)}
                  className="px-3 h-8 rounded-lg text-xs hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-all duration-200"
                >
                  Skip
                </Button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface TextareaWithSuggestionsProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  suggestions?: Array<{
    id: string;
    title: string;
    description: string;
    suggested_text: string;
    color: string;
    target_text: string;
    section: string;
  }>;
  appliedSuggestions?: Set<string>;
  appliedSuggestionHistory?: Array<{id: string, originalText: string, newText: string, section: string}>;
  onApplySuggestion?: (suggestionId: string, newText: string, currentText: string) => void;
  onRevertSuggestion?: (suggestionId: string) => void;
  placeholder?: string;
  className?: string;
  rows?: number;
  sectionName: string; // Which section this textarea represents
  style?: React.CSSProperties;
}

// Component to render text with inline markings
function TextWithMarkings({ 
  text, 
  suggestions,
  onSuggestionClick 
}: { 
  text: string; 
  suggestions: any[];
  onSuggestionClick: (suggestion: any) => void;
}) {
  if (!suggestions.length) {
    return <span>{text}</span>;
  }

  const renderMarkedText = () => {
    let result: React.ReactNode[] = [];
    let lastIndex = 0;

    // Sort suggestions by position in text
    const sortedSuggestions = suggestions
      .filter(s => s.target_text && text.toLowerCase().includes(s.target_text.toLowerCase()))
      .sort((a, b) => {
        const aIndex = text.toLowerCase().indexOf(a.target_text.toLowerCase());
        const bIndex = text.toLowerCase().indexOf(b.target_text.toLowerCase());
        return aIndex - bIndex;
      });

    sortedSuggestions.forEach((suggestion, index) => {
      const targetText = suggestion.target_text;
      const startIndex = text.toLowerCase().indexOf(targetText.toLowerCase(), lastIndex);
      
      if (startIndex !== -1) {
        // Add text before suggestion
        if (startIndex > lastIndex) {
          result.push(
            <span key={`text-${index}`}>
              {text.substring(lastIndex, startIndex)}
            </span>
          );
        }

        // Add marked text based on suggestion type
        const getMarkingClass = (color: string, type: string) => {
          const baseClasses = "cursor-pointer transition-all duration-200 hover:opacity-80";
          switch (color) {
            case 'red':
              return `${baseClasses} border-b-2 border-red-400 border-dashed bg-red-100/50 dark:bg-red-900/20`;
            case 'blue':
              return `${baseClasses} border-b-2 border-blue-400 border-dashed bg-blue-100/50 dark:bg-blue-900/20`;
            case 'green':
              return `${baseClasses} bg-green-100/70 dark:bg-green-900/30 border border-green-300 dark:border-green-600 rounded px-1`;
            case 'purple':
              return `${baseClasses} border-b-2 border-purple-400 border-dotted bg-purple-100/50 dark:bg-purple-900/20`;
            default:
              return `${baseClasses} border-b border-gray-400 border-dashed`;
          }
        };

        result.push(
          <span
            key={suggestion.id}
            className={getMarkingClass(suggestion.color, suggestion.type)}
            onClick={() => onSuggestionClick(suggestion)}
            title={suggestion.title}
          >
            {text.substring(startIndex, startIndex + targetText.length)}
          </span>
        );

        lastIndex = startIndex + targetText.length;
      }
    });

    // Add remaining text
    if (lastIndex < text.length) {
      result.push(
        <span key="text-end">
          {text.substring(lastIndex)}
        </span>
      );
    }

    return result;
  };

  return <div className="leading-relaxed">{renderMarkedText()}</div>;
}

export function TextareaWithSuggestions({
  value,
  onChange,
  suggestions = [],
  appliedSuggestions = new Set(),
  appliedSuggestionHistory = [],
  onApplySuggestion,
  onRevertSuggestion,
  placeholder,
  className,
  rows = 4,
  sectionName,
  style
}: TextareaWithSuggestionsProps) {
  const [userHasEdited, setUserHasEdited] = React.useState(false);
  const [originalValue] = React.useState(value);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  
  // Filter suggestions for this specific section and exclude already applied ones
  const sectionSuggestions = suggestions
    .filter(s => s.section === sectionName)
    .filter(s => !appliedSuggestions.has(s.id));
  
  // Track manual edits
  React.useEffect(() => {
    if (value !== originalValue && value.trim() !== originalValue.trim()) {
      setUserHasEdited(true);
    }
  }, [value, originalValue]);
  
  const handleApplySuggestion = (suggestionId: string, newText: string) => {
    const currentText = value;
    onApplySuggestion?.(suggestionId, newText, currentText);
    setUserHasEdited(false); // Reset edit flag since this is an intended change
  };

  const handleRevertSuggestion = (suggestionId: string) => {
    onRevertSuggestion?.(suggestionId);
    setUserHasEdited(false); // Reset edit flag
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e);
    // Only mark as edited if it's different from suggestions
    const isApplyingSuggestion = sectionSuggestions.some(s => 
      s.suggested_text === e.target.value
    );
    if (!isApplyingSuggestion) {
      setUserHasEdited(true);
    }
  };

  return (
    <div className="space-y-3">
      {/* Main textarea with overlay markings */}
      <div className="relative">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={handleTextareaChange}
          placeholder={placeholder}
          className={className}
          rows={rows}
          style={style}
        />
        
        
        {/* AI Enhancement indicator - shows both pending suggestions and applied count */}
        <div className="absolute bottom-2 right-2 flex gap-1 z-30">
          {/* Applied suggestions indicator */}
          {appliedSuggestionHistory.length > 0 && (
            <div className="inline-flex items-center gap-1.5 px-2 sm:px-3 py-1 sm:py-2 rounded-full text-xs font-medium !bg-white dark:!bg-background/70 backdrop-blur-md text-green-700 dark:text-green-300 !border !border-green-200 dark:!border-green-500/40 shadow-sm">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span>{appliedSuggestionHistory.length} applied</span>
            </div>
          )}
          
          {/* Pending suggestions indicator */}
          {sectionSuggestions.length > 0 && (
            <div className="inline-flex items-center gap-1.5 px-2 sm:px-3 py-1 sm:py-2 rounded-full text-xs font-medium !bg-white dark:!bg-background/70 backdrop-blur-md text-blue-700 dark:text-blue-300 !border !border-blue-200 dark:!border-blue-500/40 shadow-sm">
              <Lightbulb className="h-3 w-3 text-blue-500" />
              <span>{sectionSuggestions.length} pending</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Applied suggestions indicator for this section - matches app theme */}
      {appliedSuggestionHistory.filter(h => h.section === sectionName).length > 0 && (
        <div className="!border !border-gray-200 dark:!border-white/20 rounded-xl p-4 sm:p-6 !bg-gray-50 dark:!bg-background/70 backdrop-blur-md shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 sm:gap-3">
              <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-600 dark:text-green-400" />
              <span className="text-sm sm:text-base font-semibold text-gray-700 dark:text-gray-300">
                AI Suggestions Applied ({appliedSuggestionHistory.filter(h => h.section === sectionName).length})
              </span>
            </div>
          </div>
          
          <div className="space-y-2 sm:space-y-3">
            {appliedSuggestionHistory
              .filter(h => h.section === sectionName)
              .map((historyItem) => {
                const suggestion = suggestions.find(s => s.id === historyItem.id);
                return (
                  <div key={historyItem.id} className="flex items-center justify-between !bg-white dark:!bg-background/60 rounded-xl p-3 sm:p-4 !border !border-gray-200 dark:!border-white/8 shadow-sm group">
                    <div className="flex items-center gap-2 sm:gap-3 flex-1">
                      <CheckCircle className="h-3 w-3 sm:h-4 sm:w-4 text-green-500 dark:text-green-400" />
                      <span className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 font-medium truncate">
                        {suggestion?.title || "Suggestion applied"}
                      </span>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleRevertSuggestion(historyItem.id)}
                      className="h-6 sm:h-8 px-2 sm:px-3 text-xs text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:!bg-red-50 dark:hover:!bg-red-900/20 transition-all duration-200 rounded-lg"
                    >
                      Revert
                    </Button>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* User edit notification */}
      {userHasEdited && sectionSuggestions.length > 0 && (
        <div className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-500/30">
          <AlertCircle className="h-3 w-3" />
          Content has been manually edited. Suggestions below may no longer match.
        </div>
      )}
      
      {/* Suggestion cards displayed below textarea */}
      {sectionSuggestions.length > 0 && (
        <div className="space-y-3">
          {sectionSuggestions.slice(0, 3).map((suggestion) => {
            const getColorClasses = (color: string) => {
              switch (color) {
                case 'red': 
                  return { 
                    bg: 'bg-red-50 dark:bg-red-900/20', 
                    border: 'border-red-200 dark:border-red-500/30', 
                    text: 'text-red-700 dark:text-red-300', 
                    icon: <AlertCircle className="h-4 w-4 text-red-500 dark:text-red-400" /> 
                  };
                case 'blue': 
                  return { 
                    bg: 'bg-blue-50 dark:bg-blue-900/20', 
                    border: 'border-blue-200 dark:border-blue-500/30', 
                    text: 'text-blue-700 dark:text-blue-300', 
                    icon: <Lightbulb className="h-4 w-4 text-blue-500 dark:text-blue-400" /> 
                  };
                case 'green': 
                  return { 
                    bg: 'bg-green-50 dark:bg-green-900/20', 
                    border: 'border-green-200 dark:border-green-500/30', 
                    text: 'text-green-700 dark:text-green-300', 
                    icon: <Plus className="h-4 w-4 text-green-500 dark:text-green-400" /> 
                  };
                case 'purple': 
                  return { 
                    bg: 'bg-purple-50 dark:bg-purple-900/20', 
                    border: 'border-purple-200 dark:border-purple-500/30', 
                    text: 'text-purple-700 dark:text-purple-300', 
                    icon: <ArrowUpDown className="h-4 w-4 text-purple-500 dark:text-purple-400" /> 
                  };
                default: 
                  return { 
                    bg: 'bg-gray-50 dark:bg-background/70', 
                    border: 'border-gray-200 dark:border-white/20', 
                    text: 'text-gray-700 dark:text-gray-300', 
                    icon: <Lightbulb className="h-4 w-4 text-gray-500 dark:text-gray-400" /> 
                  };
              }
            };

            const colors = getColorClasses(suggestion.color);

            return (
              <Card key={suggestion.id} className={`${colors.bg} ${colors.border} backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-200 border-2 rounded-xl overflow-hidden`}>
                {/* Header */}
                <div className="p-3 border-b border-gray-200/50 dark:border-white/10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {colors.icon}
                      <span className={`font-semibold text-sm ${colors.text}`}>
                        {suggestion.title}
                      </span>
                    </div>
                    <Badge className="text-xs bg-white/50 dark:bg-black/20 text-gray-600 dark:text-gray-400 border-0">
                      {suggestion.color}
                    </Badge>
                  </div>
                </div>

                {/* Content */}
                <div className="p-3">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 leading-relaxed">
                    {suggestion.description}
                  </p>
                  
                  {/* Before/After comparison */}
                  <div className="space-y-2 mb-3">
                    <div className="bg-gray-100 dark:bg-gray-800/50 p-2 rounded text-xs border border-dashed border-gray-300 dark:border-gray-600">
                      <div className="text-gray-500 dark:text-gray-400 mb-1 font-medium">Current:</div>
                      <span className="line-through text-gray-600 dark:text-gray-300">{suggestion.target_text || "No specific text targeted"}</span>
                    </div>
                    
                    <div className="flex items-center gap-1 text-xs">
                      <ArrowRight className="h-3 w-3 text-gray-400" />
                      <span className="text-gray-500 dark:text-gray-400 font-medium">Suggested improvement:</span>
                    </div>
                    
                    <div className={`${colors.bg} p-2 rounded text-xs border border-dashed ${colors.border}`}>
                      <span className="font-medium text-gray-800 dark:text-gray-200">{suggestion.suggested_text}</span>
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleApplySuggestion(suggestion.id, suggestion.suggested_text)}
                      className="flex-1 h-8 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium transition-all duration-200 hover:scale-[1.02]"
                    >
                      <Zap className="h-3 w-3 mr-1" />
                      Apply
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        // Mark as dismissed by calling the apply handler with empty text
                        // This will track it as "applied" but without changing content
                        console.log("Skipped suggestion:", suggestion.id);
                      }}
                      className="px-3 h-8 rounded-lg text-xs hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-all duration-200"
                    >
                      Skip
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}