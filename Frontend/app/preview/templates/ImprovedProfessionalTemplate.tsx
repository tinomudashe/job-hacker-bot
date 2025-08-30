"use client";

import * as React from "react";
import { PreviewData } from "../types";
import { Calendar, Award, Globe, Code, Briefcase, GraduationCap, User } from "lucide-react";

export const ImprovedProfessionalTemplate: React.FC<{ data: PreviewData }> = ({
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

  // Helper function to format bullet points
  const formatBulletPoints = (text: string): string[] => {
    if (!text) return [];
    
    // First replace single newlines with spaces, then split by bullets
    const points = text
      .replace(/\n(?![•▪\-])/g, ' ') // Replace single newlines with spaces
      .split(/[•▪]|\n\s*[-•▪]/) // Split on bullets or newlines followed by bullets
      .map(point => point.trim())
      .filter(point => point.length > 0)
      .map(point => {
        // Remove redundant words and make concise
        return point
          .replace(/^(Responsible for|Managed to|Helped to|Worked on)/i, '')
          .replace(/\s+/g, ' ')
          .trim();
      });
    
    // Return all points without truncation
    return points;
  };

  // Format date ranges concisely
  const formatDateRange = (start?: string, end?: string): string => {
    if (!start) return end || '';
    const startYear = start.split(' ')[1] || start;
    const endYear = end ? (end.split(' ')[1] || end) : 'Present';
    return `${startYear} - ${endYear}`;
  };

  return (
    <div className="p-6 md:p-8 bg-white dark:bg-gray-900 font-sans text-gray-800 dark:text-gray-100 max-w-4xl mx-auto">
      {/* Header - Compact and Professional */}
      <header className="border-b-2 border-gray-800 dark:border-gray-200 pb-4 mb-6">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
          {personalInfo?.name}
        </h1>
        <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 space-y-1">
          {personalInfo?.email && <div>✉ {personalInfo.email}</div>}
          {personalInfo?.phone && <div>☎ {personalInfo.phone}</div>}
          {personalInfo?.location && <div>📍 {personalInfo.location}</div>}
          {personalInfo?.linkedin && (
            <div>
              🔗 <a href={personalInfo.linkedin} className="text-blue-600 dark:text-blue-400 hover:underline">
                {personalInfo.linkedin}
              </a>
            </div>
          )}
          {personalInfo?.website && (
            <div>
              🌐 <a href={personalInfo.website} className="text-blue-600 dark:text-blue-400 hover:underline">
                {personalInfo.website}
              </a>
            </div>
          )}
        </div>
      </header>

      {/* Professional Summary - Concise */}
      {personalInfo?.summary && (
        <section className="mb-6">
          <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-300 italic">
            {personalInfo.summary}
          </p>
        </section>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Content - 2/3 width */}
        <div className="md:col-span-2 space-y-6">
          {/* Work Experience - Concise bullet points */}
          {work_experience && work_experience.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-wide text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
                <Briefcase className="h-4 w-4" />
                Experience
              </h2>
              {work_experience.map((job) => {
                const bulletPoints = formatBulletPoints(job.description);
                return (
                  <div key={job.id} className="mb-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-bold text-gray-900 dark:text-gray-100">
                          {job.jobTitle}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {job.company}
                        </p>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-500 whitespace-nowrap">
                        {formatDateRange(job.dates?.start, job.dates?.end)}
                      </span>
                    </div>
                    {bulletPoints.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {bulletPoints.map((point, idx) => (
                          <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex">
                            <span className="mr-2">•</span>
                            <span>{point}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                );
              })}
            </section>
          )}

          {/* Projects - Structured and concise */}
          {projects && projects.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-wide text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
                <Code className="h-4 w-4" />
                Projects
              </h2>
              <div className="space-y-3">
                {projects.map((project, index) => (
                  <div key={index} className="border-l-2 border-gray-300 dark:border-gray-600 pl-3">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                      {project.title || project.name}
                      {project.url && (
                        <a href={project.url} className="ml-2 text-xs text-blue-600 dark:text-blue-400">
                          [View]
                        </a>
                      )}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {project.description}
                    </p>
                    {project.technologies && project.technologies.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {project.technologies.map((tech, idx) => (
                          <span key={idx} className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
                            {tech}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Education - Compact */}
          {education && education.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-wide text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
                <GraduationCap className="h-4 w-4" />
                Education
              </h2>
              {education.map((edu) => (
                <div key={edu.id} className="mb-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                        {edu.degree}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {edu.institution}
                      </p>
                    </div>
                    <span className="text-xs text-gray-500">
                      {edu.dates?.end}
                    </span>
                  </div>
                </div>
              ))}
            </section>
          )}
        </div>

        {/* Sidebar - 1/3 width */}
        <div className="space-y-6">
          {/* Skills - Compact tags */}
          {skills && skills.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-wide text-gray-800 dark:text-gray-200 mb-3">
                Skills
              </h2>
              <div className="flex flex-wrap gap-1.5">
                {skills.map((skill, index) => (
                  <span
                    key={index}
                    className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded-md"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </section>
          )}

          {/* Certifications - Structured */}
          {certifications && certifications.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-wide text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
                <Award className="h-4 w-4" />
                Certifications
              </h2>
              <div className="space-y-2">
                {certifications.map((cert, index) => (
                  <div key={index} className="text-sm">
                    <p className="font-semibold text-gray-800 dark:text-gray-200">
                      {cert.name}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {cert.issuing_organization}
                      {cert.date_issued && ` • ${cert.date_issued}`}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Languages - Visual proficiency */}
          {languages && languages.length > 0 && (
            <section>
              <h2 className="text-lg font-bold uppercase tracking-wide text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Languages
              </h2>
              <div className="space-y-2">
                {languages.map((lang, index) => {
                  const proficiencyLevel = {
                    'Native': '●●●●●',
                    'Fluent': '●●●●○',
                    'Professional': '●●●○○',
                    'Intermediate': '●●○○○',
                    'Basic': '●○○○○'
                  };
                  
                  return (
                    <div key={index} className="flex justify-between items-center text-sm">
                      <span className="font-medium text-gray-700 dark:text-gray-300">
                        {lang.name}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-500">
                        {proficiencyLevel[lang.proficiency as keyof typeof proficiencyLevel] || lang.proficiency}
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
};