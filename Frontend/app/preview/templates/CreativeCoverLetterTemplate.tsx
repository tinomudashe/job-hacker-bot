"use client";

import {
  Building,
  Calendar,
  Globe,
  Linkedin,
  Mail,
  MapPin,
  Phone,
  User,
} from "lucide-react";
import * as React from "react";
import { PreviewData } from "../types";
import { parseBasicMarkdown, renderMarkdownLine } from "@/lib/utils/markdown";

// EDIT: This is a brand new template for the "Creative" cover letter style.
// It uses a modern, two-column layout with icons and accent colors.
export const CreativeCoverLetterTemplate: React.FC<{
  data: PreviewData;
  hasMounted: boolean;
}> = ({ data, hasMounted }) => {
  const { personalInfo, company_name, job_title, content } = data;

  return (
    <div className="p-8 md:p-10 bg-transparent font-sans text-gray-700 dark:text-gray-300">
      <div className="max-w-4xl mx-auto">
        <header className="flex flex-col sm:flex-row items-start justify-between mb-10 pb-6 border-b-2 border-primary">
          <div>
            <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight">
              {personalInfo?.name}
            </h1>
            <p className="text-lg text-primary font-medium">{job_title}</p>
          </div>
          <div className="text-right mt-4 sm:mt-0 text-xs space-y-1.5 text-gray-500 dark:text-gray-400">
            <p className="flex items-center justify-end gap-2">
              <Mail className="w-4 h-4 text-primary/70" /> {personalInfo?.email}
            </p>
            <p className="flex items-center justify-end gap-2">
              <Phone className="w-4 h-4 text-primary/70" />{" "}
              {personalInfo?.phone}
            </p>
            {personalInfo?.linkedin && (
              <p className="flex items-center justify-end gap-2">
                <Linkedin className="w-4 h-4 text-primary/70" />
                <a
                  href={personalInfo.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline break-all"
                >
                  {personalInfo.linkedin}
                </a>
              </p>
            )}
            {personalInfo?.website && (
              <p className="flex items-center justify-end gap-2">
                <Globe className="w-4 h-4 text-primary/70" />
                <a
                  href={personalInfo.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline break-all"
                >
                  {personalInfo.website}
                </a>
              </p>
            )}
            <p className="flex items-center justify-end gap-2">
              <MapPin className="w-4 h-4 text-primary/70" />{" "}
              {personalInfo?.location}
            </p>
          </div>
        </header>

        <main>
          <div className="flex items-start text-sm mb-6">
            <div className="flex-1 space-y-1">
              <p className="font-semibold flex items-center gap-2">
                <Building className="w-4 h-4 text-gray-400" /> {company_name}
              </p>
              <p className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-400" /> Hiring Team
              </p>
            </div>
            {hasMounted && (
              <p className="text-right flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-400" />
                {new Date().toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            )}
          </div>

          {/* EDIT: Removed the hardcoded closing from this template. 
              The AI-generated content now provides the full closing, which fits the creative style better. */}
          <div className="whitespace-pre-line leading-7 text-gray-800 dark:text-gray-200 space-y-4 mt-8">
            <p>Dear Hiring Team at {company_name},</p>
            {parseBasicMarkdown(content).split("\n").map((paragraph, index) => {
              // Skip empty paragraphs
              if (!paragraph.trim()) return null;
              
              // Handle bullet points
              if (paragraph.trim().startsWith("•")) {
                return (
                  <p key={index} className="ml-4">
                    {renderMarkdownLine(paragraph)}
                  </p>
                );
              }
              
              // Regular paragraphs
              return (
                <p key={index}>
                  {renderMarkdownLine(paragraph)}
                </p>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
};
