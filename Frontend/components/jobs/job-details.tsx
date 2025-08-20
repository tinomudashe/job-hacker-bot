"use client";

import { Job } from "./job-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
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
  CheckCircle,
  Info,
  Gift,
  Target,
  Share2,
  Copy,
  Check,
  GraduationCap,
  Sparkles,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface JobDetailsProps {
  job: Job | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApply?: (job: Job) => void;
  onSave?: (job: Job) => void;
  onGenerateCoverLetter?: (job: Job) => void;
  className?: string;
}

export function JobDetails({
  job,
  open,
  onOpenChange,
  onApply,
  onSave,
  onGenerateCoverLetter,
  className,
}: JobDetailsProps) {
  const [copied, setCopied] = useState(false);

  if (!job) return null;

  const handleCopyUrl = () => {
    const url = job.url || window.location.href;
    navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success("Job URL copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleApply = () => {
    if (job.url) {
      window.open(job.url, "_blank", "noopener,noreferrer");
      onApply?.(job);
    }
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn("w-[50vw] max-w-[50vw] max-h-[90vh]", className)}>
        <DialogHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4 flex-1">
              {/* Company Logo */}
              <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                {job.companyLogo ? (
                  <img
                    src={job.companyLogo}
                    alt={job.company}
                    className="w-12 h-12 object-contain"
                  />
                ) : (
                  <Building className="h-8 w-8 text-primary" />
                )}
              </div>

              {/* Job Title and Company */}
              <div className="flex-1">
                <DialogTitle className="text-2xl font-bold mb-2">
                  {job.title}
                </DialogTitle>
                <DialogDescription className="text-base">
                  <span className="font-semibold text-foreground">
                    {job.company}
                  </span>
                </DialogDescription>

                {/* Location and Type Badges */}
                <div className="flex flex-wrap items-center gap-2 mt-3">
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    <span>{job.location}</span>
                  </div>

                  {job.type && (
                    <Badge variant="secondary" className="gap-1">
                      {getTypeIcon()}
                      {job.type}
                    </Badge>
                  )}

                  {job.level && (
                    <Badge variant="secondary" className="gap-1">
                      <TrendingUp className="h-3 w-3" />
                      {job.level}
                    </Badge>
                  )}
                  
                  {job.hasInterviewFlashcards && (
                    <Badge 
                      variant="default" 
                      className="gap-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0"
                    >
                      <GraduationCap className="h-3 w-3" />
                      Interview Prep Available
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={handleCopyUrl}
                title="Copy job URL"
              >
                {copied ? (
                  <Check className="h-5 w-5 text-green-600" />
                ) : (
                  <Copy className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-6">
            {/* Key Information */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {job.salary && (
                <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
                  <DollarSign className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="text-xs text-muted-foreground">Salary</p>
                    <p className="text-sm font-semibold">{job.salary}</p>
                  </div>
                </div>
              )}

              {job.posted && (
                <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <Clock className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-xs text-muted-foreground">Posted</p>
                    <p className="text-sm font-semibold">{job.posted}</p>
                  </div>
                </div>
              )}

              {job.deadline && (
                <div className="flex items-center gap-2 p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
                  <Calendar className="h-5 w-5 text-orange-600" />
                  <div>
                    <p className="text-xs text-muted-foreground">Deadline</p>
                    <p className="text-sm font-semibold">{job.deadline}</p>
                  </div>
                </div>
              )}

              {job.applicants && (
                <div className="flex items-center gap-2 p-3 bg-purple-50 dark:bg-purple-950/20 rounded-lg border border-purple-200 dark:border-purple-800">
                  <Users className="h-5 w-5 text-purple-600" />
                  <div>
                    <p className="text-xs text-muted-foreground">Applicants</p>
                    <p className="text-sm font-semibold">{job.applicants}</p>
                  </div>
                </div>
              )}
            </div>

            <Separator />

            {/* Job Description */}
            {job.description && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-primary" />
                  <h3 className="font-semibold text-lg">Job Description</h3>
                </div>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                    {job.description}
                  </p>
                </div>
              </div>
            )}

            {/* Requirements */}
            {job.requirements && job.requirements.length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Target className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold text-lg">Requirements</h3>
                  </div>
                  <ul className="space-y-2">
                    {job.requirements.map((req, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                        <span className="text-sm text-muted-foreground">
                          {req}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}

            {/* Required Skills */}
            {job.skills && job.skills.length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold text-lg">Required Skills</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {job.skills.map((skill, index) => (
                      <Badge key={index} variant="secondary">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Benefits */}
            {job.benefits && job.benefits.length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Gift className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold text-lg">Benefits</h3>
                  </div>
                  <ul className="space-y-2">
                    {job.benefits.map((benefit, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />
                        <span className="text-sm text-muted-foreground">
                          {benefit}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
        </ScrollArea>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-6 border-t">
          <div className="flex items-center gap-2">
            {onGenerateCoverLetter && (
              <Button
                variant="outline"
                onClick={() => {
                  onGenerateCoverLetter(job);
                  onOpenChange(false);
                }}
                className="gap-2"
              >
                <FileText className="h-4 w-4" />
                Generate Cover Letter
              </Button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
            {job.url && (
              <Button onClick={handleApply} className="gap-2">
                <ExternalLink className="h-4 w-4" />
                Apply Now
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}