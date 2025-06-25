"use client";

import * as React from "react";
import { DataTable } from "./data-table";
import { Button } from "./button";
import { Badge } from "./badge";

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  salary?: string;
  type: string;
  skills?: string[];
  postedDate: string;
  link?: string;
}

interface JobTableProps {
  jobs: Job[];
  onApply?: (jobId: string) => void;
}

export function JobTable({ jobs, onApply }: JobTableProps) {
  const columns = React.useMemo(
    () => [
      {
        key: "title",
        label: "Position",
        render: (value: any, row: Job) => (
          <div>
            <div className="font-medium">{value}</div>
            <div className="text-sm text-muted-foreground">{row.company}</div>
          </div>
        ),
      },
      {
        key: "location",
        label: "Location",
      },
      {
        key: "type",
        label: "Type",
        render: (value: any) => (
          <Badge variant={value === "Full-time" ? "default" : "secondary"}>
            {value}
          </Badge>
        ),
      },
      {
        key: "salary",
        label: "Salary",
        render: (value: any) => value || "Not specified",
      },
      {
        key: "skills",
        label: "Required Skills",
        render: (value: any) => (
          <div className="flex flex-wrap gap-1">
            {value?.map((skill: string) => (
              <Badge key={skill} variant="outline">
                {skill}
              </Badge>
            ))}
          </div>
        ),
      },
      {
        key: "postedDate",
        label: "Posted",
        render: (value: any) => {
          const date = new Date(value);
          const now = new Date();
          const diffTime = Math.abs(now.getTime() - date.getTime());
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
          return `${diffDays} days ago`;
        },
      },
      {
        key: "actions",
        label: "",
        render: (_: any, row: Job) => (
          <div className="flex justify-end">
            {row.link ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(row.link, "_blank")}
              >
                View
              </Button>
            ) : (
              <Button
                variant="default"
                size="sm"
                onClick={() => onApply?.(row.id)}
              >
                Apply
              </Button>
            )}
          </div>
        ),
      },
    ],
    [onApply]
  );

  return (
    <div className="rounded-md border">
      <DataTable data={jobs} columns={columns} />
    </div>
  );
} 