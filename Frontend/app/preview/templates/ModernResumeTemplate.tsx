"use client";

import * as React from "react";
import { PreviewData } from "../types"; // Assuming types are defined in a shared file

// EDIT: This is the existing ResumeTemplate component, moved into its own file.
// It will serve as our "Modern" style.
export const ModernResumeTemplate: React.FC<{ data: PreviewData }> = ({
  data,
}) => {
  const {
    personalInfo,
    work_experience,
    education,
    skills,
    projects,
    certifications,
    languages,
  } = data;

  return (
    <div className="p-8 md:p-12 bg-transparent font-sans text-gray-800 dark:text-gray-200">
      <header className="text-center mb-10 border-b pb-6 border-gray-300 dark:border-gray-700">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          {personalInfo?.name}
        </h1>
        <div className="flex justify-center flex-wrap gap-x-6 gap-y-2 mt-4 text-sm text-gray-500 dark:text-gray-400">
          <span>{personalInfo?.email}</span>
          {personalInfo?.phone && <span>| {personalInfo.phone}</span>}
          {personalInfo?.location && <span>| {personalInfo.location}</span>}
          {personalInfo?.linkedin && (
            <a
              href={personalInfo.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline dark:text-blue-400"
            >
              | LinkedIn
            </a>
          )}
        </div>
      </header>

      <main>
        {personalInfo?.summary && (
          <section className="mb-8">
            <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
              Summary
            </h2>
            <p className="text-gray-600 dark:text-gray-400 whitespace-pre-line">
              {personalInfo.summary}
            </p>
          </section>
        )}

        {work_experience && work_experience.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
              Experience
            </h2>
            {work_experience?.map((job) => (
              <div key={job.id} className="mb-6">
                <div className="flex justify-between items-baseline">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {job.jobTitle}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {job.dates?.start} - {job.dates?.end || "Present"}
                  </p>
                </div>
                <p className="font-medium text-gray-600 dark:text-gray-300 mb-2">
                  {job.company}
                </p>
                <p className="text-gray-600 dark:text-gray-400 whitespace-pre-line">
                  {job.description}
                </p>
              </div>
            ))}
          </section>
        )}

        {projects && projects.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
              Projects
            </h2>
            {projects.map((project, index) => (
              <div key={index} className="mb-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  {project.name}
                </h3>
                {project.url && (
                  <a
                    href={project.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline dark:text-blue-400"
                  >
                    {project.url}
                  </a>
                )}
                <p className="mt-2 text-gray-600 dark:text-gray-400 whitespace-pre-line">
                  {project.description}
                </p>
                {project.technologies && project.technologies.length > 0 && (
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    <span className="font-semibold">Technologies:</span>{" "}
                    {project.technologies.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </section>
        )}

        {education && education.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
              Education
            </h2>
            {education?.map((edu) => (
              <div key={edu.id} className="mb-4">
                <div className="flex justify-between items-baseline">
                  <h3 className="text-xl font-semibold">{edu.degree}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {edu.dates?.end}
                  </p>
                </div>
                <p className="font-medium text-gray-600 dark:text-gray-300">
                  {edu.institution}
                </p>
              </div>
            ))}
          </section>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {skills && skills.length > 0 && (
            <section>
              <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
                Skills
              </h2>
              <ul className="space-y-1">
                {skills.map((skill, index) => (
                  <li key={index} className="text-gray-600 dark:text-gray-400">
                    {skill}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {certifications && certifications.length > 0 && (
            <section>
              <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
                Certifications
              </h2>
              <ul className="space-y-2">
                {certifications.map((cert, index) => (
                  <li key={index} className="text-gray-600 dark:text-gray-400">
                    <span className="font-semibold">{cert.name}</span>
                    {cert.issuing_organization && (
                      <span className="block text-sm italic">
                        {cert.issuing_organization}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {languages && languages.length > 0 && (
            <section>
              <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
                Languages
              </h2>
              <ul className="space-y-1">
                {languages.map((lang, index) => (
                  <li key={index} className="text-gray-600 dark:text-gray-400">
                    <span className="font-semibold">{lang.name}</span>
                    {lang.proficiency && `: ${lang.proficiency}`}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </main>
    </div>
  );
};
