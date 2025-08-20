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