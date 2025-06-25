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