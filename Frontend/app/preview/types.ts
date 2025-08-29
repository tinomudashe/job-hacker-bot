// EDIT: Created a new shared types file to be used by the preview page and all templates.
// This ensures all components work with the same data structure.
export interface PreviewData {
  content: string;
  style: string;
  company_name: string;
  job_title: string;
  content_type: "cover_letter" | "resume";
  section_order?: Array<{ id: string; visible: boolean }>;
  personalInfo?: {
    name: string;
    email: string;
    phone: string;
    location: string;
    linkedin: string;
    website: string;
    summary: string;
  };
  work_experience?: Array<{
    id: string;
    jobTitle: string;
    company: string;
    dates: { start: string; end: string };
    description: string;
  }>;
  education?: Array<{
    id: string;
    degree: string;
    institution: string;
    dates: { end: string };
    description: string;
  }>;
  skills?: string[];
  projects?: Array<{
    name: string;
    description: string;
    technologies: string[];
    url: string;
  }>;
  certifications?: Array<{
    name: string;
    issuing_organization: string;
    date_issued: string;
  }>;
  languages?: Array<{
    name: string;
    proficiency: string;
  }>;
}
