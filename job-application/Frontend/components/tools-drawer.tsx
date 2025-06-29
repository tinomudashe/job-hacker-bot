"use client";

import * as React from "react";
import { X } from "lucide-react";
import { DynamicForm, FormField } from "./ui/dynamic-form";
import { Button } from "./ui/button";
import { useWebSocket } from "../lib/hooks/use-websocket";

interface ToolConfig {
  name: string;
  display: string;
  description: string;
  fields: FormField[];
  craftMessage: (data: Record<string, unknown>) => string;
}

const TOOL_CONFIG: ToolConfig[] = [
  {
    name: "search_jobs",
    display: "Search Jobs",
    description: "Find job listings online that match a search query.",
    fields: [
      { name: "query", label: "Search Query", type: "text", required: true, placeholder: "e.g. python developer in Poland" },
    ],
    craftMessage: (data) => `Please use the search_jobs tool with the query: \"${data.query}\"`,
  },
  {
    name: "generate_tailored_resume",
    display: "Generate Tailored Resume",
    description: "Create a complete resume tailored to a specific job and company.",
    fields: [
      { name: "job_title", label: "Job Title", type: "text", required: true, placeholder: "e.g. Software Engineer" },
      { name: "company_name", label: "Company Name", type: "text", placeholder: "e.g. Google (optional)" },
      { name: "job_description", label: "Job Description", type: "textarea", rows: 6, placeholder: "Paste the full job description here for better tailoring..." },
      { name: "user_skills", label: "Additional Skills to Highlight", type: "text", placeholder: "e.g. Python, React, AWS (optional)" },
    ],
    craftMessage: (data) => `Please use the generate_tailored_resume tool with job_title: "${data.job_title}", company_name: "${data.company_name}", job_description: "${data.job_description}", user_skills: "${data.user_skills}"`,
  },
  {
    name: "create_resume_from_scratch",
    display: "Create Resume from Scratch",
    description: "Build a complete professional resume based on your career goals.",
    fields: [
      { name: "target_role", label: "Target Role", type: "text", required: true, placeholder: "e.g. Product Manager" },
      { name: "experience_level", label: "Experience Level", type: "select", required: true, options: [
        { value: "entry-level", label: "Entry Level (0-2 years)" },
        { value: "mid-level", label: "Mid Level (3-7 years)" },
        { value: "senior", label: "Senior (8-15 years)" },
        { value: "executive", label: "Executive (15+ years)" }
      ]},
      { name: "industry", label: "Target Industry", type: "text", placeholder: "e.g. Technology, Healthcare (optional)" },
      { name: "key_skills", label: "Key Skills", type: "text", placeholder: "e.g. Leadership, Data Analysis, Python" },
    ],
    craftMessage: (data) => `Please use the create_resume_from_scratch tool with target_role: "${data.target_role}", experience_level: "${data.experience_level}", industry: "${data.industry}", key_skills: "${data.key_skills}"`,
  },
  {
    name: "enhance_resume_section",
    display: "Enhance Resume Section",
    description: "Improve a specific section of your resume with AI-powered enhancements.",
    fields: [
      { name: "section", label: "Section to Enhance", type: "select", required: true, options: [
        { value: "summary", label: "Professional Summary" },
        { value: "experience", label: "Work Experience" },
        { value: "skills", label: "Skills" },
        { value: "education", label: "Education" }
      ]},
      { name: "current_content", label: "Current Content", type: "textarea", rows: 4, placeholder: "Paste your current section content here..." },
      { name: "job_description", label: "Target Job Description", type: "textarea", rows: 4, placeholder: "Paste job description to tailor the enhancement (optional)" },
    ],
    craftMessage: (data) => `Please use the enhance_resume_section tool with section: "${data.section}", current_content: "${data.current_content}", job_description: "${data.job_description}"`,
  },
  {
    name: "update_personal_information",
    display: "Update Personal Info",
    description: "Edit your resume's personal information section.",
    fields: [
      { name: "name", label: "Name", type: "text" },
      { name: "email", label: "Email", type: "email" },
      { name: "phone", label: "Phone", type: "tel" },
      { name: "linkedin", label: "LinkedIn", type: "url" },
      { name: "location", label: "Location", type: "text" },
      { name: "summary", label: "Professional Summary", type: "textarea", rows: 4 },
    ],
    craftMessage: (data) => `Please use the update_personal_information tool with the following details: ${JSON.stringify(data)}`,
  },
  {
    name: "add_work_experience",
    display: "Add Work Experience",
    description: "Add a work experience entry to your resume.",
    fields: [
      { name: "job_title", label: "Job Title", type: "text", required: true },
      { name: "company", label: "Company", type: "text", required: true },
      { name: "dates", label: "Dates (e.g. 2021-2023)", type: "text", required: true },
      { name: "description", label: "Description", type: "textarea", rows: 4, required: true },
    ],
    craftMessage: (data) => `Please use the add_work_experience tool with the following details: ${JSON.stringify(data)}`,
  },
  {
    name: "generate_cover_letter_from_url",
    display: "Generate Cover Letter from Job URL",
    description: "Create a tailored cover letter from a job posting URL.",
    fields: [
      { name: "job_url", label: "Job Posting URL", type: "url", required: true, placeholder: "https://linkedin.com/jobs/view/..." },
      { name: "user_skills", label: "Skills to Highlight", type: "text", placeholder: "e.g. Python, Leadership, Data Analysis (optional)" },
      { name: "use_browser", label: "Use Browser Automation", type: "checkbox", defaultValue: true },
    ],
    craftMessage: (data) => `Please use the generate_cover_letter_from_url tool with job_url: "${data.job_url}", user_skills: "${data.user_skills}", use_browser: ${data.use_browser}`,
  },
  {
    name: "generate_cover_letter",
    display: "Generate Cover Letter Manually",
    description: "Create a cover letter by providing job details manually.",
    fields: [
      { name: "job_title", label: "Job Title", type: "text", required: true, placeholder: "e.g. Software Engineer" },
      { name: "company_name", label: "Company Name", type: "text", required: true, placeholder: "e.g. Google" },
      { name: "job_description", label: "Job Description", type: "textarea", rows: 6, required: true, placeholder: "Paste the job description here..." },
      { name: "user_skills", label: "Skills to Highlight", type: "text", placeholder: "e.g. Python, React, AWS (optional)" },
    ],
    craftMessage: (data) => `Please use the generate_cover_letter tool with job_title: "${data.job_title}", company_name: "${data.company_name}", job_description: "${data.job_description}", user_skills: "${data.user_skills}"`,
  },
  {
    name: "add_education",
    display: "Add Education",
    description: "Add an education entry to your resume.",
    fields: [
      { name: "degree", label: "Degree", type: "text", required: true },
      { name: "institution", label: "Institution", type: "text", required: true },
      { name: "dates", label: "Dates", type: "text", required: true },
    ],
    craftMessage: (data) => `Please use the add_education tool with the following details: ${JSON.stringify(data)}`,
  },
  {
    name: "set_skills",
    display: "Set Skills",
    description: "Replace your skills list with a new set.",
    fields: [
      { name: "skills", label: "Skills (comma-separated)", type: "textarea", rows: 3, required: true, placeholder: "Python, React, SQL" },
    ],
    craftMessage: (data) => `Please use the set_skills tool with the skills: ${data.skills}`,
  },
];

