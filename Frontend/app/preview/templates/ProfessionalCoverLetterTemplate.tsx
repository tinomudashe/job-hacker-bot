"use client";

import * as React from "react";
import { PreviewData } from "../types";

// EDIT: This is a brand new template for the "Professional" cover letter style.
// It uses a classic, formal business letter layout.
export const ProfessionalCoverLetterTemplate: React.FC<{
  data: PreviewData;
  hasMounted: boolean;
}> = ({ data, hasMounted }) => {
  const { personalInfo, company_name, job_title, content } = data;

  // EDIT: Check if the content already contains a closing.
  const hasClosing =
    content.toLowerCase().includes("sincerely") ||
    content.toLowerCase().includes("best regards");

  return (
    <div className="p-8 md:p-12 bg-transparent font-serif text-gray-800 dark:text-gray-200 text-sm">
      <div className="max-w-4xl mx-auto">
        {/* Sender's Info (Top Left) */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {personalInfo?.name}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {personalInfo?.location}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            {personalInfo?.email}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            {personalInfo?.phone}
          </p>
          {personalInfo?.linkedin && (
            <a
              href={personalInfo.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-700 hover:underline dark:text-blue-400"
            >
              {personalInfo.linkedin}
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
          <p className="font-semibold text-gray-800 dark:text-gray-100">
            Hiring Manager
          </p>
          <p className="text-gray-700 dark:text-gray-300">{company_name}</p>
        </div>

        {/* Subject Line */}
        <p className="mb-6 font-semibold text-gray-800 dark:text-gray-100">
          Regarding: Application for the {job_title} Position
        </p>

        {/* Body of the letter */}
        <div className="whitespace-pre-line leading-relaxed text-gray-700 dark:text-gray-300 space-y-4">
          {content.split("\n").map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>

        {/* Closing */}
        {/* EDIT: Only render the template's closing if the main content doesn't already have one. */}
        {!hasClosing && (
          <div className="mt-8">
            <p className="text-gray-700 dark:text-gray-300">Sincerely,</p>
            <p className="mt-4 font-semibold text-gray-900 dark:text-gray-100">
              {personalInfo?.name}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
