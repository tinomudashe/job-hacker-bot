"use client";

import { useState, useEffect } from "react";
import { JobList } from "./job-list";
import { JobDetails } from "./job-details";
import { Job } from "./job-card";
import { toast } from "sonner";

interface JobDisplayProps {
  data: any; // Raw data from WebSocket/API
  onGenerateCoverLetter?: (job: Job) => void;
  onSendMessage?: (message: string) => void;
  onRegenerateLastMessage?: () => void;
  className?: string;
}

export function JobDisplay({ data, onGenerateCoverLetter, onSendMessage, onRegenerateLastMessage, className }: JobDisplayProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [loading] = useState(false);
  const [title, setTitle] = useState<string>("");
  const [description, setDescription] = useState<string>("");

  useEffect(() => {
    // Parse the job data from various formats
    if (data) {
      try {
        let jobData: any;
        
        // Handle string data
        if (typeof data === "string") {
          // Try to parse as JSON
          try {
            jobData = JSON.parse(data);
          } catch {
            // If not JSON, look for JSON within the string
            const jsonMatch = data.match(/\{[\s\S]*"jobs"[\s\S]*\}/) || 
                            data.match(/```json\s*([\s\S]*?)\s*```/);
            if (jsonMatch) {
              const jsonStr = jsonMatch[1] || jsonMatch[0];
              jobData = JSON.parse(jsonStr);
            }
          }
        } else {
          jobData = data;
        }

        // Extract jobs array
        if (jobData?.jobs && Array.isArray(jobData.jobs)) {
          const formattedJobs: Job[] = jobData.jobs.map((job: any, index: number) => ({
            id: job.id || `job-${index}`,
            title: job.title || job.job_title || "Untitled Position",
            company: job.company || job.company_name || "Unknown Company",
            companyLogo: job.logo || job.company_logo,
            location: job.location || job.job_location || "Location not specified",
            salary: job.salary || job.salary_range || job.compensation,
            type: job.type || job.job_type || job.employment_type,
            level: job.level || job.experience_level || job.seniority,
            description: job.description || job.job_description || job.summary,
            requirements: job.requirements || job.qualifications,
            benefits: job.benefits || job.perks,
            skills: job.skills || job.required_skills || job.technologies,
            posted: job.posted || job.posted_date || job.date_posted,
            deadline: job.deadline || job.application_deadline,
            applicants: job.applicants || job.applicant_count,
            url: job.url || job.apply_url || job.link || job.application_link,
            saved: false,
            hasInterviewFlashcards: job.hasInterviewFlashcards || job.interview_flashcards_available || false,
          }));

          setJobs(formattedJobs);
          
          // Set title and description if available
          if (jobData.search_query || jobData.query) {
            setTitle(`Jobs for "${jobData.search_query || jobData.query}"`);
          }
          if (jobData.location) {
            setDescription(`Found ${formattedJobs.length} opportunities in ${jobData.location}`);
          } else if (jobData.total_jobs) {
            setDescription(`Showing ${formattedJobs.length} of ${jobData.total_jobs} total jobs`);
          }
        }
        // Handle single job object
        else if (jobData?.title || jobData?.job_title) {
          const singleJob: Job = {
            id: jobData.id || "single-job",
            title: jobData.title || jobData.job_title,
            company: jobData.company || jobData.company_name,
            companyLogo: jobData.logo || jobData.company_logo,
            location: jobData.location || jobData.job_location,
            salary: jobData.salary || jobData.salary_range,
            type: jobData.type || jobData.job_type,
            level: jobData.level || jobData.experience_level,
            description: jobData.description || jobData.job_description,
            requirements: jobData.requirements,
            benefits: jobData.benefits,
            skills: jobData.skills || jobData.required_skills,
            posted: jobData.posted || jobData.posted_date,
            deadline: jobData.deadline,
            applicants: jobData.applicants,
            url: jobData.url || jobData.apply_url,
            saved: false,
            hasInterviewFlashcards: jobData.hasInterviewFlashcards || jobData.interview_flashcards_available || false,
          };
          setJobs([singleJob]);
          setTitle("Job Opportunity");
        }
      } catch (error) {
        console.error("Error parsing job data:", error);
        toast.error("Failed to parse job data");
      }
    }
  }, [data]);

  const handleApply = (job: Job) => {
    if (job.url) {
      window.open(job.url, "_blank", "noopener,noreferrer");
      toast.success(`Opening application for ${job.title}`);
    } else {
      toast.error("No application URL available");
    }
  };

  const handleSave = (job: Job) => {
    // Update the job's saved status
    setJobs((prevJobs) =>
      prevJobs.map((j) =>
        j.id === job.id ? { ...j, saved: !j.saved } : j
      )
    );
  };

  const handleViewDetails = (job: Job) => {
    setSelectedJob(job);
    setDetailsOpen(true);
  };

  const handleGenerateCoverLetter = (job: Job) => {
    if (onSendMessage && job.url) {
      // Send a message to create a cover letter for this job
      const message = `Create a cover letter for this job: ${job.url}`;
      onSendMessage(message);
      toast.success("Generating cover letter...");
    } else if (onGenerateCoverLetter) {
      onGenerateCoverLetter(job);
      toast.success("Generating cover letter...");
    }
  };

  const handleRefresh = () => {
    if (onRegenerateLastMessage) {
      onRegenerateLastMessage();
      toast.info("Refreshing job listings...");
    } else {
      toast.info("Refresh function not available");
    }
  };

  const handleExport = () => {
    // Export jobs as JSON or CSV
    const dataStr = JSON.stringify(jobs, null, 2);
    const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
    
    const exportFileDefaultName = `jobs-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    toast.success("Jobs exported successfully");
  };

  if (jobs.length === 0 && !loading) {
    return (
      <div className="text-center py-8 px-4">
        <p className="text-muted-foreground">No jobs to display</p>
      </div>
    );
  }

  return (
    <>
      <JobList
        jobs={jobs}
        loading={loading}
        title={title}
        description={description}
        onApply={handleApply}
        onSave={handleSave}
        onGenerateCoverLetter={handleGenerateCoverLetter}
        onViewDetails={handleViewDetails}
        onRefresh={handleRefresh}
        onExport={handleExport}
        className={className}
      />
      
      <JobDetails
        job={selectedJob}
        open={detailsOpen}
        onOpenChange={setDetailsOpen}
        onApply={handleApply}
        onSave={handleSave}
        onGenerateCoverLetter={handleGenerateCoverLetter}
      />
    </>
  );
}