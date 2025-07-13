"use client";

import * as React from "react";
import { PreviewData } from "../types";

// EDIT: This is a brand new template component for the "Professional" style.
export const ProfessionalResumeTemplate: React.FC<{ data: PreviewData }> = ({
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
    <div className="p-8 md:p-10 bg-transparent font-serif text-gray-800 dark:text-gray-100">
      <header className="text-center mb-8">
        <h1 className="text-4xl font-bold tracking-wider text-gray-900 dark:text-white">
          {personalInfo?.name}
        </h1>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 tracking-widest">
          {personalInfo?.email} • {personalInfo?.phone} •{" "}
          {personalInfo?.location}
        </p>
        {personalInfo?.linkedin && (
          <a
            href={personalInfo.linkedin}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-700 hover:underline dark:text-blue-400"
          >
            {personalInfo.linkedin}
          </a>
        )}
      </header>

      <hr className="my-6 border-gray-300 dark:border-gray-700" />

      <main className="flex flex-col md:flex-row gap-12">
        {/* Left Column */}
        <div className="w-full md:w-1/3 md:pr-8">
          {personalInfo?.summary && (
            <section className="mb-8">
              <h2 className="text-base font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400 mb-4">
                About Me
              </h2>
              <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                {personalInfo.summary}
              </p>
            </section>
          )}

          {skills && skills.length > 0 && (
            <section className="mb-8">
              <h2 className="text-base font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400 mb-4">
                Skills
              </h2>
              <ul className="space-y-1">
                {skills.map((skill, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-700 dark:text-gray-300"
                  >
                    {skill}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {languages && languages.length > 0 && (
            <section className="mb-8">
              <h2 className="text-base font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400 mb-4">
                Languages
              </h2>
              <ul className="space-y-1">
                {languages.map((lang, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-700 dark:text-gray-300"
                  >
                    <span className="font-semibold">{lang.name}</span> (
                    {lang.proficiency})
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        {/* Right Column */}
        <div className="w-full md:w-2/3">
          {work_experience && work_experience.length > 0 && (
            <section className="mb-8">
              <h2 className="text-base font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400 mb-6">
                Work Experience
              </h2>
              {work_experience?.map((job) => (
                <div
                  key={job.id}
                  className="mb-6 relative pl-6 before:absolute before:left-0 before:top-1.5 before:w-2 before:h-2 before:bg-gray-500 before:rounded-full"
                >
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                    {job.jobTitle}
                  </h3>
                  <p className="text-md font-medium text-gray-700 dark:text-gray-300">
                    {job.company}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                    {job.dates?.start} - {job.dates?.end || "Present"}
                  </p>
                  <p className="text-sm leading-relaxed text-gray-600 dark:text-gray-400 whitespace-pre-line">
                    {job.description}
                  </p>
                </div>
              ))}
            </section>
          )}

          {projects && projects.length > 0 && (
            <section className="mb-8">
              <h2 className="text-base font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400 mb-6">
                Projects
              </h2>
              {projects.map((project, index) => (
                <div
                  key={index}
                  className="mb-6 relative pl-6 before:absolute before:left-0 before:top-1.5 before:w-2 before:h-2 before:bg-gray-500 before:rounded-full"
                >
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                    {project.name}
                  </h3>
                  <p className="text-sm leading-relaxed text-gray-600 dark:text-gray-400 whitespace-pre-line">
                    {project.description}
                  </p>
                </div>
              ))}
            </section>
          )}

          {education && education.length > 0 && (
            <section className="mb-8">
              <h2 className="text-base font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400 mb-6">
                Education
              </h2>
              {education?.map((edu) => (
                <div key={edu.id} className="mb-4">
                  <h3 className="text-lg font-semibold">{edu.degree}</h3>
                  <p className="font-medium text-gray-700 dark:text-gray-300">
                    {edu.institution} - {edu.dates?.end}
                  </p>
                </div>
              ))}
            </section>
          )}

          {certifications && certifications.length > 0 && (
            <section>
              <h2 className="text-base font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400 mb-6">
                Certifications
              </h2>
              {certifications.map((cert, index) => (
                <div key={index} className="mb-2">
                  <p className="font-medium text-gray-700 dark:text-gray-300">
                    {cert.name}
                    {cert.issuing_organization &&
                      `, ${cert.issuing_organization}`}
                  </p>
                </div>
              ))}
            </section>
          )}
        </div>
      </main>
    </div>
  );
};
