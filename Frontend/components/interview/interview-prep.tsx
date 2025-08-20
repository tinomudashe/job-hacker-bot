"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  GraduationCap,
  Sparkles,
  ChevronDown,
  ChevronRight,
  Building,
  Target,
  Code,
  Users,
  BookOpen,
  Lightbulb,
  MessageSquare,
  Trophy,
  Briefcase,
  CheckCircle,
  Brain,
} from "lucide-react";

interface InterviewSection {
  id: string;
  title: string;
  icon: React.ReactNode;
  content: string | string[];
  subsections?: {
    title: string;
    content: string | string[];
  }[];
}

interface InterviewPrepProps {
  content: string;
  className?: string;
}

export function InterviewPrep({ content, className }: InterviewPrepProps) {
  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(
    new Set(["company--role-overview"])
  );

  // Parse the content to extract role, company, and sections
  const parseContent = () => {
    const lines = content.split('\n');
    let role = '';
    let company = '';
    const sections: InterviewSection[] = [];
    let currentSection: InterviewSection | null = null;
    let currentSubsection: any = null;
    
    for (const line of lines) {
      // Skip the flashcards marker line
      if (line.includes('[INTERVIEW_FLASHCARDS_AVAILABLE]')) {
        continue;
      }
      
      // Extract role
      if (line.includes('**Role:**')) {
        role = line.replace('**Role:**', '').replace(/\*/g, '').trim();
      }
      // Extract company
      if (line.includes('**Company:**')) {
        company = line.replace('**Company:**', '').replace(/\*/g, '').trim();
      }
      
      // Parse sections - skip the main title
      if (line.startsWith('# Comprehensive Interview Preparation Guide')) {
        continue;
      }
      
      // Parse sections
      if (line.startsWith('## ')) {
        if (currentSection) sections.push(currentSection);
        const title = line.replace('## ', '').replace(/\*/g, '').replace(/^\d+\.\s*/, '').trim();
        currentSection = {
          id: title.toLowerCase().replace(/\s+/g, '-'),
          title,
          icon: getSectionIcon(title),
          content: [],
          subsections: []
        };
        currentSubsection = null;
      } else if (line.startsWith('### ') && currentSection) {
        const title = line.replace('### ', '').replace(/\*/g, '').trim();
        currentSubsection = {
          title,
          content: []
        };
        currentSection.subsections?.push(currentSubsection);
      } else if (line.trim() && currentSection) {
        const cleanLine = line.replace(/\*\*/g, '').trim();
        // Skip empty lines or lines that are just formatting
        if (cleanLine && !cleanLine.match(/^[-=]+$/)) {
          if (currentSubsection) {
            if (Array.isArray(currentSubsection.content)) {
              currentSubsection.content.push(cleanLine);
            }
          } else {
            if (Array.isArray(currentSection.content)) {
              currentSection.content.push(cleanLine);
            }
          }
        }
      }
    }
    
    if (currentSection) sections.push(currentSection);
    
    return { role, company, sections };
  };

  const getSectionIcon = (title: string) => {
    if (title.includes('Company') || title.includes('Overview')) return <Building className="h-4 w-4" />;
    if (title.includes('Technical')) return <Code className="h-4 w-4" />;
    if (title.includes('Behavioral')) return <Users className="h-4 w-4" />;
    if (title.includes('Questions')) return <MessageSquare className="h-4 w-4" />;
    if (title.includes('Tips')) return <Lightbulb className="h-4 w-4" />;
    if (title.includes('Success')) return <Trophy className="h-4 w-4" />;
    return <BookOpen className="h-4 w-4" />;
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  const { role, company, sections } = parseContent();

  return (
    <Card className={cn(
      "w-full max-w-full overflow-hidden transition-all duration-200",
      "hover:shadow-xl hover:border-primary/50",
      "bg-card",
      className
    )}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <GraduationCap className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  Interview Preparation Guide
                </h3>
                <p className="text-sm text-muted-foreground">
                  {role && company ? `${role} at ${company}` : 'Comprehensive preparation materials'}
                </p>
              </div>
            </div>
            
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-sm font-medium border bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30">
              <GraduationCap className="h-3 w-3" />
              Interview Flashcards Available
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <ScrollArea className="h-[500px] w-full">
          <div className="p-6 space-y-4 max-w-full overflow-hidden">
            {sections.map((section, index) => (
              <div key={section.id} className="space-y-3">
                {index > 0 && <Separator className="my-4" />}
                
                <Button
                  variant="ghost"
                  className="w-full justify-start p-3 hover:bg-muted/50"
                  onClick={() => toggleSection(section.id)}
                >
                  <div className="flex items-center gap-2 w-full">
                    {expandedSections.has(section.id) ? (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    )}
                    <div className="p-1.5 rounded-md bg-primary/10">
                      {section.icon}
                    </div>
                    <span className="font-medium text-sm text-foreground">{section.title}</span>
                  </div>
                </Button>

                {expandedSections.has(section.id) && (
                  <div className="pl-10 space-y-3 max-w-full overflow-hidden">
                    {Array.isArray(section.content) && section.content.length > 0 && (
                      <div className="space-y-2 max-w-full">
                        {section.content
                          .filter(line => !line.includes('[INTERVIEW_FLASHCARDS_AVAILABLE]'))
                          .map((line, idx) => (
                            <div key={idx} className="text-sm text-muted-foreground leading-relaxed break-words">
                              {line.startsWith('-') || line.startsWith('•') ? (
                                <div className="flex items-start gap-2">
                                  <CheckCircle className="h-3 w-3 mt-1 text-green-600 dark:text-green-400 flex-shrink-0" />
                                  <span className="break-words overflow-wrap-anywhere">{line.replace(/^[-•]\s*/, '')}</span>
                                </div>
                              ) : (
                                <p className="break-words overflow-wrap-anywhere">{line}</p>
                              )}
                            </div>
                          ))}
                      </div>
                    )}

                    {section.subsections && section.subsections.length > 0 && (
                      <div className="space-y-4 max-w-full">
                        {section.subsections.map((subsection, subIdx) => (
                          <div key={subIdx} className="space-y-2 max-w-full overflow-hidden">
                            <h4 className="font-medium text-sm text-foreground/90 break-words">
                              {subsection.title}
                            </h4>
                            <div className="space-y-1 pl-4 max-w-full">
                              {Array.isArray(subsection.content) && subsection.content
                                .filter(line => !line.includes('[INTERVIEW_FLASHCARDS_AVAILABLE]'))
                                .map((line, lineIdx) => (
                                  <div key={lineIdx} className="text-sm text-muted-foreground leading-relaxed break-words">
                                    {line.startsWith('-') || line.startsWith('•') || /^\d+\./.test(line) ? (
                                      <div className="flex items-start gap-2">
                                        <CheckCircle className="h-3 w-3 mt-1 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                                        <span className="break-words overflow-wrap-anywhere flex-1">{line.replace(/^[-•]\s*/, '').replace(/^\d+\.\s*/, '')}</span>
                                      </div>
                                    ) : (
                                      <p className="break-words overflow-wrap-anywhere">{line}</p>
                                    )}
                                  </div>
                                ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>

      <div className="p-4 border-t bg-muted/10">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-primary animate-pulse" />
              <p className="text-xs font-medium text-foreground">
                Click the brain icon below to generate interview flashcards
              </p>
            </div>
            <Button size="sm" variant="outline" className="gap-1.5">
              <BookOpen className="h-3 w-3" />
              View Guide
            </Button>
          </div>
          <div className="flex items-center gap-2 p-2 rounded-lg bg-primary/5 border border-primary/10">
            <Sparkles className="h-3 w-3 text-primary flex-shrink-0" />
            <p className="text-xs text-muted-foreground">
              Interactive flashcards help you practice key concepts and prepare for technical questions
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}