"use client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  Calendar,
  Clock,
  Send,
  CheckCircle,
  AlertCircle,
  Mail,
  Building,
  Briefcase,
  User,
  ArrowRight,
  Plus,
  RefreshCw,
  Timer,
  Target,
  TrendingUp,
  ChevronRight,
} from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";

interface EmailRecord {
  id: string;
  subject: string;
  recipient: string;
  company: string;
  jobTitle: string;
  sentAt: string;
  status: "sent" | "opened" | "replied" | "scheduled" | "draft";
  followUpCount: number;
  nextFollowUp?: string;
  lastResponse?: string;
}

interface FollowUpSchedule {
  emailId: string;
  scheduledFor: string;
  type: "gentle" | "value-add" | "final" | "thank-you";
  daysSinceApplication: number;
}

interface FollowUpTrackerProps {
  onSendMessage?: (message: string) => void;
  onGenerateFollowUp?: (originalEmail: EmailRecord) => void;
  className?: string;
}

export function FollowUpTracker({
  onSendMessage,
  onGenerateFollowUp,
  className,
}: FollowUpTrackerProps) {
  const [emails, setEmails] = useState<EmailRecord[]>([
    {
      id: "1",
      subject: "Application for Senior Frontend Developer",
      recipient: "Sarah Johnson",
      company: "TechCorp",
      jobTitle: "Senior Frontend Developer",
      sentAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      status: "sent",
      followUpCount: 0,
      nextFollowUp: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "2",
      subject: "Following up - Software Engineer Position",
      recipient: "Mike Chen",
      company: "StartupXYZ",
      jobTitle: "Software Engineer",
      sentAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      status: "opened",
      followUpCount: 1,
      nextFollowUp: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    },
  ]);

  const [scheduledFollowUps, setScheduledFollowUps] = useState<FollowUpSchedule[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailRecord | null>(null);

  // Calculate days since sent
  const getDaysSince = (date: string) => {
    const diff = Date.now() - new Date(date).getTime();
    return Math.floor(diff / (1000 * 60 * 60 * 24));
  };

  // Get follow-up recommendation
  const getFollowUpRecommendation = (email: EmailRecord) => {
    const daysSince = getDaysSince(email.sentAt);
    
    if (email.status === "replied") {
      return { action: "none", message: "Already received a response" };
    }
    
    if (email.followUpCount === 0 && daysSince >= 3) {
      return { action: "gentle", message: "Send gentle follow-up (3 days)" };
    }
    
    if (email.followUpCount === 1 && daysSince >= 7) {
      return { action: "value-add", message: "Send value-add follow-up (1 week)" };
    }
    
    if (email.followUpCount === 2 && daysSince >= 14) {
      return { action: "final", message: "Send final follow-up (2 weeks)" };
    }
    
    if (email.followUpCount >= 3) {
      return { action: "none", message: "Maximum follow-ups reached" };
    }
    
    return { action: "wait", message: `Wait ${3 - daysSince} more days` };
  };

  // Generate follow-up
  const handleGenerateFollowUp = (email: EmailRecord) => {
    const daysSince = getDaysSince(email.sentAt);
    const followUpType = email.followUpCount === 0 ? "gentle" : 
                        email.followUpCount === 1 ? "value-add" : "final";
    
    const message = `Generate a ${followUpType} follow-up email for:
    
Original Email: ${email.subject}
Company: ${email.company}
Position: ${email.jobTitle}
Recipient: ${email.recipient}
Days since application: ${daysSince}
Previous follow-ups: ${email.followUpCount}

Make it brief, professional, and add value.`;
    
    if (onSendMessage) {
      onSendMessage(message);
    }
    
    // Update email record
    setEmails(emails.map(e => 
      e.id === email.id 
        ? { ...e, followUpCount: e.followUpCount + 1, status: "sent" as const }
        : e
    ));
    
    toast.success("Follow-up generated and sent!");
  };

  // Schedule follow-up
  const scheduleFollowUp = (email: EmailRecord, days: number) => {
    const scheduledDate = new Date(Date.now() + days * 24 * 60 * 60 * 1000);
    
    const newSchedule: FollowUpSchedule = {
      emailId: email.id,
      scheduledFor: scheduledDate.toISOString(),
      type: email.followUpCount === 0 ? "gentle" : "value-add",
      daysSinceApplication: getDaysSince(email.sentAt) + days,
    };
    
    setScheduledFollowUps([...scheduledFollowUps, newSchedule]);
    
    // Update email record
    setEmails(emails.map(e => 
      e.id === email.id 
        ? { ...e, nextFollowUp: scheduledDate.toISOString() }
        : e
    ));
    
    toast.success(`Follow-up scheduled for ${scheduledDate.toLocaleDateString()}`);
  };

  // Get status color
  const getStatusColor = (status: EmailRecord["status"]) => {
    switch (status) {
      case "sent":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400";
      case "opened":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
      case "replied":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
      case "scheduled":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400";
    }
  };

  // Check for pending follow-ups
  useEffect(() => {
    const checkPendingFollowUps = () => {
      emails.forEach(email => {
        if (email.nextFollowUp) {
          const followUpDate = new Date(email.nextFollowUp);
          const now = new Date();
          
          if (followUpDate <= now && email.status !== "replied") {
            toast.info(`Follow-up due for ${email.company} - ${email.jobTitle}`);
          }
        }
      });
    };
    
    checkPendingFollowUps();
    const interval = setInterval(checkPendingFollowUps, 60 * 60 * 1000); // Check every hour
    
    return () => clearInterval(interval);
  }, [emails]);

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Mail className="h-5 w-5 text-primary" />
            Email Follow-up Tracker
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            Track and automate your job application follow-ups
          </p>
        </div>
        
        <Button size="sm" variant="outline">
          <Plus className="h-4 w-4 mr-1" />
          Add Email
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Sent</p>
                <p className="text-2xl font-bold">{emails.length}</p>
              </div>
              <Send className="h-8 w-8 text-blue-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Opened</p>
                <p className="text-2xl font-bold">
                  {emails.filter(e => e.status === "opened").length}
                </p>
              </div>
              <Mail className="h-8 w-8 text-yellow-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Replied</p>
                <p className="text-2xl font-bold">
                  {emails.filter(e => e.status === "replied").length}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold">
                  {emails.filter(e => e.nextFollowUp && new Date(e.nextFollowUp) > new Date()).length}
                </p>
              </div>
              <Clock className="h-8 w-8 text-purple-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Email List */}
      <div className="space-y-4">
        {emails.map((email) => {
          const recommendation = getFollowUpRecommendation(email);
          const daysSince = getDaysSince(email.sentAt);
          
          return (
            <Card key={email.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-2">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold text-base">{email.subject}</h4>
                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Building className="h-3 w-3" />
                            {email.company}
                          </span>
                          <span className="flex items-center gap-1">
                            <Briefcase className="h-3 w-3" />
                            {email.jobTitle}
                          </span>
                          <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {email.recipient}
                          </span>
                        </div>
                      </div>
                      
                      <Badge className={cn("ml-2", getStatusColor(email.status))}>
                        {email.status}
                      </Badge>
                    </div>

                    {/* Timeline */}
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1 text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        Sent {daysSince} days ago
                      </span>
                      
                      {email.followUpCount > 0 && (
                        <span className="flex items-center gap-1">
                          <RefreshCw className="h-3 w-3" />
                          {email.followUpCount} follow-up{email.followUpCount > 1 ? "s" : ""}
                        </span>
                      )}
                      
                      {email.nextFollowUp && (
                        <span className="flex items-center gap-1 text-purple-600 dark:text-purple-400">
                          <Timer className="h-3 w-3" />
                          Next: {new Date(email.nextFollowUp).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    {/* Recommendation */}
                    {recommendation.action !== "none" && (
                      <div className="flex items-center gap-2 pt-2">
                        <AlertCircle className="h-4 w-4 text-amber-500" />
                        <span className="text-sm text-amber-600 dark:text-amber-400">
                          {recommendation.message}
                        </span>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      {recommendation.action !== "none" && recommendation.action !== "wait" && (
                        <Button
                          size="sm"
                          onClick={() => handleGenerateFollowUp(email)}
                        >
                          <Send className="h-3 w-3 mr-1" />
                          Send Follow-up
                        </Button>
                      )}
                      
                      {email.status !== "replied" && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => scheduleFollowUp(email, 3)}
                          >
                            <Clock className="h-3 w-3 mr-1" />
                            Schedule (3 days)
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelectedEmail(email)}
                          >
                            <ChevronRight className="h-3 w-3 mr-1" />
                            View Details
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Best Practices */}
      <Card className="bg-muted/30">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Follow-up Best Practices
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <Target className="h-4 w-4 text-primary mt-0.5" />
              <span>First follow-up after 3-5 days increases reply rate by 49%</span>
            </li>
            <li className="flex items-start gap-2">
              <Target className="h-4 w-4 text-primary mt-0.5" />
              <span>Keep follow-ups brief and add new value or information</span>
            </li>
            <li className="flex items-start gap-2">
              <Target className="h-4 w-4 text-primary mt-0.5" />
              <span>Space follow-ups 3-7 days apart, limit to 3-4 total</span>
            </li>
            <li className="flex items-start gap-2">
              <Target className="h-4 w-4 text-primary mt-0.5" />
              <span>Reference specific details from the job posting or company</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}