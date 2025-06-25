import * as React from 'react';
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  Briefcase, 
  Search, 
  Building2, 
  MapPin, 
  Clock, 
  ChevronDown,
  Sparkles
} from 'lucide-react';

interface ToolsMenuProps {
  onToolSelect: (prompt: string) => void;
}

const JOB_TOOLS = [
  {
    icon: Search,
    label: "Search Jobs",
    prompt: "Search for jobs matching my skills and experience"
  },
  {
    icon: Building2,
    label: "Company Search",
    prompt: "Find companies that are hiring in my field"
  },
  {
    icon: MapPin,
    label: "Location Search",
    prompt: "Find jobs in a specific location"
  },
  {
    icon: Clock,
    label: "Recent Jobs",
    prompt: "Show me the most recent job postings"
  },
  {
    icon: Sparkles,
    label: "Job Recommendations",
    prompt: "Recommend jobs based on my profile"
  }
];

export function ToolsMenu({ onToolSelect }: ToolsMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon"
          className="h-9 w-9 hover:bg-primary/10"
        >
          <Briefcase className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        {JOB_TOOLS.map((tool) => (
          <DropdownMenuItem
            key={tool.label}
            onClick={() => onToolSelect(tool.prompt)}
            className="flex items-center gap-2 py-3 cursor-pointer"
          >
            <tool.icon className="h-4 w-4" />
            <span>{tool.label}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
} 