interface ToolsDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function ToolsDrawer({ open, onClose }: ToolsDrawerProps) {
  const { sendMessage, isConnected } = useWebSocket();
  const [activeTool, setActiveTool] = React.useState<ToolConfig>(TOOL_CONFIG[0]);
  const [lastMessage, setLastMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!open) {
      // reset state when drawer closes
      setLastMessage(null);
    }
  }, [open]);

  const handleToolSubmit = (values: Record<string, unknown>) => {
    if (!activeTool) return;
    const prompt = activeTool.craftMessage(values);
    sendMessage(prompt);
    setLastMessage("Command sent successfully ✨");
    setTimeout(() => setLastMessage(null), 4000);
  };

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col bg-background shadow-lg sm:max-w-lg animate-slide-in-right">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">Tools</h2>
          <button onClick={onClose} aria-label="Close drawer" className="rounded-md p-2 hover:bg-accent">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Tool selector */}
        <div className="flex flex-wrap gap-3 p-6">
          {TOOL_CONFIG.map((tool) => (
            <Button
              key={tool.name}
              size="sm"
              variant={activeTool.name === tool.name ? "default" : "outline"}
              onClick={() => setActiveTool(tool)}
            >
              {tool.display}
            </Button>
          ))}
        </div>

        {/* Form */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-medium">{activeTool.display}</h3>
              <p className="text-muted-foreground text-sm">
                {activeTool.description}
              </p>
            </div>
            {!isConnected && (
              <p className="text-destructive">Connecting to backend…</p>
            )}
            <DynamicForm
              fields={activeTool.fields}
              onSubmit={handleToolSubmit}
              submitLabel="Run"
            />
            {lastMessage && (
              <p className="text-sm text-green-600" aria-live="polite">
                {lastMessage}
              </p>
            )}
          </div>
        </div>
      </div>
    </>
  );
} 