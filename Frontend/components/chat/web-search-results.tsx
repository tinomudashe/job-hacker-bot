"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Globe, Search, ExternalLink, Sparkles, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface WebSearchResultsProps {
  content: string;
  className?: string;
}

export function WebSearchResults({ content, className }: WebSearchResultsProps) {
  // Parse the content to extract search query and results
  const parseSearchContent = () => {
    const lines = content.split('\n').filter(line => line.trim());
    
    let query = '';
    const results: Array<{ title: string; content: string; url?: string }> = [];
    let applicationSection = '';
    let isInResults = false;
    let isInApplication = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Extract search query
      if (line.includes('Latest Information on:') || line.includes('**Latest Information on:')) {
        query = line.replace(/\*\*/g, '').replace('Latest Information on:', '').replace('🌐', '').trim();
      }
      
      // Start of results section
      if (line.includes('Based on current web search results:') || line.includes('search results:')) {
        isInResults = true;
        isInApplication = false;
        continue;
      }
      
      // Start of application section
      if (line.includes('How this applies') || line.includes('💡')) {
        isInResults = false;
        isInApplication = true;
        applicationSection = lines.slice(i + 1).join('\n').replace(/💡/g, '').trim();
        break;
      }
      
      // Process search results
      if (isInResults) {
        // Check if this is a title (usually bold or starts with **)
        if (line.startsWith('**') && line.endsWith('**')) {
          const title = line.replace(/\*\*/g, '').trim();
          // Get the content (next few lines until another title or section)
          let resultContent = '';
          for (let j = i + 1; j < lines.length; j++) {
            if (lines[j].startsWith('**') || lines[j].includes('How this applies')) {
              break;
            }
            resultContent += lines[j] + ' ';
          }
          results.push({ 
            title, 
            content: resultContent.trim(),
            url: extractUrl(title)
          });
        }
      }
    }
    
    return { query, results, applicationSection };
  };
  
  // Extract URL from title if it contains domain
  const extractUrl = (title: string) => {
    const domainMatch = title.match(/\| ([^\s]+\.[^\s]+)$/);
    if (domainMatch) {
      return `https://${domainMatch[1]}`;
    }
    return undefined;
  };
  
  const { query, results, applicationSection } = parseSearchContent();
  
  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center gap-3 pb-2 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30">
          <Globe className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Web Search Results
          </h3>
          {query && (
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
              {query}
            </p>
          )}
        </div>
      </div>
      
      {/* Search Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
            <Search className="h-3.5 w-3.5" />
            <span>Based on current web search results:</span>
          </div>
          
          <div className="space-y-3">
            {results.map((result, index) => (
              <Card 
                key={index} 
                className="border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
              >
                <CardContent className="p-4">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 leading-tight">
                        {result.title.replace(/\|.*$/, '').trim()}
                      </h4>
                      {result.url && (
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                    
                    {result.content && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        {result.content}
                      </p>
                    )}
                    
                    {result.url && (
                      <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-500">
                        <span className="truncate">{result.url.replace('https://', '')}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
      
      {/* Application Section */}
      {applicationSection && (
        <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white dark:bg-gray-800 shadow-sm">
              <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex-1 space-y-2">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                How this applies to your situation
              </h4>
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                {applicationSection}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}