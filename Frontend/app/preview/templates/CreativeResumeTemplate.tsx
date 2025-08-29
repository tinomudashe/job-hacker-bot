"use client";

import {
  Award,
  Briefcase,
  Globe,
  GraduationCap,
  Lightbulb,
  Linkedin,
  Mail,
  MapPin,
  Phone,
  Star,
  User,
} from "lucide-react";
import * as React from "react";
import { PreviewData } from "../types";

// EDIT: This is a brand new template component for the "Creative" style.
export const CreativeResumeTemplate: React.FC<{ data: PreviewData }> = ({
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

  const Section: React.FC<{
    icon: React.ReactNode;
    title: string;
    children: React.ReactNode;
  }> = ({ icon, title, children }) => (
    <section className="mb-8 print:mb-4">
      <div className="flex items-center mb-4 print:mb-2">
        <div className="w-8 h-8 mr-4 bg-primary/10 text-primary rounded-full flex items-center justify-center print:!bg-gray-100 print:!text-gray-700 print:w-6 print:h-6 print:mr-2">
          {icon}
        </div>
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200 print:!text-gray-900 print:text-lg">
          {title}
        </h2>
      </div>
      <div className="pl-12 print:pl-0">{children}</div>
    </section>
  );

  return (
    <div className="p-8 md:p-12 bg-transparent font-sans text-gray-700 dark:text-gray-300 print:p-8 print:!bg-white">
      <header className="mb-12 print:mb-6">
        <div className="flex flex-col md:flex-row items-start justify-between print:flex-row">
          <div>
            <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent print:!text-gray-900 print:!bg-none print:text-3xl print:font-bold">
              {personalInfo?.name}
            </h1>
            <p className="text-lg text-gray-500 dark:text-gray-400 mt-1 print:text-base print:mt-0.5">
              {work_experience?.[0]?.jobTitle || "Professional"}
            </p>
          </div>
          <div className="text-right mt-4 md:mt-0 text-sm space-y-1 print:mt-0 print:text-xs print:space-y-0.5">
            <p className="flex items-center justify-end gap-2 print:gap-1">
              <Mail className="w-4 h-4 text-gray-400 print:w-3 print:h-3" /> {personalInfo?.email}
            </p>
            <p className="flex items-center justify-end gap-2 print:gap-1">
              <Phone className="w-4 h-4 text-gray-400 print:w-3 print:h-3" /> {personalInfo?.phone}
            </p>
            {personalInfo?.location && (
              <p className="flex items-center justify-end gap-2 print:gap-1">
                <MapPin className="w-4 h-4 text-gray-400 print:w-3 print:h-3" /> {personalInfo.location}
              </p>
            )}
            {personalInfo?.linkedin && (
              <div className="flex items-center justify-end gap-2 print:gap-1">
                <Linkedin className="w-4 h-4 text-gray-400 print:w-3 print:h-3" />
                <a
                  href={personalInfo.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline text-xs break-all"
                >
                  {personalInfo.linkedin}
                </a>
              </div>
            )}
            {personalInfo?.website && (
              <div className="flex items-center justify-end gap-2 print:gap-1">
                <Globe className="w-4 h-4 text-gray-400 print:w-3 print:h-3" />
                <a
                  href={personalInfo.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline text-xs break-all"
                >
                  {personalInfo.website}
                </a>
              </div>
            )}
          </div>
        </div>
      </header>

      <main>
        {personalInfo?.summary && (
          <Section icon={<User className="w-5 h-5" />} title="About Me">
            <p className="leading-relaxed">{personalInfo.summary}</p>
          </Section>
        )}

        {work_experience && work_experience.length > 0 && (
          <Section icon={<Briefcase className="w-5 h-5 print:w-4 print:h-4" />} title="Experience">
            <div className="space-y-6 border-l-2 border-primary/20 pl-6 print:border-none print:pl-0 print:space-y-3">
              {work_experience.map((job) => (
                <div
                  key={job.id}
                  className="relative before:absolute before:-left-[27px] before:top-1.5 before:w-2 before:h-2 before:bg-primary before:rounded-full print:before:hidden"
                >
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 print:text-sm print:font-medium">
                    {job.jobTitle} at {job.company}
                  </h3>
                  <p className="text-xs text-gray-400 mb-1 print:text-[10px]">
                    {job.dates?.start} - {job.dates?.end || "Present"}
                  </p>
                  <ul className="text-sm leading-relaxed space-y-1 print:text-xs print:leading-normal print:space-y-0.5">
                    {job.description
                      .replace(/\n(?![•▪\-])/g, ' ') // Replace single newlines with spaces
                      .split(/[•▪]|\n\s*[-•▪]/) // Split on bullets or newlines followed by bullets
                      .filter(p => p.trim())
                      .map((point, idx) => (
                      <li key={idx} className="flex">
                        <span className="mr-2 text-blue-500">•</span>
                        <span>{point.trim()}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Section>
        )}

        {projects && projects.length > 0 && (
          <Section icon={<Lightbulb className="w-5 h-5 print:w-4 print:h-4" />} title="Projects">
            <div className="space-y-6 print:space-y-3">
              {projects.map((project, index) => (
                <div key={index}>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 print:text-sm print:font-medium">
                    {project.name}
                  </h3>
                  <p className="text-sm leading-relaxed whitespace-pre-line print:text-xs print:leading-normal">
                    {project.description}
                  </p>
                  {project.technologies && project.technologies.length > 0 && (
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 print:text-[10px] print:mt-1">
                      <span className="font-semibold">Built with:</span>{" "}
                      {project.technologies.join(", ")}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        <div className="grid md:grid-cols-2 gap-8 print:gap-4">
          {education && education.length > 0 && (
            <Section
              icon={<GraduationCap className="w-5 h-5 print:w-4 print:h-4" />}
              title="Education"
            >
              <div className="space-y-4 print:space-y-2">
                {education.map((edu) => (
                  <div key={edu.id}>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 print:text-sm">
                      {edu.degree}
                    </h3>
                    <p className="text-gray-500 print:text-xs">
                      {edu.institution} - {edu.dates?.end}
                    </p>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {skills && skills.length > 0 && (
            <Section icon={<Star className="w-5 h-5 print:w-4 print:h-4" />} title="Skills">
              <div className="flex flex-wrap gap-2 print:gap-1">
                {skills.map((skill, index) => (
                  <span
                    key={index}
                    className="bg-primary/10 text-primary text-sm font-medium px-3 py-1 rounded-full print:!bg-gray-100 print:!text-gray-700 print:border print:border-gray-300 print:text-xs print:px-2 print:py-0.5"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {certifications && certifications.length > 0 && (
            <Section
              icon={<Award className="w-5 h-5 print:w-4 print:h-4" />}
              title="Certifications"
            >
              <div className="space-y-2 print:space-y-1">
                {certifications.map((cert, index) => (
                  <p key={index} className="text-gray-600 dark:text-gray-300 print:text-xs">
                    <span className="font-semibold">{cert.name}</span>
                    <span className="text-sm print:text-xs">
                      , {cert.issuing_organization}
                    </span>
                  </p>
                ))}
              </div>
            </Section>
          )}

          {languages && languages.length > 0 && (
            <Section icon={<Globe className="w-5 h-5 print:w-4 print:h-4" />} title="Languages">
              <div className="space-y-2 print:space-y-0.5">
                {languages.map((lang, index) => (
                  <p key={index} className="text-gray-600 dark:text-gray-300 print:text-xs">
                    <span className="font-semibold">{lang.name}</span>
                    <span className="text-sm print:text-xs"> ({lang.proficiency})</span>
                  </p>
                ))}
              </div>
            </Section>
          )}
        </div>
      </main>
    </div>
  );
};
