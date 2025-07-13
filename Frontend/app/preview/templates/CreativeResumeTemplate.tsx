"use client";

import {
  Award,
  Briefcase,
  Globe,
  GraduationCap,
  Lightbulb,
  Linkedin,
  Mail,
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
    <section className="mb-8">
      <div className="flex items-center mb-4">
        <div className="w-8 h-8 mr-4 bg-primary/10 text-primary rounded-full flex items-center justify-center">
          {icon}
        </div>
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200">
          {title}
        </h2>
      </div>
      <div className="pl-12">{children}</div>
    </section>
  );

  return (
    <div className="p-8 md:p-12 bg-transparent font-sans text-gray-700 dark:text-gray-300">
      <header className="mb-12">
        <div className="flex flex-col md:flex-row items-start justify-between">
          <div>
            <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {personalInfo?.name}
            </h1>
            <p className="text-lg text-gray-500 dark:text-gray-400 mt-1">
              {work_experience?.[0]?.jobTitle || "Professional"}
            </p>
          </div>
          <div className="text-right mt-4 md:mt-0 text-sm space-y-1">
            <p className="flex items-center justify-end gap-2">
              <Mail className="w-4 h-4 text-gray-400" /> {personalInfo?.email}
            </p>
            <p className="flex items-center justify-end gap-2">
              <Phone className="w-4 h-4 text-gray-400" /> {personalInfo?.phone}
            </p>
            {personalInfo?.linkedin && (
              <a
                href={personalInfo.linkedin}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-end gap-2 text-blue-600 hover:underline"
              >
                <Linkedin className="w-4 h-4" /> LinkedIn Profile
              </a>
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
          <Section icon={<Briefcase className="w-5 h-5" />} title="Experience">
            <div className="space-y-6 border-l-2 border-primary/20 pl-6">
              {work_experience.map((job) => (
                <div
                  key={job.id}
                  className="relative before:absolute before:-left-[27px] before:top-1.5 before:w-2 before:h-2 before:bg-primary before:rounded-full"
                >
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {job.jobTitle} at {job.company}
                  </h3>
                  <p className="text-xs text-gray-400 mb-1">
                    {job.dates?.start} - {job.dates?.end || "Present"}
                  </p>
                  <p className="text-sm leading-relaxed whitespace-pre-line">
                    {job.description}
                  </p>
                </div>
              ))}
            </div>
          </Section>
        )}

        {projects && projects.length > 0 && (
          <Section icon={<Lightbulb className="w-5 h-5" />} title="Projects">
            <div className="space-y-6">
              {projects.map((project, index) => (
                <div key={index}>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {project.name}
                  </h3>
                  <p className="text-sm leading-relaxed whitespace-pre-line">
                    {project.description}
                  </p>
                  {project.technologies && project.technologies.length > 0 && (
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      <span className="font-semibold">Built with:</span>{" "}
                      {project.technologies.join(", ")}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          {education && education.length > 0 && (
            <Section
              icon={<GraduationCap className="w-5 h-5" />}
              title="Education"
            >
              <div className="space-y-4">
                {education.map((edu) => (
                  <div key={edu.id}>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {edu.degree}
                    </h3>
                    <p className="text-gray-500">
                      {edu.institution} - {edu.dates?.end}
                    </p>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {skills && skills.length > 0 && (
            <Section icon={<Star className="w-5 h-5" />} title="Skills">
              <div className="flex flex-wrap gap-2">
                {skills.map((skill, index) => (
                  <span
                    key={index}
                    className="bg-primary/10 text-primary text-sm font-medium px-3 py-1 rounded-full"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {certifications && certifications.length > 0 && (
            <Section
              icon={<Award className="w-5 h-5" />}
              title="Certifications"
            >
              <div className="space-y-2">
                {certifications.map((cert, index) => (
                  <p key={index} className="text-gray-600 dark:text-gray-300">
                    <span className="font-semibold">{cert.name}</span>
                    <span className="text-sm">
                      , {cert.issuing_organization}
                    </span>
                  </p>
                ))}
              </div>
            </Section>
          )}

          {languages && languages.length > 0 && (
            <Section icon={<Globe className="w-5 h-5" />} title="Languages">
              <div className="space-y-2">
                {languages.map((lang, index) => (
                  <p key={index} className="text-gray-600 dark:text-gray-300">
                    <span className="font-semibold">{lang.name}</span>
                    <span className="text-sm"> ({lang.proficiency})</span>
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
