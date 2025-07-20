import { toast } from "sonner";
import { create } from "zustand";

export type DocumentType = "resume" | "cover-letter" | "cv";
// ADDITION: Define a specific type for template names for type safety.
export type TemplateName = "Modern" | "Professional" | "Creative";

interface GeneratedDocumentState {
  documentType: DocumentType | null;
  documentContent: Record<string, unknown> | string | null;
  // FIX: Use the specific TemplateName type for selectedTemplate.
  selectedTemplate: TemplateName;
  isLoading: boolean;
  error: string | null;
  fetchLatestDocument: (
    type: DocumentType,
    token: string | null
  ) => Promise<void>;
  // FIX: Update the setTemplate function to accept the specific TemplateName type.
  setTemplate: (templateName: TemplateName) => void;
  setContent: (content: Record<string, unknown> | string) => void;
}

const useGeneratedDocumentStore = create<GeneratedDocumentState>((set) => ({
  documentType: null,
  documentContent: null,
  selectedTemplate: "Modern", // Default template
  isLoading: false,
  error: null,

  fetchLatestDocument: async (type: DocumentType, token: string | null) => {
    if (!token) {
      set({ error: "Authentication token not found.", isLoading: false });
      toast.error("Authentication required to fetch documents.");
      return;
    }

    set({ isLoading: true, error: null, documentType: type });
    const endpoint =
      type === "resume" || type === "cv"
        ? "/api/resume/latest"
        : "/api/documents/cover-letters/latest";

    try {
      const response = await fetch(endpoint, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch ${type}. Status: ${response.status}`);
      }

      const data = await response.json();
      const contentToParse = data.content;

      let parsedContent: Record<string, unknown> | string;
      try {
        parsedContent = JSON.parse(contentToParse);
      } catch {
        parsedContent = contentToParse;
      }
      if (
        typeof parsedContent === "string" &&
        (type === "resume" || type === "cv")
      ) {
        parsedContent = { body: parsedContent };
      }
      set({
        documentContent: parsedContent,
        isLoading: false,
      });
      toast.success(
        `${type.charAt(0).toUpperCase() + type.slice(1)} loaded successfully!`
      );
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "An unknown error occurred";
      set({ error: errorMessage, isLoading: false, documentContent: null });
      toast.error(`Could not load your ${type}.`);
    }
  },

  // FIX: Update the setTemplate function to accept the specific TemplateName type.
  setTemplate: (templateName: TemplateName) => {
    set({ selectedTemplate: templateName });
  },

  setContent: (content: Record<string, unknown> | string) => {
    set({ documentContent: content });
  },
}));

export default useGeneratedDocumentStore;
