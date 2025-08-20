"use client";

import { useState, useMemo } from "react";
import { JobCard, Job } from "./job-card";
import { JobSkeleton } from "./job-skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Download,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { AnimatePresence } from "framer-motion";

interface JobListProps {
  jobs: Job[];
  loading?: boolean;
  title?: string;
  description?: string;
  onApply?: (job: Job) => void;
  onSave?: (job: Job) => void;
  onGenerateCoverLetter?: (job: Job) => void;
  onViewDetails?: (job: Job) => void;
  onRefresh?: () => void;
  onExport?: () => void;
  className?: string;
}

type SortBy = "date" | "salary" | "relevance" | "company";

export function JobList({
  jobs,
  loading = false,
  title,
  description,
  onApply,
  onSave,
  onGenerateCoverLetter,
  onViewDetails,
  onRefresh,
  onExport,
  className,
}: JobListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("date");
  const [currentPage, setCurrentPage] = useState(1);

  const itemsPerPage = 10;

  // Filter and sort jobs
  const filteredJobs = useMemo(() => {
    let filtered = [...jobs];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (job) =>
          job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          job.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
          job.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
          job.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Sort jobs
    switch (sortBy) {
      case "salary":
        filtered.sort((a, b) => {
          const salaryA = parseInt(a.salary?.replace(/\D/g, "") || "0");
          const salaryB = parseInt(b.salary?.replace(/\D/g, "") || "0");
          return salaryB - salaryA;
        });
        break;
      case "company":
        filtered.sort((a, b) => a.company.localeCompare(b.company));
        break;
      case "date":
      default:
        // Assuming newer jobs are at the beginning
        break;
    }

    return filtered;
  }, [jobs, searchQuery, sortBy]);

  // Pagination
  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);
  const paginatedJobs = filteredJobs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  if (loading) {
    return (
      <div className={cn("space-y-6", className)}>
        {title && (
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">{title}</h2>
            {description && (
              <p className="text-muted-foreground">{description}</p>
            )}
          </div>
        )}
        <div className="space-y-4">
          {[...Array(6)].map((_, i) => (
            <JobSkeleton key={i} variant="detailed" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      {(title || description) && (
        <div className="space-y-2">
          {title && <h2 className="text-2xl font-bold">{title}</h2>}
          {description && (
            <p className="text-muted-foreground">{description}</p>
          )}
        </div>
      )}

      {/* Stats Bar */}
      <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border">
        <div className="flex items-center gap-4">
          <Badge variant="secondary" className="gap-1">
            <TrendingUp className="h-3 w-3" />
            {filteredJobs.length} jobs found
          </Badge>
          {searchQuery && (
            <Badge variant="outline">
              Searching: "{searchQuery}"
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onRefresh && (
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
          )}
          {onExport && (
            <Button variant="ghost" size="sm" onClick={() => {
              // Generate CSV data
              const csvData = [
                ['Title', 'Company', 'Location', 'Type', 'Level', 'Salary', 'Posted', 'Link', 'Description'],
                ...filteredJobs.map(job => [
                  job.title,
                  job.company,
                  job.location,
                  job.type || '',
                  job.level || '',
                  job.salary || '',
                  job.posted || '',
                  job.url || '',
                  job.description?.replace(/,/g, ';') || ''
                ])
              ];
              
              // Convert to CSV string
              const csv = csvData.map(row => 
                row.map(cell => 
                  cell.includes(',') || cell.includes('\n') ? `"${cell.replace(/"/g, '""')}"` : cell
                ).join(',')
              ).join('\n');
              
              // Create blob and download
              const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
              const link = document.createElement('a');
              const url = URL.createObjectURL(blob);
              link.setAttribute('href', url);
              link.setAttribute('download', `jobs_export_${new Date().toISOString().split('T')[0]}.csv`);
              link.style.visibility = 'hidden';
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              
              onExport();
            }}>
              <Download className="h-4 w-4 mr-1" />
              Export CSV
            </Button>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="space-y-4">
        {/* Search and View Toggle */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 z-10 pointer-events-none">
              <Search className="h-5 w-5 text-foreground/70" />
            </div>
            <Input
              placeholder="Search jobs by title, company, or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-11"
            />
          </div>

          <div className="flex items-center gap-2">
            {/* Sort */}
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value as SortBy)}
              aria-label="Sort jobs by"
              className="flex h-10 w-[140px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="date">Latest</option>
              <option value="salary">Salary</option>
              <option value="relevance">Relevance</option>
              <option value="company">Company</option>
            </select>

          </div>
        </div>

      </div>

      {/* Job Cards */}
      {paginatedJobs.length > 0 ? (
        <>
          <div className="space-y-4">
            <AnimatePresence mode="popLayout">
              {paginatedJobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  variant="detailed"
                  onApply={onApply}
                  onSave={onSave}
                  onGenerateCoverLetter={onGenerateCoverLetter}
                  onViewDetails={onViewDetails}
                />
              ))}
            </AnimatePresence>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>

              <div className="flex items-center gap-1">
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  const pageNum = i + 1;
                  return (
                    <Button
                      key={pageNum}
                      variant={currentPage === pageNum ? "default" : "outline"}
                      size="sm"
                      onClick={() => setCurrentPage(pageNum)}
                      className="w-10"
                    >
                      {pageNum}
                    </Button>
                  );
                })}
                {totalPages > 5 && <span className="px-2">...</span>}
                {totalPages > 5 && (
                  <Button
                    variant={currentPage === totalPages ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentPage(totalPages)}
                    className="w-10"
                  >
                    {totalPages}
                  </Button>
                )}
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <p className="text-lg font-medium text-muted-foreground">
            No jobs found matching your criteria
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Try adjusting your filters or search query
          </p>
        </div>
      )}
    </div>
  );
}