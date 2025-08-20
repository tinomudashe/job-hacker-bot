"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  FileSearch,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Sparkles,
  FileText,
  Type,
  Users,
  Mail,
  BookOpen,
  Briefcase,
  Trophy,
  Target,
  ChevronRight,
  Wand2,
} from "lucide-react";

interface ScoreBreakdown {
  formatting: number;
  sections: number;
  contact_info: number;
  readability: number;
  skills: number;
  experience: number;
  achievements: number;
}

interface ATSScoreProps {
  content: string;
  className?: string;
  onRefineCV?: () => void;
  onSendMessage?: (message: string) => void;
}

export function ATSScoreCard({ content, className, onRefineCV, onSendMessage }: ATSScoreProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  
  // Parse the ATS score from the content
  const parseATSContent = () => {
    const lines = content.split('\n');
    let totalScore = 0;
    let maxScore = 100;
    let grade = 'C';
    let level = '';
    const breakdown: ScoreBreakdown = {
      formatting: 0,
      sections: 0,
      contact_info: 0,
      readability: 0,
      skills: 0,
      experience: 0,
      achievements: 0,
    };
    const suggestions: string[] = [];
    
    for (const line of lines) {
      // Extract overall score
      const scoreMatch = line.match(/Overall Score:\s*(\d+)\/(\d+)\s*\(([A-Z][+-]?)\)/);
      if (scoreMatch) {
        totalScore = parseInt(scoreMatch[1]);
        maxScore = parseInt(scoreMatch[2]);
        grade = scoreMatch[3];
      }
      
      // Extract breakdown scores
      if (line.includes('**Formatting**:')) {
        const match = line.match(/(\d+)\/\d+/);
        if (match) breakdown.formatting = parseInt(match[1]);
      }
      if (line.includes('**Standard Sections**:')) {
        const match = line.match(/(\d+)\/\d+/);
        if (match) breakdown.sections = parseInt(match[1]);
      }
      if (line.includes('**Contact Information**:')) {
        const match = line.match(/(\d+)\/\d+/);
        if (match) breakdown.contact_info = parseInt(match[1]);
      }
      if (line.includes('**Readability**:')) {
        const match = line.match(/(\d+)\/\d+/);
        if (match) breakdown.readability = parseInt(match[1]);
      }
      if (line.includes('**Skills Section**:')) {
        const match = line.match(/(\d+)\/\d+/);
        if (match) breakdown.skills = parseInt(match[1]);
      }
      if (line.includes('**Experience Format**:')) {
        const match = line.match(/(\d+)\/\d+/);
        if (match) breakdown.experience = parseInt(match[1]);
      }
      if (line.includes('**Quantified Achievements**:')) {
        const match = line.match(/(\d+)\/\d+/);
        if (match) breakdown.achievements = parseInt(match[1]);
      }
      
      // Extract optimization level
      if (line.includes('**Excellent**')) level = 'Excellent';
      else if (line.includes('**Good**')) level = 'Good';
      else if (line.includes('**Fair**')) level = 'Fair';
      else if (line.includes('**Needs Improvement**')) level = 'Needs Improvement';
      
      // Extract suggestions
      const suggestionMatch = line.match(/^\d+\.\s+(.+)/);
      if (suggestionMatch && !line.includes('###')) {
        suggestions.push(suggestionMatch[1]);
      }
    }
    
    return { totalScore, maxScore, grade, level, breakdown, suggestions };
  };
  
  const { totalScore, maxScore, grade, level, breakdown, suggestions } = parseATSContent();
  
  // Get color based on score
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600 dark:text-green-400";
    if (score >= 70) return "text-blue-600 dark:text-blue-400";
    if (score >= 60) return "text-yellow-600 dark:text-yellow-400";
    return "text-red-600 dark:text-red-400";
  };
  
  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300";
    if (grade.startsWith('B')) return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300";
    if (grade.startsWith('C')) return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300";
    return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300";
  };
  
  const getLevelIcon = () => {
    if (level === 'Excellent') return <Trophy className="h-5 w-5 text-green-600" />;
    if (level === 'Good') return <TrendingUp className="h-5 w-5 text-blue-600" />;
    if (level === 'Fair') return <AlertCircle className="h-5 w-5 text-yellow-600" />;
    return <XCircle className="h-5 w-5 text-red-600" />;
  };
  
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'formatting': return <Type className="h-4 w-4" />;
      case 'sections': return <FileText className="h-4 w-4" />;
      case 'contact_info': return <Mail className="h-4 w-4" />;
      case 'readability': return <BookOpen className="h-4 w-4" />;
      case 'skills': return <Briefcase className="h-4 w-4" />;
      case 'experience': return <Users className="h-4 w-4" />;
      case 'achievements': return <Target className="h-4 w-4" />;
      default: return <FileSearch className="h-4 w-4" />;
    }
  };
  
  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'formatting': return 'Formatting';
      case 'sections': return 'Standard Sections';
      case 'contact_info': return 'Contact Info';
      case 'readability': return 'Readability';
      case 'skills': return 'Skills';
      case 'experience': return 'Experience';
      case 'achievements': return 'Achievements';
      default: return category;
    }
  };
  
  const getCategoryMax = (category: string) => {
    switch (category) {
      case 'formatting': return 20;
      case 'sections': return 15;
      case 'contact_info': return 10;
      case 'readability': return 10;
      case 'skills': return 15;
      case 'experience': return 15;
      case 'achievements': return 15;
      default: return 10;
    }
  };

  const handleRefineClick = () => {
    if (onSendMessage) {
      // Send a message to refine the CV based on ATS feedback
      onSendMessage("Please refine my resume to improve the ATS score based on the feedback");
    } else if (onRefineCV) {
      onRefineCV();
    }
  };

  return (
    <Card className={cn(
      "w-full overflow-hidden transition-all duration-200",
      "hover:shadow-xl hover:border-primary/50",
      "bg-card",
      className
    )}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileSearch className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                ATS Resume Review
              </h3>
              <p className="text-sm text-muted-foreground">
                Applicant Tracking System Compatibility
              </p>
            </div>
          </div>
          <Badge className={cn("text-lg px-3 py-1", getGradeColor(grade))}>
            {grade}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Main Score Display */}
        <div className="text-center space-y-3">
          <div className="relative inline-flex items-center justify-center">
            <div className="text-5xl font-bold">
              <span className={getScoreColor(totalScore)}>{totalScore}</span>
              <span className="text-2xl text-muted-foreground">/{maxScore}</span>
            </div>
          </div>
          <div className="flex items-center justify-center gap-2">
            {getLevelIcon()}
            <span className="text-sm font-medium">{level}</span>
          </div>
          <Progress value={totalScore} max={maxScore} className="h-3" />
        </div>

        <Separator />

        {/* Score Breakdown */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-foreground">Score Breakdown</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="gap-1"
            >
              {isExpanded ? 'Hide Details' : 'Show Details'}
              <ChevronRight className={cn(
                "h-3 w-3 transition-transform",
                isExpanded && "rotate-90"
              )} />
            </Button>
          </div>
          
          {isExpanded && (
            <div className="space-y-2">
              {Object.entries(breakdown).map(([category, score]) => {
                const max = getCategoryMax(category);
                const percentage = (score / max) * 100;
                
                return (
                  <div key={category} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(category)}
                        <span className="text-muted-foreground">
                          {getCategoryLabel(category)}
                        </span>
                      </div>
                      <span className="font-medium">
                        {score}/{max}
                      </span>
                    </div>
                    <Progress value={percentage} className="h-2" />
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Improvement Suggestions */}
        {suggestions.length > 0 && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                Top Improvements
              </h4>
              <div className="space-y-2">
                {suggestions.slice(0, 3).map((suggestion, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">{suggestion}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>

      <CardFooter className="p-4 border-t bg-muted/10">
        <div className="flex items-center justify-between w-full">
          <p className="text-xs text-muted-foreground">
            Optimize for ATS to increase visibility
          </p>
          <Button
            onClick={handleRefineClick}
            size="sm"
            className="gap-2"
          >
            <Wand2 className="h-3 w-3" />
            Refine Resume
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}