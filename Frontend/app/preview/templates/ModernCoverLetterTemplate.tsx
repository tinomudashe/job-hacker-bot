"use client";

import * as React from "react";
import { PreviewData } from "../types";
import { parseBasicMarkdown, renderMarkdownLine } from "@/lib/utils/markdown";

// EDIT: This is the existing CoverLetterTemplate component, moved into its own file.
// This will serve as our "Modern" style, matching the original implementation.
export const ModernCoverLetterTemplate: React.FC<{
  data: PreviewData;
  hasMounted: boolean;
}> = ({ data, hasMounted }) => {
  const { personalInfo, company_name, job_title, content } = data;

  return (
    <div className="p-8 md:p-12 bg-transparent text-gray-800 font-serif text-base leading-relaxed dark:text-gray-200">
      <div className="max-w-4xl mx-auto">
        {/* Sender's Info (Top Right) */}
        <div className="text-right mb-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {personalInfo?.name}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {personalInfo?.location}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            {personalInfo?.email} | {personalInfo?.phone}
          </p>
          {personalInfo?.linkedin && (
            <a
              href={personalInfo.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline dark:text-blue-400"
            >
              LinkedIn Profile
            </a>
          )}
        </div>

        {/* Date */}
        {hasMounted && (
          <p className="mb-8 text-gray-600 dark:text-gray-400">
            {new Date().toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        )}

        {/* Recipient's Info */}
        <div className="mb-8">
          <p className="font-semibold text-gray-900 dark:text-gray-100">
            Hiring Team
          </p>
          <p className="text-gray-700 dark:text-gray-300">{company_name}</p>
        </div>

        {/* Subject Line */}
        <h2 className="text-lg font-semibold mb-6 text-gray-900 dark:text-gray-100">
          RE: {job_title} Position
        </h2>

        {/* Body of the letter */}
        <div className="whitespace-pre-line text-justify text-gray-700 dark:text-gray-300 space-y-4">
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
      </div>
    </div>
  );
};
