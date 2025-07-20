"use client";

import { DynamicForm, FormField } from "./dynamic-form";

interface JobFormProps {
  onSubmit: (data: any) => void;
  defaultValues?: any;
}

export function JobForm({ onSubmit, defaultValues }: JobFormProps) {
  const formFields: FormField[] = [
    {
      name: "fullName",
      label: "Full Name",
      type: "text",
      required: true,
      placeholder: "Enter your full name",
    },
    {
      name: "email",
      label: "Email",
      type: "email",
      required: true,
      placeholder: "Enter your email address",
    },
    {
      name: "phone",
      label: "Phone Number",
      type: "tel",
      required: true,
      placeholder: "Enter your phone number",
    },
    {
      name: "resume",
      label: "Resume/CV",
      type: "file",
      required: true,
      accept: ".pdf,.doc,.docx",
      helperText: "Upload your resume (PDF, DOC, or DOCX)",
    },
    {
      name: "coverLetter",
      label: "Cover Letter",
      type: "textarea",
      required: false,
      placeholder: "Write your cover letter here...",
      rows: 5,
    },
    {
      name: "experience",
      label: "Years of Experience",
      type: "select",
      required: true,
      options: [
        { value: "0-1", label: "0-1 years" },
        { value: "1-3", label: "1-3 years" },
        { value: "3-5", label: "3-5 years" },
        { value: "5-10", label: "5-10 years" },
        { value: "10+", label: "10+ years" },
      ],
    },
    {
      name: "startDate",
      label: "Available Start Date",
      type: "date",
      required: true,
    },
    {
      name: "salary",
      label: "Expected Salary",
      type: "text",
      required: false,
      placeholder: "Enter your expected salary",
    },
    {
      name: "linkedin",
      label: "LinkedIn Profile",
      type: "url",
      required: false,
      placeholder: "Enter your LinkedIn profile URL",
    },
    {
      name: "portfolio",
      label: "Portfolio/Website",
      type: "url",
      required: false,
      placeholder: "Enter your portfolio or website URL",
    },
    {
      name: "references",
      label: "References",
      type: "textarea",
      required: false,
      placeholder: "List your professional references...",
      rows: 3,
    },
    {
      name: "additionalInfo",
      label: "Additional Information",
      type: "textarea",
      required: false,
      placeholder: "Any additional information you'd like to share...",
      rows: 3,
    },
  ];

  return (
    <div className="max-w-2xl mx-auto p-6 bg-card rounded-lg border">
      <h2 className="text-2xl font-semibold mb-6">Job Application</h2>
      <DynamicForm
        fields={formFields}
        onSubmit={onSubmit}
        defaultValues={defaultValues}
        submitLabel="Submit Application"
      />
    </div>
  );
}
