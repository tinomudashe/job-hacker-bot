"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  Building,
  MapPin,
  DollarSign,
  Clock,
  Briefcase,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  FileText,
  Users,
  Calendar,
  TrendingUp,
  Home,
  GraduationCap,
} from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

export interface Job {
  id: string;
  title: string;
  company: string;
  companyLogo?: string;
  location: string;
  salary?: string;
  type?: "Full-time" | "Part-time" | "Contract" | "Internship" | "Remote" | "Hybrid";
  level?: "Entry" | "Mid" | "Senior" | "Lead" | "Manager";
  description?: string;
  requirements?: string[];
  benefits?: string[];
  skills?: string[];
  posted?: string;
  deadline?: string;
  applicants?: number;
  url?: string;
  saved?: boolean;
  hasInterviewFlashcards?: boolean;
}

interface JobCardProps {
  job: Job;
  variant?: "compact" | "detailed" | "minimal";
  onApply?: (job: Job) => void;
  onSave?: (job: Job) => void;
  onGenerateCoverLetter?: (job: Job) => void;
  onViewDetails?: (job: Job) => void;
  className?: string;
}

export function JobCard({
  job,
  variant = "compact",
  onApply,
  onSave,
  onGenerateCoverLetter,
  onViewDetails,
  className,
}: JobCardProps) {
  const [isSaved, setIsSaved] = useState(job.saved || false);
  const [isHovered, setIsHovered] = useState(false);

  const handleSave = () => {
    setIsSaved(!isSaved);
    onSave?.(job);
  };

  const getTypeIcon = () => {
    switch (job.type) {
      case "Remote":
        return <Home className="h-4 w-4" />;
      case "Hybrid":
        return <Users className="h-4 w-4" />;
      default:
        return <Briefcase className="h-4 w-4" />;
    }
  };

  const getTypeColor = () => {
    switch (job.type) {
      case "Remote":
        return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300";
      case "Hybrid":
        return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300";
      case "Contract":
        return "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300";
      default:
        return "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300";
    }
  };

  const getLevelColor = () => {
    switch (job.level) {
      case "Entry":
        return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300";
      case "Senior":
      case "Lead":
        return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300";
      case "Manager":
        return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300";
      default:
        return "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300";
    }
  };

  if (variant === "minimal") {
    return (
      <motion.div
        whileHover={{ scale: 1.02 }}
        className={cn(
          "p-4 border rounded-lg hover:shadow-md transition-all cursor-pointer",
          "hover:border-primary/50 bg-card",
          className
        )}
        onClick={() => onViewDetails?.(job)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="font-semibold text-sm">{job.title}</h4>
            <p className="text-xs text-muted-foreground mt-1">{job.company}</p>
            <div className="flex items-center gap-2 mt-2">
              <MapPin className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs">{job.location}</span>
              {job.salary && (
                <>
                  <span className="text-muted-foreground">•</span>
                  <span className="text-xs font-medium">{job.salary}</span>
                </>
              )}
            </div>
          </div>
          <Badge variant="secondary" className="text-xs">
            {job.type}
          </Badge>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={cn(
          "transition-all duration-200",
          "hover:shadow-xl hover:border-primary/50",
          isHovered && "ring-2 ring-primary/20",
          className
        )}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              {/* Company Logo or Icon */}
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                {job.companyLogo ? (
                  <img
                    src={job.companyLogo}
                    alt={job.company}
                    className="w-8 h-8 object-contain"
                  />
                ) : (
                  <Building className="h-6 w-6 text-primary" />
                )}
              </div>

              {/* Job Title and Company */}
              <div className="flex-1">
                <h3 className="font-semibold text-lg leading-tight hover:text-primary transition-colors cursor-pointer"
                    onClick={() => onViewDetails?.(job)}>
                  {job.title}
                </h3>
                <p className="text-sm text-muted-foreground mt-1">{job.company}</p>
                
                {/* Location and Type */}
                <div className="flex flex-wrap items-center gap-2 mt-3">
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    <span>{job.location}</span>
                  </div>
                  
                  {job.type && (
                    <Badge
                      variant="secondary"
                      className={cn("gap-1", getTypeColor())}
                    >
                      {getTypeIcon()}
                      {job.type}
                    </Badge>
                  )}
                  
                  {job.level && (
                    <Badge
                      variant="secondary"
                      className={cn("gap-1", getLevelColor())}
                    >
                      <TrendingUp className="h-3 w-3" />
                      {job.level}
                    </Badge>
                  )}
                  
                  {job.hasInterviewFlashcards && (
                    <Badge 
                      variant="default" 
                      className="gap-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0 shadow-sm"
                    >
                      <GraduationCap className="h-3 w-3" />
                      <span className="text-xs">Interview Prep</span>
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Save Button */}
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0"
              onClick={handleSave}
            >
              {isSaved ? (
                <BookmarkCheck className="h-5 w-5 text-primary fill-primary" />
              ) : (
                <Bookmark className="h-5 w-5" />
              )}
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pb-4">
          {/* Salary and Posted Date */}
          <div className="flex flex-wrap items-center gap-4 text-sm">
            {job.salary && (
              <div className="flex items-center gap-1 text-green-600 dark:text-green-400 font-medium">
                <DollarSign className="h-4 w-4" />
                <span>{job.salary}</span>
              </div>
            )}
            
            {job.posted && (
              <div className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>{job.posted}</span>
              </div>
            )}
            
            {job.applicants && (
              <div className="flex items-center gap-1 text-muted-foreground">
                <Users className="h-4 w-4" />
                <span>{job.applicants} applicants</span>
              </div>
            )}

            {job.deadline && (
              <div className="flex items-center gap-1 text-orange-600 dark:text-orange-400">
                <Calendar className="h-4 w-4" />
                <span>Deadline: {job.deadline}</span>
              </div>
            )}
          </div>

          {/* Skills */}
          {job.skills && job.skills.length > 0 && variant === "detailed" && (
            <div className="mt-4">
              <p className="text-sm font-medium mb-2">Required Skills:</p>
              <div className="flex flex-wrap gap-2">
                {job.skills.slice(0, 5).map((skill, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))}
                {job.skills.length > 5 && (
                  <Badge variant="outline" className="text-xs">
                    +{job.skills.length - 5} more
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* Description Preview */}
          {job.description && variant === "detailed" && (
            <div className="mt-4">
              <p className="text-sm text-muted-foreground line-clamp-3">
                {job.description}
              </p>
            </div>
          )}
        </CardContent>

        <CardFooter className="p-4 border-t bg-muted/10">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              {onGenerateCoverLetter && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onGenerateCoverLetter(job)}
                  className="gap-1.5"
                >
                  <FileText className="h-4 w-4" />
                  Cover Letter
                </Button>
              )}
              
              {onViewDetails && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onViewDetails(job)}
                >
                  View Details
                </Button>
              )}
            </div>

            {onApply && job.url && (
              <Button
                size="sm"
                onClick={() => onApply(job)}
                className="gap-1.5"
              >
                <ExternalLink className="h-4 w-4" />
                Apply Now
              </Button>
            )}
          </div>
        </CardFooter>
      </Card>
    </motion.div>
  );
}