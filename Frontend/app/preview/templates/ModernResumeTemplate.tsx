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
        <div className="mt-4 text-sm text-gray-500 dark:text-gray-400 text-center">
          {personalInfo?.email && <div>{personalInfo.email}</div>}
          {personalInfo?.phone && <div>{personalInfo.phone}</div>}
          {personalInfo?.location && <div>{personalInfo.location}</div>}
          {personalInfo?.linkedin && (
            <div>
              <a
                href={personalInfo.linkedin}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline dark:text-blue-400"
              >
                {personalInfo.linkedin}
              </a>
            </div>
          )}
          {personalInfo?.website && (
            <div>
              <a
                href={personalInfo.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline dark:text-blue-400"
              >
                {personalInfo.website}
              </a>
            </div>
          )}
        </div>
      </header>

      <main>
        {personalInfo?.summary && (
          <section className="mb-8">
            <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
              Summary
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line">
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
                <ul className="text-gray-600 dark:text-gray-400 mt-2 space-y-1">
                  {job.description
                    .replace(/\n(?![•▪\-])/g, ' ') // Replace single newlines with spaces
                    .split(/[•▪]|\n\s*[-•▪]/) // Split on bullets or newlines followed by bullets
                    .filter(p => p.trim())
                    .map((point, idx) => (
                    <li key={idx} className="flex text-sm">
                      <span className="mr-2 text-blue-500">▪</span>
                      <span>{point.trim()}</span>
                    </li>
                  ))}
                </ul>
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
                <p className="mt-2 text-gray-600 dark:text-gray-400 text-sm">
                  {project.description}
                </p>
                {project.technologies && project.technologies.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {project.technologies.map((tech, idx) => (
                      <span key={idx} className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full">
                        {tech}
                      </span>
                    ))}
                  </div>
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
                  <li key={index} className="text-sm text-gray-600 dark:text-gray-400">
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
              <div className="space-y-2">
                {certifications.map((cert, index) => (
                  <div key={index} className="bg-gray-50 dark:bg-gray-800/50 p-1.5 rounded">
                    <p className="font-semibold text-xs text-gray-800 dark:text-gray-200">
                      {cert.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {cert.issuing_organization}
                      {cert.date_issued && ` • ${cert.date_issued}`}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {languages && languages.length > 0 && (
            <section>
              <h2 className="text-lg uppercase font-bold tracking-widest text-gray-700 dark:text-gray-300 mb-4">
                Languages
              </h2>
              <div className="space-y-2">
                {languages.map((lang, index) => {
                  const getProficiencyDots = (level: string) => {
                    const levels: Record<string, number> = {
                      'Native': 5, 'Fluent': 4, 'Professional': 3, 'Intermediate': 2, 'Basic': 1
                    };
                    const dots = levels[level] || 3;
                    return '●'.repeat(dots) + '○'.repeat(5 - dots);
                  };
                  return (
                    <div key={index} className="flex justify-between items-center">
                      <span className="font-medium text-sm text-gray-700 dark:text-gray-300">
                        {lang.name}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {getProficiencyDots(lang.proficiency || 'Intermediate')}
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
};
