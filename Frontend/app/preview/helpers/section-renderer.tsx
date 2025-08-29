import React from "react";
import { PreviewData } from "../types";

interface SectionRendererProps {
  data: PreviewData;
  renderWorkExperience: () => React.ReactNode;
  renderEducation: () => React.ReactNode;
  renderProjects: () => React.ReactNode;
  renderCertifications: () => React.ReactNode;
  renderLanguages: () => React.ReactNode;
}

export const SectionRenderer: React.FC<SectionRendererProps> = ({
  data,
  renderWorkExperience,
  renderEducation,
  renderProjects,
  renderCertifications,
  renderLanguages,
}) => {
  const defaultOrder = [
    { id: "workExperience", visible: true },
    { id: "education", visible: true },
    { id: "projects", visible: true },
    { id: "certifications", visible: true },
    { id: "languages", visible: true },
  ];

  const sectionOrder = data.section_order || defaultOrder;

  const sectionMap: { [key: string]: () => React.ReactNode } = {
    workExperience: renderWorkExperience,
    education: renderEducation,
    projects: renderProjects,
    certifications: renderCertifications,
    languages: renderLanguages,
  };

  return (
    <>
      {sectionOrder.map((section) => {
        if (section.visible && sectionMap[section.id]) {
          return <React.Fragment key={section.id}>{sectionMap[section.id]()}</React.Fragment>;
        }
        return null;
      })}
    </>
  );
};