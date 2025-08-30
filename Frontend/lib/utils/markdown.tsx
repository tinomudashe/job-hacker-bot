import React from "react";

/**
 * Utility function to convert basic markdown to plain text
 * Handles bullet points and preserves line breaks
 */
export function parseBasicMarkdown(text: string): string {
  if (!text) return "";
  
  // Process each line
  return text
    .split("\n")
    .map(line => {
      // Handle bullet points
      if (line.trim().startsWith("- ")) {
        // Remove the dash and convert to bullet
        let content = line.trim().substring(2);
        return `• ${content}`;
      }
      
      // Return line as-is
      return line;
    })
    .join("\n");
}

/**
 * Convert markdown line to React elements for rendering
 * Handles bold text (**text**)
 */
export function renderMarkdownLine(text: string): React.ReactNode {
  if (!text) return null;
  
  // Split by ** to find bold sections
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  
  return parts.map((part, index) => {
    // Check if this part is bold (surrounded by **)
    if (part.startsWith("**") && part.endsWith("**")) {
      const boldText = part.slice(2, -2);
      return <strong key={index} className="font-semibold">{boldText}</strong>;
    }
    return part;
  });
}

/**
 * Parse job description into bullet points for consistent rendering
 * Handles various bullet formats and ensures proper spacing
 */
export function parseJobDescription(description: string): string[] {
  if (!description) return [];
  
  // Normalize the text first
  const normalized = description
    .replace(/\r\n/g, '\n') // Normalize line endings
    .replace(/\r/g, '\n')   // Handle Mac line endings
    .trim();
  
  // Split on various bullet point indicators
  const points = normalized
    .split(/(?:\n|^)\s*[•▪\-\*]\s*/) // Split on newline + bullet chars
    .filter(point => point.trim().length > 0) // Remove empty points
    .map(point => point.trim().replace(/\n+/g, ' ')); // Clean up each point
  
  // If no bullet points found, split on double newlines (paragraphs)
  if (points.length <= 1) {
    return normalized
      .split(/\n\s*\n/)
      .filter(para => para.trim().length > 0)
      .map(para => para.trim().replace(/\n/g, ' '));
  }
  
  return points;
}