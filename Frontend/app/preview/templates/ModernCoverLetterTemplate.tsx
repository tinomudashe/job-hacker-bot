"use client";

import * as React from "react";
import { PreviewData } from "../types";

// EDIT: This is the existing CoverLetterTemplate component, moved into its own file.
// This will serve as our "Modern" style, matching the original implementation.
export const ModernCoverLetterTemplate: React.FC<{
  data: PreviewData;
  hasMounted: boolean;
}> = ({ data, hasMounted }) => {
  const { personal_info, company_name, job_title, content } = data;

  return (
    <div className="p-8 md:p-12 bg-transparent text-gray-800 font-serif text-base leading-relaxed dark:text-gray-200">
      <div className="max-w-4xl mx-auto">
        {/* Sender's Info (Top Right) */}
        <div className="text-right mb-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {personal_info?.name}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {personal_info?.location}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            {personal_info?.email} | {personal_info?.phone}
          </p>
          {personal_info?.linkedin && (
            <a
              href={personal_info.linkedin}
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
        <div className="whitespace-pre-line text-justify text-gray-700 dark:text-gray-300">
          {content}
        </div>
      </div>
    </div>
  );
};
