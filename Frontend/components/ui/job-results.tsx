"use client"

import { cn } from "@/lib/utils"
import { Button } from "./button"
import { Badge } from "./badge"
import { ExternalLink, MapPin, Building, DollarSign, Clock, Copy, Check, Search, Lightbulb } from "lucide-react"
import { useState } from "react"

interface JobResult {
  title: string
  company: string
  location: string
  description: string
  apply_url?: string
  job_type?: string
  salary_range?: string
}

interface JobSearchResponse {
  search_query: string
  location: string
  total_jobs: number
  jobs: JobResult[]
}

interface JobResultsProps {
  results: string | JobSearchResponse
  className?: string
}

export function JobResults({ results, className }: JobResultsProps) {
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);
  
  // Parse the results if it's a JSON string
  let jobData: JobSearchResponse
  
  try {
    if (typeof results === 'string') {
      jobData = JSON.parse(results)
    } else {
      jobData = results
    }
  } catch (error) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <p>Unable to parse job results. Please try again.</p>
      </div>
    )
  }

  if (!jobData.jobs || jobData.jobs.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <p>No jobs found for "{jobData.search_query}" in {jobData.location}.</p>
        <p className="text-sm mt-1">Try different keywords or expand your search area.</p>
      </div>
    )
  }

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl(null), 2000);
  };

  const handleApply = (job: JobResult) => {
    if (job.apply_url) {
      window.open(job.apply_url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Search Summary */}
      <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-xl border border-blue-200 dark:border-blue-800">
        <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
          <Search className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <span className="text-foreground">Job Search Results</span>
        </h3>
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            Query: {jobData.search_query}
          </span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            Location: {jobData.location}
          </span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 border border-green-200 dark:border-green-800">
            Found: {jobData.total_jobs} jobs
          </span>
        </div>
      </div>

      {/* Job Listings */}
      <div className="space-y-10">
        {jobData.jobs.map((job, index) => (
          <>
            <div
              key={index}
              className="p-6 border border-border rounded-xl hover:shadow-lg transition-all duration-200 bg-card hover:border-primary/50"
            >
              {/* Job Header */}
              <div className="flex justify-between items-start mb-6">
                <div className="flex-1">
                  <h4 className="font-bold text-xl text-foreground mb-3 group-hover:text-primary transition-colors">
                    {job.title}
                  </h4>
                  <div className="flex items-center gap-2 text-muted-foreground mb-4">
                    <Building className="h-5 w-5 text-primary" />
                    <span className="font-semibold text-lg">{job.company}</span>
                  </div>
                </div>
              </div>

              {/* Job Details */}
              <div className="flex flex-wrap gap-4 mb-6">
                {job.location && (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-950/30 rounded-full">
                    <MapPin className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-800 dark:text-blue-200">{job.location}</span>
                  </div>
                )}
                
                {job.salary_range && (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-950/30 rounded-full">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800 dark:text-green-200">{job.salary_range}</span>
                  </div>
                )}
                
                {job.job_type && (
                  <Badge variant="outline" className="border-purple-200 text-purple-700 dark:border-purple-700 dark:text-purple-300">
                    {job.job_type}
                  </Badge>
                )}
              </div>

              {/* Job Description */}
              {job.description && (
                <div className="mb-6 p-6 bg-muted/30 rounded-xl border border-border/30">
                  <p className="text-sm text-muted-foreground leading-7 whitespace-pre-line">{job.description}</p>
                </div>
              )}

              {/* Apply Section */}
              <div className="flex items-center justify-between pt-6 border-t border-border/50">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>Posted recently</span>
                </div>
                
                <div className="flex items-center gap-2">
                  {job.apply_url && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopyUrl(job.apply_url!)}
                        className="gap-2"
                      >
                        {copiedUrl === job.apply_url ? (
                          <>
                            <Check className="h-4 w-4 text-green-600" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4" />
                            Copy Link
                          </>
                        )}
                      </Button>
                      
                      <Button
                        onClick={() => handleApply(job)}
                        className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
                      >
                        <ExternalLink className="h-4 w-4" />
                        Apply Now
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </div>
            {/* Add separator between jobs except for the last one */}
            {index < jobData.jobs.length - 1 && (
              <div className="flex items-center justify-center py-4">
                <div className="w-full max-w-xs h-px bg-gradient-to-r from-transparent via-border to-transparent"></div>
              </div>
            )}
          </>
        ))}
      </div>

      {/* Footer */}
      <div className="text-center p-4 bg-muted/20 rounded-xl border border-border/30">
        <p className="text-xs text-muted-foreground flex items-center justify-center gap-2">
          <Lightbulb className="h-3 w-3" />
          <span><strong>Tip:</strong> Click "Apply Now" to visit the company's job posting page, or "Copy Link" to save for later</span>
        </p>
      </div>
    </div>
  )
}

// Helper function to extract job results from AI responses
export function extractJobResults(text: string): JobSearchResponse | null {
  try {
    // Look for JSON blocks in the text
    const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/) || 
                     text.match(/\{[\s\S]*"jobs"[\s\S]*\}/);
    
    if (jsonMatch) {
      const jsonStr = jsonMatch[1] || jsonMatch[0];
      return JSON.parse(jsonStr);
    }
    
    // Try to parse the entire text as JSON
    return JSON.parse(text);
  } catch {
    return null;
  }
} 