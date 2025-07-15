import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Briefcase,
  Building2,
  Clock,
  Crown,
  MapPin,
  Search,
  Sparkles,
} from "lucide-react";

interface ToolsMenuProps {
  onToolSelect: (prompt: string) => void;
}

interface Tool {
  icon: React.ElementType;
  label: string;
  prompt?: string;
  action?: string;
}

const JOB_TOOLS: Tool[] = [
  {
    icon: Search,
    label: "Search Jobs",
    prompt: "Search for jobs matching my skills and experience",
  },
  {
    icon: Building2,
    label: "Company Search",
    prompt: "Find companies that are hiring in my field",
  },
  {
    icon: MapPin,
    label: "Location Search",
    prompt: "Find jobs in a specific location",
  },
  {
    icon: Clock,
    label: "Recent Jobs",
    prompt: "Show me the most recent job postings",
  },
  {
    icon: Sparkles,
    label: "Job Recommendations",
    prompt: "Recommend jobs based on my profile",
  },
];

const PRO_TOOL: Tool = {
  icon: Crown,
  label: "Upgrade to Pro",
  action: "upgrade",
};

export function ToolsMenu({ onToolSelect }: ToolsMenuProps) {
  const handleSelect = async (tool: Tool) => {
    if (tool.action === "upgrade") {
      try {
        const response = await fetch("/api/billing/create-checkout-session", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ plan: "pro" }),
        });
        if (response.ok) {
          const { url } = await response.json();
          window.location.href = url;
        } else {
          console.error("Failed to create checkout session");
        }
      } catch (error) {
        console.error("Error creating checkout session:", error);
      }
    } else if (tool.prompt) {
      onToolSelect(tool.prompt);
    }
  };

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
            onClick={() => handleSelect(tool)}
            className="flex items-center gap-2 py-3 cursor-pointer"
          >
            <tool.icon className="h-4 w-4" />
            <span>{tool.label}</span>
          </DropdownMenuItem>
        ))}
        <DropdownMenuItem
          key={PRO_TOOL.label}
          onClick={() => handleSelect(PRO_TOOL)}
          className="flex items-center gap-2 py-3 cursor-pointer text-primary"
        >
          <PRO_TOOL.icon className="h-4 w-4" />
          <span>{PRO_TOOL.label}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
