import React from "react";
import { PreviewData } from "../types";
import { SectionRenderer } from "../helpers/section-renderer";
import { parseJobDescription } from "@/lib/utils/markdown";

interface ProfessionalATSTemplateProps {
  data: PreviewData;
}

export const ProfessionalATSTemplate: React.FC<ProfessionalATSTemplateProps> = ({
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
    job_title,
  } = data;

  return (
    <div className="w-full max-w-[21cm] mx-auto bg-white text-black p-12 font-sans">
      {/* Header - Simple and Clean */}
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-blue-600 uppercase mb-2">
          {personalInfo?.name || "Your Name"}
        </h1>
        {job_title && (
          <h2 className="text-base font-semibold text-black uppercase mb-2">
            {job_title}
          </h2>
        )}
        <div className="text-sm text-black">
          {personalInfo?.location && <div>{personalInfo.location}</div>}
          {personalInfo?.email && <div>{personalInfo.email}</div>}
          {personalInfo?.phone && <div>{personalInfo.phone}</div>}
          {personalInfo?.linkedin && <div>{personalInfo.linkedin}</div>}
          {personalInfo?.website && <div>{personalInfo.website}</div>}
        </div>
      </header>

      {/* Summary Section */}
      {personalInfo?.summary && (
        <section className="mb-5">
          <h3 className="text-sm font-bold text-blue-600 uppercase border-b border-gray-300 pb-1 mb-3">
            SUMMARY
          </h3>
          <p className="text-sm text-black text-justify">
            {personalInfo.summary}
          </p>
        </section>
      )}

      {/* Technical Skills Section */}
      {skills && skills.length > 0 && (
        <section className="mb-5">
          <h3 className="text-sm font-bold text-blue-600 uppercase border-b border-gray-300 pb-1 mb-3">
            TECHNICAL SKILLS
          </h3>
          <div className="grid grid-cols-3 gap-x-8 gap-y-1">
            {skills.map((skill, idx) => (
              <div key={idx} className="text-sm text-black">
                {skill}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Dynamic Sections based on order */}
      <SectionRenderer
        data={data}
        renderWorkExperience={() =>
          work_experience && work_experience.length > 0 ? (
            <section className="mb-5">
              <h3 className="text-sm font-bold text-blue-600 uppercase border-b border-gray-300 pb-1 mb-3">
                PROFESSIONAL EXPERIENCE
              </h3>
              <div className="space-y-3">
                {work_experience.map((job) => (
                  <div key={job.id} className="mb-3">
                    <div className="flex justify-between items-start mb-1">
                      <h4 className="font-semibold text-black text-sm">
                        {job.jobTitle}, {job.company}
                      </h4>
                      <span className="text-sm text-black font-semibold">
                        {job.dates?.start} - {job.dates?.end || "Present"}
                      </span>
                    </div>
                    {job.description && (
                      <ul className="mt-1 space-y-0.5 ml-4">
                        {parseJobDescription(job.description).map((point, idx) => (
                          <li key={idx} className="text-sm text-black list-disc">
                            {point}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </section>
          ) : null
        }
        renderEducation={() =>
          education && education.length > 0 ? (
            <section className="mb-5">
              <h3 className="text-sm font-bold text-blue-600 uppercase border-b border-gray-300 pb-1 mb-3">
                EDUCATION
              </h3>
              <div className="space-y-2">
                {education.map((edu, idx) => (
                  <div key={idx} className="mb-2">
                    <div className="mb-1">
                      <h4 className="font-semibold text-black text-sm">{edu.degree}</h4>
                    </div>
                    <div className="flex justify-between items-start">
                      <div className="text-sm text-black">{edu.institution}</div>
                      <span className="text-sm text-black font-semibold">
                        {edu.dates?.end}
                      </span>
                    </div>
                    {edu.description && (
                      <ul className="mt-1 ml-4">
                        {edu.description
                          .split(/[•▪\n]/)
                          .filter(p => p.trim())
                          .map((point, idx) => (
                            <li key={idx} className="text-sm text-black list-disc">
                              {point.trim()}
                            </li>
                          ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </section>
          ) : null
        }
        renderProjects={() =>
          projects && projects.length > 0 ? (
            <section className="mb-5">
              <h3 className="text-sm font-bold text-blue-600 uppercase border-b border-gray-300 pb-1 mb-3">
                PROJECTS
              </h3>
              <div className="space-y-2">
                {projects.map((project, idx) => (
                  <div key={idx} className="mb-2">
                    <h4 className="font-semibold text-black text-sm mb-1">{project.name}</h4>
                    {project.description && (
                      <ul className="ml-4 space-y-0.5">
                        {project.description
                          .split(/[•▪\n]/)
                          .filter(p => p.trim())
                          .map((point, idx) => (
                            <li key={idx} className="text-sm text-black list-disc">
                              {point.trim()}
                            </li>
                          ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </section>
          ) : null
        }
        renderCertifications={() =>
          certifications && certifications.length > 0 ? (
            <section className="mb-5">
              <h3 className="text-sm font-bold text-blue-600 uppercase border-b border-gray-300 pb-1 mb-3">
                CERTIFICATIONS
              </h3>
              <div className="text-sm text-black">
                {certifications.map((cert, idx) => (
                  <div key={idx} className="mb-1">
                    <span className="font-semibold">{cert.name}</span>
                    {cert.issuing_organization && <span> - {cert.issuing_organization}</span>}
                    {cert.date_issued && <span> ({cert.date_issued})</span>}
                  </div>
                ))}
              </div>
            </section>
          ) : null
        }
        renderLanguages={() =>
          languages && languages.length > 0 ? (
            <section className="mb-5">
              <h3 className="text-sm font-bold text-blue-600 uppercase border-b border-gray-300 pb-1 mb-3">
                LANGUAGES
              </h3>
              <div className="text-sm text-black">
                <span className="font-semibold">Languages: </span>
                {languages.map((lang, idx, arr) => (
                  <span key={idx}>
                    {lang.name} ({lang.proficiency}){idx < arr.length - 1 ? ', ' : ''}
                  </span>
                ))}
              </div>
            </section>
          ) : null
        }
      />
    </div>
  );
};